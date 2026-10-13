import os
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

_mongo_client = None
_mongo_db = None


def get_mongodb_uri():
    """
    Returns the MongoDB Atlas connection string from environment variables or settings.
    """
    return os.environ.get('MONGODB_URI', getattr(settings, 'MONGODB_URI', ''))


def get_mongodb_db_name():
    """
    Returns the configured MongoDB database name.
    """
    return os.environ.get('MONGODB_DB_NAME', getattr(settings, 'MONGODB_DB_NAME', 'campusconnect_db'))


def get_mongo_client():
    """
    Returns a cached PyMongo client instance configured with timeout limits.
    """
    global _mongo_client
    uri = get_mongodb_uri()

    if not uri:
        return None

    if _mongo_client is None:
        try:
            _mongo_client = MongoClient(
                uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
        except Exception as e:
            logger.error(f"Failed to create MongoClient: {e}")
            return None

    return _mongo_client


def get_mongo_db():
    """
    Returns the MongoDB database handle for CampusConnect.
    """
    global _mongo_db
    client = get_mongo_client()
    if client is None:
        return None
    if _mongo_db is None:
        db_name = get_mongodb_db_name()
        _mongo_db = client[db_name]
    return _mongo_db


def check_mongo_connection():
    """
    Tests MongoDB Atlas connectivity and returns (is_connected: bool, details: str).
    """
    uri = get_mongodb_uri()
    if not uri:
        return False, "MONGODB_URI environment variable is not configured yet in .env"

    client = get_mongo_client()
    if client is None:
        return False, "Could not initialize MongoDB client"

    try:
        # Ping the server
        client.admin.command('ping')
        db_name = get_mongodb_db_name()
        return True, f"Successfully connected to MongoDB Atlas (Database: '{db_name}')"
    except (ConnectionFailure, ConfigurationError) as e:
        return False, f"Connection to MongoDB Atlas failed: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error connecting to MongoDB Atlas: {str(e)}"


# ==========================================
# 8 Collections Accessors
# ==========================================

def get_collection(collection_name):
    db = get_mongo_db()
    if db is None:
        return None
    return db[collection_name]


def users_col():
    return get_collection('users')


def events_col():
    return get_collection('events')


def registrations_col():
    return get_collection('registrations')


def teams_col():
    return get_collection('teams')


def event_questions_col():
    return get_collection('event_questions')


def attendance_col():
    return get_collection('attendance')


def announcements_col():
    return get_collection('announcements')


def feedback_col():
    return get_collection('feedback')


# ==========================================
# Real Data Persistence & Sync Methods
# ==========================================

def mongo_sync_user(user, profile=None):
    """
    Inserts or updates actual user in MongoDB Atlas 'users' collection.
    """
    col = users_col()
    if col is None:
        return False

    try:
        doc = {
            'django_user_id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_active': user.is_active,
            'role': profile.role if profile else 'STUDENT',
            'college': profile.college if profile else '',
            'department': profile.department if profile else '',
            'year_of_study': profile.year_of_study if profile else '',
            'phone': profile.phone if profile else '',
            'skills': profile.skills if profile else '',
            'is_approved': profile.is_approved if profile else True,
            'updated_at': timezone.now().isoformat()
        }
        col.update_one(
            {'django_user_id': user.id},
            {'$set': doc, '$setOnInsert': {'created_at': timezone.now().isoformat()}},
            upsert=True
        )
        return True
    except Exception as e:
        logger.error(f"Error syncing user to MongoDB Atlas: {e}")
        return False


def mongo_sync_event(event):
    """
    Inserts or updates actual coordinator event in MongoDB Atlas 'events' collection.
    """
    col = events_col()
    if col is None:
        return False

    try:
        doc = {
            'django_event_id': event.id,
            'title': event.title,
            'slug': event.slug,
            'category': event.category.name if event.category else 'General',
            'coordinator_username': event.coordinator.username,
            'coordinator_name': event.coordinator_name,
            'coordinator_email': event.coordinator_email,
            'college_name': event.college_name,
            'department': event.department,
            'short_description': event.short_description,
            'description': event.description,
            'event_mode': event.event_mode,
            'venue': event.venue,
            'start_date': event.start_date.isoformat() if event.start_date else None,
            'end_date': event.end_date.isoformat() if event.end_date else None,
            'registration_deadline': event.registration_deadline.isoformat() if event.registration_deadline else None,
            'capacity': event.capacity,
            'registration_fee': float(event.registration_fee),
            'prize_pool': event.prize_pool,
            'is_team_event': event.is_team_event,
            'min_team_size': event.min_team_size,
            'max_team_size': event.max_team_size,
            'eligibility': event.eligibility,
            'rules': event.rules,
            'is_published': event.is_published,
            'updated_at': timezone.now().isoformat()
        }
        col.update_one(
            {'django_event_id': event.id},
            {'$set': doc, '$setOnInsert': {'created_at': timezone.now().isoformat()}},
            upsert=True
        )
        return True
    except Exception as e:
        logger.error(f"Error syncing event to MongoDB Atlas: {e}")
        return False


def mongo_sync_registration(registration):
    """
    Inserts student registration into MongoDB Atlas 'registrations' (and 'teams' if applicable).
    """
    reg_col = registrations_col()
    if reg_col is None:
        return False

    try:
        doc = {
            'django_registration_id': registration.id,
            'event_slug': registration.event.slug,
            'event_title': registration.event.title,
            'username': registration.user.username,
            'student_name': registration.user.get_full_name() or registration.user.username,
            'student_email': registration.user.email,
            'registration_token': str(registration.registration_token),
            'status': registration.status,
            'is_checked_in': registration.is_checked_in,
            'checked_in_at': registration.checked_in_at.isoformat() if registration.checked_in_at else None,
            'team_name': registration.team_name,
            'team_members_info': registration.team_members_info,
            'notes': registration.notes,
            'registered_at': registration.registered_at.isoformat() if registration.registered_at else timezone.now().isoformat()
        }
        reg_col.update_one(
            {'registration_token': str(registration.registration_token)},
            {'$set': doc},
            upsert=True
        )

        # If team event, also write/update 'teams' collection
        if registration.team_name:
            t_col = teams_col()
            if t_col is not None:
                t_doc = {
                    'team_name': registration.team_name,
                    'event_slug': registration.event.slug,
                    'event_title': registration.event.title,
                    'team_leader_username': registration.user.username,
                    'team_leader_name': registration.user.get_full_name() or registration.user.username,
                    'roster_info': registration.team_members_info,
                    'updated_at': timezone.now().isoformat()
                }
                t_col.update_one(
                    {'team_name': registration.team_name, 'event_slug': registration.event.slug},
                    {'$set': t_doc, '$setOnInsert': {'created_at': timezone.now().isoformat()}},
                    upsert=True
                )
        return True
    except Exception as e:
        logger.error(f"Error syncing registration to MongoDB Atlas: {e}")
        return False


def mongo_record_attendance(registration, scanned_by_user):
    """
    Inserts a verified attendance record into MongoDB Atlas 'attendance' collection.
    """
    col = attendance_col()
    if col is None:
        return False

    try:
        now_iso = timezone.now().isoformat()
        doc = {
            'registration_token': str(registration.registration_token),
            'event_id': registration.event.id,
            'event_title': registration.event.title,
            'student_username': registration.user.username,
            'student_name': registration.user.get_full_name() or registration.user.username,
            'student_email': registration.user.email,
            'scanned_by_username': scanned_by_user.username if scanned_by_user else 'system',
            'scanned_by_name': scanned_by_user.get_full_name() or scanned_by_user.username if scanned_by_user else 'Coordinator',
            'verified_at': now_iso,
            'team_name': registration.team_name,
            'verification_type': 'QR_CAMERA_SCAN'
        }
        col.insert_one(doc)

        # Update registration status in registrations collection
        reg_col = registrations_col()
        if reg_col is not None:
            reg_col.update_one(
                {'registration_token': str(registration.registration_token)},
                {'$set': {
                    'is_checked_in': True,
                    'checked_in_at': now_iso,
                    'checked_in_by': scanned_by_user.username if scanned_by_user else 'coordinator'
                }}
            )
        return True
    except Exception as e:
        logger.error(f"Error recording attendance in MongoDB Atlas: {e}")
        return False


def mongo_sync_question(question):
    """
    Inserts/updates student question in MongoDB Atlas 'event_questions' collection.
    """
    col = event_questions_col()
    if col is None:
        return False

    try:
        doc = {
            'django_question_id': question.id,
            'event_slug': question.event.slug,
            'event_title': question.event.title,
            'student_username': question.student.username,
            'student_name': question.student.get_full_name() or question.student.username,
            'question': question.question,
            'answer': question.answer,
            'answered_by': question.answered_by.username if question.answered_by else None,
            'created_at': question.created_at.isoformat() if question.created_at else timezone.now().isoformat(),
            'answered_at': question.answered_at.isoformat() if question.answered_at else None,
            'is_public': question.is_public
        }
        col.update_one(
            {'django_question_id': question.id},
            {'$set': doc},
            upsert=True
        )
        return True
    except Exception as e:
        logger.error(f"Error syncing question to MongoDB Atlas: {e}")
        return False


def mongo_sync_announcement(announcement):
    """
    Inserts announcement in MongoDB Atlas 'announcements' collection.
    """
    col = announcements_col()
    if col is None:
        return False

    try:
        doc = {
            'django_announcement_id': announcement.id,
            'event_slug': announcement.event.slug,
            'event_title': announcement.event.title,
            'title': announcement.title,
            'content': announcement.content,
            'posted_by': announcement.posted_by.username,
            'is_urgent': announcement.is_urgent,
            'created_at': announcement.created_at.isoformat() if announcement.created_at else timezone.now().isoformat()
        }
        col.update_one(
            {'django_announcement_id': announcement.id},
            {'$set': doc},
            upsert=True
        )
        return True
    except Exception as e:
        logger.error(f"Error syncing announcement to MongoDB Atlas: {e}")
        return False


def get_atlas_collection_counts():
    """
    Returns actual document counts for all 8 collections in MongoDB Atlas.
    """
    counts = {
        'users': 0,
        'events': 0,
        'registrations': 0,
        'teams': 0,
        'event_questions': 0,
        'attendance': 0,
        'announcements': 0,
        'feedback': 0,
    }

    db = get_mongo_db()
    if db is None:
        return counts, False

    try:
        for key in counts.keys():
            counts[key] = db[key].count_documents({})
        return counts, True
    except Exception as e:
        logger.warning(f"Could not read counts from MongoDB Atlas: {e}")
        return counts, False
