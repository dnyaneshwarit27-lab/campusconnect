import csv
import json
import uuid
from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Q, Count
from django.urls import reverse

from .models import (
    UserProfile,
    Category,
    College,
    Event,
    Registration,
    EventQuestion,
    Announcement,
    TeamFinderPost,
    EventFeedback,
    TeamCollaborationRequest,
    EventCoordinatorTeam,
)
from .utils import generate_qr_base64
from .mongodb import (
    get_mongo_db,
    check_mongo_connection,
    get_atlas_collection_counts,
    mongo_sync_user,
    mongo_sync_event,
    mongo_sync_registration,
    mongo_record_attendance,
    mongo_sync_question,
    mongo_sync_announcement,
    mongo_sync_event_team,
)


def is_coordinator_or_admin(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    profile = getattr(user, 'profile', None)
    if profile and profile.is_coordinator:
        return True
    return EventCoordinatorTeam.objects.filter(user=user, status='APPROVED').exists()


def is_admin_user(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    profile = getattr(user, 'profile', None)
    return profile and profile.is_admin


# ==========================================
# PUBLIC / STUDENT VIEWS (ALL REAL DATA)
# ==========================================

def home(request):
    """
    Main Discovery Hub:
    All dynamic real data from database. Shows clean empty states when no events exist.
    """
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()
    mode = request.GET.get('mode', '').strip()
    status = request.GET.get('status', 'upcoming').strip()
    department = request.GET.get('department', '').strip()

    events_qs = Event.objects.filter(is_published=True).select_related('category', 'college', 'coordinator')

    now = timezone.now()

    # Search filter
    if query:
        events_qs = events_qs.filter(
            Q(title__icontains=query) |
            Q(short_description__icontains=query) |
            Q(description__icontains=query) |
            Q(venue__icontains=query) |
            Q(department__icontains=query) |
            Q(college_name__icontains=query)
        )

    # Category filter
    if category_slug:
        events_qs = events_qs.filter(category__slug=category_slug)

    # Mode filter
    if mode in ['OFFLINE', 'ONLINE', 'HYBRID']:
        events_qs = events_qs.filter(event_mode=mode)

    # Department filter
    if department:
        events_qs = events_qs.filter(department__icontains=department)

    # Status filter
    if status == 'upcoming':
        events_qs = events_qs.filter(start_date__gte=now)
    elif status == 'ongoing':
        events_qs = events_qs.filter(start_date__lte=now, end_date__gte=now)
    elif status == 'past':
        events_qs = events_qs.filter(end_date__lt=now)

    # Featured events (only actual featured events)
    featured_events = Event.objects.filter(is_published=True, is_featured=True, end_date__gte=now)[:4]
    
    # Closing soon events (deadlines in next 7 days)
    closing_soon = Event.objects.filter(
        is_published=True,
        registration_deadline__gte=now,
        registration_deadline__lte=now + timedelta(days=7)
    ).order_by('registration_deadline')[:3]

    categories = Category.objects.annotate(
        active_events_count=Count('events', filter=Q(events__is_published=True, events__end_date__gte=now))
    )

    departments = Event.objects.filter(is_published=True).values_list('department', flat=True).distinct()

    # Dynamic metrics from actual database records
    total_events = Event.objects.filter(is_published=True).count()
    total_registrations = Registration.objects.filter(status='CONFIRMED').count()
    total_verified_attendance = Registration.objects.filter(status='CONFIRMED', is_checked_in=True).count()
    colleges_count = College.objects.count()

    # MongoDB Atlas Status Check
    mongo_connected, mongo_msg = check_mongo_connection()

    context = {
        'events': events_qs,
        'featured_events': featured_events,
        'closing_soon': closing_soon,
        'categories': categories,
        'departments': departments,
        'current_query': query,
        'current_category': category_slug,
        'current_mode': mode,
        'current_status': status,
        'current_department': department,
        'stats': {
            'total_events': total_events,
            'total_registrations': total_registrations,
            'total_verified_attendance': total_verified_attendance,
            'colleges_count': colleges_count,
        },
        'mongo_connected': mongo_connected,
        'mongo_msg': mongo_msg,
    }
    return render(request, 'events/home.html', context)


def event_detail(request, slug):
    """
    Detailed event page:
    Eligibility, rules, agenda, Q&A with coordinator, announcements,
    registration status, and shareable Event Poster QR code.
    """
    event = get_object_or_404(Event.objects.select_related('category', 'college', 'coordinator'), slug=slug)
    
    # Generate Event Poster QR code linking to this page
    event_url = request.build_absolute_uri(reverse('event_detail', args=[event.slug]))
    poster_qr_base64 = generate_qr_base64(event_url, box_size=8)

    # Check if logged-in user is already registered
    user_registration = None
    ticket_qr_base64 = None
    if request.user.is_authenticated:
        user_registration = Registration.objects.filter(event=event, user=request.user).first()
        if user_registration:
            ticket_qr_base64 = generate_qr_base64(str(user_registration.registration_token), box_size=8)

    questions = event.questions.filter(is_public=True).select_related('student', 'answered_by')
    announcements = event.announcements.all()
    related_events = Event.objects.filter(
        category=event.category,
        is_published=True
    ).exclude(id=event.id)[:3]

    # Organizing Team data
    approved_team = event.get_approved_team()
    user_team_membership = event.get_user_team_membership(request.user) if request.user.is_authenticated else None
    can_manage_event = event.is_user_coordinator(request.user) if request.user.is_authenticated else False
    is_lead = (request.user.is_authenticated and (event.coordinator == request.user or request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.is_admin)))
    pending_team_requests_count = event.get_pending_team_requests().count() if is_lead else 0

    context = {
        'event': event,
        'event_url': event_url,
        'poster_qr_base64': poster_qr_base64,
        'user_registration': user_registration,
        'ticket_qr_base64': ticket_qr_base64,
        'questions': questions,
        'announcements': announcements,
        'related_events': related_events,
        'approved_team': approved_team,
        'user_team_membership': user_team_membership,
        'can_manage_event': can_manage_event,
        'is_lead': is_lead,
        'pending_team_requests_count': pending_team_requests_count,
    }
    return render(request, 'events/event_detail.html', context)


@login_required
def register_event(request, slug):
    """
    Processes actual student event registration (individual or team).
    Prevents duplicates, enforces capacity, generates unique security token,
    and synchronizes to MongoDB Atlas 'registrations' and 'teams' collections.
    """
    event = get_object_or_404(Event, slug=slug)

    if request.method == 'POST':
        # Check if already registered
        existing = Registration.objects.filter(event=event, user=request.user).first()
        if existing:
            messages.info(request, f"You are already registered for '{event.title}'. Here is your Digital Pass!")
            return redirect('ticket_pass', token=existing.registration_token)

        # Check capacity & deadline
        if not event.is_registration_open:
            messages.error(request, "Registration for this event is closed or capacity has been reached.")
            return redirect('event_detail', slug=event.slug)

        team_name = request.POST.get('team_name', '').strip()
        team_members_info = request.POST.get('team_members_info', '').strip()
        notes = request.POST.get('notes', '').strip()

        if event.is_team_event and not team_name:
            messages.error(request, "Team Name is required for this team event.")
            return redirect('event_detail', slug=event.slug)

        registration = Registration.objects.create(
            event=event,
            user=request.user,
            team_name=team_name,
            team_members_info=team_members_info,
            notes=notes,
            status='CONFIRMED'
        )

        # Synchronize to MongoDB Atlas 'registrations' and 'teams' collections
        mongo_sync_registration(registration)

        messages.success(request, f"🎉 Success! You are registered for '{event.title}'. Your QR Ticket Pass is ready!")
        return redirect('ticket_pass', token=registration.registration_token)

    return redirect('event_detail', slug=event.slug)


@login_required
def ticket_pass(request, token):
    """
    Displays the unique digital QR entry pass for attendance verification.
    """
    registration = get_object_or_404(
        Registration.objects.select_related('event', 'user', 'user__profile'),
        registration_token=token
    )

    # Permission check: attendee, event coordinator, or admin
    is_owner = registration.user == request.user
    is_coord = registration.event.coordinator == request.user or is_coordinator_or_admin(request.user)

    if not (is_owner or is_coord):
        messages.error(request, "You do not have permission to view this ticket pass.")
        return redirect('home')

    qr_base64 = generate_qr_base64(str(registration.registration_token), box_size=10)

    context = {
        'registration': registration,
        'event': registration.event,
        'qr_base64': qr_base64,
        'is_owner': is_owner,
    }
    return render(request, 'events/ticket_pass.html', context)


@login_required
def my_registrations(request):
    """
    Student Dashboard:
    List of actual registered events, pass links, check-in status, and certificate download.
    """
    registrations = Registration.objects.filter(
        user=request.user
    ).select_related('event', 'event__category').order_by('-registered_at')

    context = {
        'registrations': registrations,
    }
    return render(request, 'events/my_registrations.html', context)


@login_required
def certificate_view(request, token):
    """
    Digital Participation / Completion Certificate:
    Accessible only if attendee attendance is verified (is_checked_in = True).
    """
    registration = get_object_or_404(
        Registration.objects.select_related('event', 'user', 'user__profile'),
        registration_token=token
    )

    if not registration.is_checked_in:
        messages.warning(
            request,
            "Certificate is available only after your physical attendance is verified at the event venue by the coordinator."
        )
        return redirect('ticket_pass', token=registration.registration_token)

    # Generate verification QR code
    verify_url = request.build_absolute_uri(reverse('verify_certificate', args=[registration.registration_token]))
    qr_base64 = generate_qr_base64(verify_url, box_size=6)

    context = {
        'registration': registration,
        'event': registration.event,
        'qr_base64': qr_base64,
        'verify_url': verify_url,
    }
    return render(request, 'events/certificate.html', context)


def verify_certificate(request, token):
    """
    Public verification portal for digital certificates.
    """
    registration = get_object_or_404(
        Registration.objects.select_related('event', 'user', 'user__profile'),
        registration_token=token
    )
    context = {
        'registration': registration,
        'event': registration.event,
        'is_valid': registration.is_checked_in,
    }
    return render(request, 'events/verify_certificate.html', context)


@login_required
def ask_question(request, slug):
    """
    Submit a real question directly to the event coordinator.
    Synchronizes to MongoDB Atlas 'event_questions' collection.
    """
    event = get_object_or_404(Event, slug=slug)
    if request.method == 'POST':
        question_text = request.POST.get('question', '').strip()
        if question_text:
            q = EventQuestion.objects.create(
                event=event,
                student=request.user,
                question=question_text
            )
            # Sync to MongoDB Atlas 'event_questions'
            mongo_sync_question(q)
            messages.success(request, "Your question has been sent to the coordinator! The answer will appear here once reviewed.")
        else:
            messages.error(request, "Please enter a valid question.")
    return redirect('event_detail', slug=event.slug)


def team_finder(request):
    """
    Hackathon Team Finder:
    Browse real student postings, connect with other students, or post a request for teammates.
    """
    posts = TeamFinderPost.objects.all().select_related('user', 'user__profile', 'event').prefetch_related('collaboration_requests', 'collaboration_requests__sender', 'collaboration_requests__sender__profile')
    events = Event.objects.filter(is_published=True, is_team_event=True, end_date__gte=timezone.now())

    # Build mapping of current user's sent pitches/requests
    my_sent_requests = []
    if request.user.is_authenticated:
        my_sent_requests = list(TeamCollaborationRequest.objects.filter(sender=request.user).select_related('post', 'post__user', 'post__user__profile', 'post__event'))
        sent_dict = {req.post_id: req for req in my_sent_requests}
        for post in posts:
            post.my_request = sent_dict.get(post.id)

    query = request.GET.get('q', '').strip()
    if query:
        posts = posts.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(skills_needed__icontains=query) |
            Q(skills_offered__icontains=query)
        )

    if request.method == 'POST' and request.user.is_authenticated:
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        skills_offered = request.POST.get('skills_offered', '').strip()
        skills_needed = request.POST.get('skills_needed', '').strip()
        contact_handle = request.POST.get('contact_handle', '').strip()
        event_id = request.POST.get('event_id', '').strip()

        event_obj = Event.objects.filter(id=event_id).first() if event_id else None

        if title and description and contact_handle:
            TeamFinderPost.objects.create(
                user=request.user,
                event=event_obj,
                title=title,
                description=description,
                skills_offered=skills_offered,
                skills_needed=skills_needed,
                contact_handle=contact_handle,
            )
            messages.success(request, "Your Team Finder request has been posted successfully!")
            return redirect('team_finder')
        else:
            messages.error(request, "Please fill in all required fields.")

    context = {
        'posts': posts,
        'events': events,
        'query': query,
        'my_sent_requests': my_sent_requests,
    }
    return render(request, 'events/team_finder.html', context)


@login_required
def team_connect(request, post_id):
    """
    Submit a real collaboration pitch/request to a team finder post.
    Synchronizes with MongoDB Atlas.
    """
    if request.method != 'POST':
        return redirect('team_finder')

    post = get_object_or_404(TeamFinderPost, id=post_id)

    if post.user == request.user:
        messages.warning(request, "This is your own team request!")
        return redirect('team_finder')

    message = request.POST.get('message', '').strip()
    sender_contact = request.POST.get('sender_contact', '').strip()

    if not message:
        messages.error(request, "Please write a short pitch or intro message.")
        return redirect('team_finder')

    if not sender_contact:
        profile = getattr(request.user, 'profile', None)
        sender_contact = request.user.email or (profile.phone if profile and profile.phone else '') or request.user.username

    req = TeamCollaborationRequest.objects.create(
        post=post,
        sender=request.user,
        message=message,
        sender_contact=sender_contact,
        status='PENDING'
    )

    # Sync to MongoDB Atlas 'collaboration_requests' & 'teams'
    db = get_mongo_db()
    if db is not None:
        try:
            col = db['collaboration_requests']
            col.insert_one({
                'post_id': post.id,
                'post_title': post.title,
                'event_title': post.event.title if post.event else 'General Hackathon',
                'recipient_username': post.user.username,
                'recipient_name': post.user.get_full_name() or post.user.username,
                'sender_username': request.user.username,
                'sender_name': request.user.get_full_name() or request.user.username,
                'sender_email': request.user.email,
                'sender_contact': sender_contact,
                'message': message,
                'status': 'PENDING',
                'created_at': timezone.now().isoformat()
            })
        except Exception as e:
            pass

    recipient_name = post.user.get_full_name() or post.user.username
    messages.success(request, f"Collaboration request sent to {recipient_name}! They can now review your pitch and contact you.")
    return redirect('team_finder')


@login_required
def team_request_status(request, req_id, new_status):
    """
    Team post owner can mark collaboration request as ACCEPTED or DECLINED.
    """
    collab_req = get_object_or_404(TeamCollaborationRequest, id=req_id, post__user=request.user)
    if new_status in ['ACCEPTED', 'DECLINED']:
        collab_req.status = new_status
        collab_req.save()

        # Update in MongoDB Atlas
        db = get_mongo_db()
        if db is not None:
            try:
                db['collaboration_requests'].update_one(
                    {'post_id': collab_req.post.id, 'sender_username': collab_req.sender.username},
                    {'$set': {'status': new_status, 'updated_at': timezone.now().isoformat()}}
                )
            except Exception as e:
                pass

        action_word = "accepted" if new_status == 'ACCEPTED' else "declined"
        sender_name = collab_req.sender.get_full_name() or collab_req.sender.username
        messages.success(request, f"You have {action_word} the collaboration request from {sender_name}!")
    return redirect('team_finder')


@login_required
def team_post_delete(request, post_id):
    """
    Allows post author (or admin) to delete their team finder post.
    """
    post = get_object_or_404(TeamFinderPost, id=post_id)
    if not (post.user == request.user or request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.is_admin)):
        messages.error(request, "You do not have permission to delete this post.")
        return redirect('team_finder')

    title = post.title
    post.delete()

    # Clean up from MongoDB Atlas
    db = get_mongo_db()
    if db is not None:
        try:
            db['collaboration_requests'].delete_many({'post_id': post_id})
        except Exception as e:
            pass

    messages.success(request, f"Team post '{title}' has been successfully deleted.")
    return redirect('team_finder')


@login_required
def team_post_toggle_status(request, post_id):
    """
    Author can mark post as Closed (Team Formed) or Re-open it.
    """
    post = get_object_or_404(TeamFinderPost, id=post_id)
    if not (post.user == request.user or request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.is_admin)):
        messages.error(request, "You do not have permission to modify this post.")
        return redirect('team_finder')

    post.is_open = not post.is_open
    post.save()
    status_label = "Open" if post.is_open else "Closed (Team Formed)"
    messages.success(request, f"Post status updated to: {status_label}!")
    return redirect('team_finder')




# ==========================================
# COORDINATOR PORTAL & QR ATTENDANCE SCANNER
# ==========================================

@login_required
@user_passes_test(is_coordinator_or_admin)
def coordinator_dashboard(request):
    """
    Coordinator Overview:
    Dynamic metrics and events list (Lead events + Co-Coordinating events).
    Allows discovering and joining other event organizing teams.
    """
    is_admin = request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.is_admin)

    if is_admin:
        events = Event.objects.all().select_related('category', 'college', 'coordinator').prefetch_related('coordinator_team')
    else:
        events = Event.objects.filter(
            Q(coordinator=request.user) |
            Q(coordinator_team__user=request.user, coordinator_team__status='APPROVED')
        ).distinct().select_related('category', 'college', 'coordinator').prefetch_related('coordinator_team')

    # Tag user's role on each event
    for ev in events:
        if ev.coordinator == request.user:
            ev.my_role_label = "Lead Coordinator"
            ev.is_my_lead = True
            ev.pending_count = ev.coordinator_team.filter(status='PENDING').count()
        else:
            team_rec = ev.coordinator_team.filter(user=request.user, status='APPROVED').first()
            ev.my_role_label = team_rec.get_role_display() if team_rec else "Co-Coordinator"
            ev.is_my_lead = False
            ev.pending_count = 0

    total_events = events.count()
    total_registrations = Registration.objects.filter(event__in=events, status='CONFIRMED').count()
    total_checked_in = Registration.objects.filter(event__in=events, status='CONFIRMED', is_checked_in=True).count()
    avg_attendance = round((total_checked_in / total_registrations * 100)) if total_registrations > 0 else 0

    unanswered_questions_count = EventQuestion.objects.filter(
        event__in=events,
        answer__isnull=True
    ).count() + EventQuestion.objects.filter(event__in=events, answer='').count()

    # Discover other upcoming events available to join
    my_event_ids = [e.id for e in events]
    pending_event_ids = list(EventCoordinatorTeam.objects.filter(user=request.user, status='PENDING').values_list('event_id', flat=True))
    available_events_to_join = Event.objects.filter(
        is_published=True,
        end_date__gte=timezone.now()
    ).exclude(id__in=my_event_ids).exclude(id__in=pending_event_ids).select_related('category', 'college', 'coordinator')[:6]

    # Total pending join requests count for current user
    if is_admin:
        pending_join_requests_count = EventCoordinatorTeam.objects.filter(status='PENDING').count()
    else:
        pending_join_requests_count = EventCoordinatorTeam.objects.filter(
            event__coordinator=request.user,
            status='PENDING'
        ).count()

    # MongoDB Atlas Status
    mongo_connected, mongo_msg = check_mongo_connection()

    context = {
        'events': events,
        'available_events_to_join': available_events_to_join,
        'pending_join_requests_count': pending_join_requests_count,
        'stats': {
            'total_events': total_events,
            'total_registrations': total_registrations,
            'total_checked_in': total_checked_in,
            'avg_attendance': avg_attendance,
            'unanswered_questions_count': unanswered_questions_count,
        },
        'mongo_connected': mongo_connected,
        'mongo_msg': mongo_msg,
    }
    return render(request, 'events/coordinator_dashboard.html', context)


@login_required
def event_join_team(request, slug):
    """
    Self-service request to join an Event Organizing Team.
    Coordinator/Student requests a specific responsibility (e.g. Attendance & QR, Q&A, Co-Coordinator).
    Synchronizes to MongoDB Atlas.
    """
    event = get_object_or_404(Event, slug=slug)

    if request.method != 'POST':
        return redirect('event_detail', slug=event.slug)

    if event.coordinator == request.user:
        messages.info(request, "You are already the Lead Coordinator of this event!")
        return redirect('event_detail', slug=event.slug)

    existing = EventCoordinatorTeam.objects.filter(event=event, user=request.user).first()
    if existing:
        if existing.status == 'APPROVED':
            messages.info(request, f"You are already an active {existing.get_role_display()} on this event team!")
        elif existing.status == 'PENDING':
            messages.warning(request, f"Your request to join as {existing.get_role_display()} is already pending review from the Lead Coordinator.")
        else:
            role = request.POST.get('role', 'CO_COORDINATOR')
            pitch_note = request.POST.get('pitch_note', '').strip()
            existing.role = role
            existing.pitch_note = pitch_note
            existing.status = 'PENDING'
            existing.save()
            mongo_sync_event_team(existing)
            messages.success(request, f"Your re-application to join as {existing.get_role_display()} has been submitted!")
        return redirect('event_detail', slug=event.slug)

    role = request.POST.get('role', 'CO_COORDINATOR')
    pitch_note = request.POST.get('pitch_note', '').strip()

    membership = EventCoordinatorTeam.objects.create(
        event=event,
        user=request.user,
        role=role,
        pitch_note=pitch_note,
        status='PENDING'
    )
    mongo_sync_event_team(membership)

    lead_name = event.coordinator.get_full_name() or event.coordinator.username
    messages.success(request, f"Request to join the Organizing Team for '{event.title}' submitted! {lead_name} will review your request.")
    return redirect('event_detail', slug=event.slug)


@login_required
def coordinator_manage_team_request(request, membership_id, action):
    """
    Lead Coordinator or Admin approves or rejects a 'Join Event Team' request.
    When approved, automatically grants coordinator portal access.
    Synchronizes to MongoDB Atlas.
    """
    membership = get_object_or_404(EventCoordinatorTeam, id=membership_id)
    event = membership.event

    if not (event.coordinator == request.user or request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.is_admin)):
        messages.error(request, "You do not have permission to manage this event team.")
        return redirect('coordinator_dashboard')

    applicant_name = membership.user.get_full_name() or membership.user.username

    if action == 'APPROVE':
        membership.status = 'APPROVED'
        membership.approved_by = request.user
        membership.save()

        # Ensure applicant profile can access coordinator portal
        profile = getattr(membership.user, 'profile', None)
        if profile and profile.role == 'STUDENT':
            profile.role = 'COORDINATOR'
            profile.save()
            mongo_sync_user(membership.user, profile)

        mongo_sync_event_team(membership)
        messages.success(request, f"Approved {applicant_name} as {membership.get_role_display()} for '{event.title}'! They now have team access.")

    elif action == 'REJECT':
        membership.status = 'REJECTED'
        membership.save()
        mongo_sync_event_team(membership)
        messages.info(request, f"Request from {applicant_name} was rejected.")

    return redirect('coordinator_manage_event', slug=event.slug)


@login_required
def coordinator_update_team_role(request, membership_id):
    """
    Lead Coordinator or Admin re-assigns responsibilities in the organizing team.
    """
    if request.method != 'POST':
        return redirect('coordinator_dashboard')

    membership = get_object_or_404(EventCoordinatorTeam, id=membership_id)
    event = membership.event

    if not (event.coordinator == request.user or request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.is_admin)):
        messages.error(request, "You do not have permission to modify roles on this event team.")
        return redirect('coordinator_dashboard')

    if membership.role == 'LEAD' and membership.user == event.coordinator:
        messages.warning(request, "The event creator cannot be demoted from Lead Coordinator.")
        return redirect('coordinator_manage_event', slug=event.slug)

    new_role = request.POST.get('role')
    custom_role = request.POST.get('custom_role', '').strip()

    if new_role:
        membership.role = new_role
        membership.custom_role = custom_role
        membership.save()
        mongo_sync_event_team(membership)
        member_name = membership.user.get_full_name() or membership.user.username
        messages.success(request, f"Updated role for {member_name} to {membership.get_role_display()}!")

    return redirect('coordinator_manage_event', slug=event.slug)


@login_required
def coordinator_remove_team_member(request, membership_id):
    """
    Lead Coordinator or Admin removes a member from the organizing team.
    """
    membership = get_object_or_404(EventCoordinatorTeam, id=membership_id)
    event = membership.event

    if not (event.coordinator == request.user or request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.is_admin)):
        messages.error(request, "You do not have permission to remove team members.")
        return redirect('coordinator_dashboard')

    if membership.role == 'LEAD' or membership.user == event.coordinator:
        messages.error(request, "Cannot remove the Lead Coordinator / Event Creator.")
        return redirect('coordinator_manage_event', slug=event.slug)

    member_name = membership.user.get_full_name() or membership.user.username
    membership.delete()

    db = get_mongo_db()
    if db is not None:
        try:
            db['event_teams'].delete_one({'event_slug': event.slug, 'username': membership.user.username})
        except Exception:
            pass

    messages.info(request, f"Removed {member_name} from the '{event.title}' organizing team.")
    return redirect('coordinator_manage_event', slug=event.slug)


@login_required
@user_passes_test(is_coordinator_or_admin)
def coordinator_manage_event(request, slug):
    """
    Detailed management for an event:
    Attendee roster, manual check-in toggle, announcement sender, Q&A replies,
    and Organizing Team delegation & join request approvals.
    """
    event = get_object_or_404(Event, slug=slug)

    # Permission check: Lead Coordinator, Approved Team Member, or Admin
    if not event.is_user_coordinator(request.user):
        messages.error(request, "You do not have permission to manage this event.")
        return redirect('coordinator_dashboard')

    is_lead = (event.coordinator == request.user or request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.is_admin))
    user_team_membership = event.get_user_team_membership(request.user)

    # Post announcement
    if request.method == 'POST' and 'post_announcement' in request.POST:
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        is_urgent = 'is_urgent' in request.POST
        if title and content:
            announcement = Announcement.objects.create(
                event=event,
                title=title,
                content=content,
                posted_by=request.user,
                is_urgent=is_urgent
            )
            mongo_sync_announcement(announcement)
            messages.success(request, "Announcement published successfully!")
            return redirect('coordinator_manage_event', slug=event.slug)

    # Answer question
    if request.method == 'POST' and 'answer_question' in request.POST:
        q_id = request.POST.get('question_id')
        answer_text = request.POST.get('answer', '').strip()
        question = get_object_or_404(EventQuestion, id=q_id, event=event)
        if answer_text:
            question.answer = answer_text
            question.answered_by = request.user
            question.answered_at = timezone.now()
            question.save()
            mongo_sync_question(question)
            messages.success(request, "Question answered successfully!")
            return redirect('coordinator_manage_event', slug=event.slug)

    # Filter registrations
    reg_filter = request.GET.get('filter', 'all')
    registrations = event.registrations.select_related('user', 'user__profile')
    if reg_filter == 'checked_in':
        registrations = registrations.filter(is_checked_in=True)
    elif reg_filter == 'pending':
        registrations = registrations.filter(is_checked_in=False)

    questions = event.questions.select_related('student', 'answered_by')
    announcements = event.announcements.all()
    approved_team = event.get_approved_team()
    pending_team_requests = event.get_pending_team_requests() if is_lead else []

    context = {
        'event': event,
        'registrations': registrations,
        'questions': questions,
        'announcements': announcements,
        'approved_team': approved_team,
        'pending_team_requests': pending_team_requests,
        'is_lead': is_lead,
        'user_team_membership': user_team_membership,
        'reg_filter': reg_filter,
    }
    return render(request, 'events/coordinator_manage_event.html', context)


@login_required
@user_passes_test(is_coordinator_or_admin)
def coordinator_toggle_checkin(request, reg_id):
    """
    1-click manual check-in toggle from the coordinator roster.
    Synchronizes attendance to MongoDB Atlas 'attendance' collection.
    """
    registration = get_object_or_404(Registration, id=reg_id)
    if not registration.event.is_user_coordinator(request.user):
        messages.error(request, "You do not have permission to check in attendees for this event.")
        return redirect('coordinator_dashboard')

    registration.is_checked_in = not registration.is_checked_in
    if registration.is_checked_in:
        registration.checked_in_at = timezone.now()
        registration.checked_in_by = request.user
        mongo_record_attendance(registration, request.user)
    else:
        registration.checked_in_at = None
        registration.checked_in_by = None
    registration.save()

    messages.info(
        request,
        f"Updated check-in status for {registration.user.get_full_name() or registration.user.username}."
    )
    return redirect('coordinator_manage_event', slug=registration.event.slug)


@login_required
@user_passes_test(is_coordinator_or_admin)
def coordinator_scanner(request, slug):
    """
    Live QR Attendance Scanner:
    Accessible by Lead Coordinator and all Approved Organizing Team Members.
    Multiple coordinators can scan simultaneously without duplicate check-ins.
    """
    event = get_object_or_404(Event, slug=slug)

    if not event.is_user_coordinator(request.user):
        messages.error(request, "You do not have permission to scan tickets for this event.")
        return redirect('coordinator_dashboard')

    membership = event.get_user_team_membership(request.user)

    context = {
        'event': event,
        'membership': membership,
    }
    return render(request, 'events/coordinator_scanner.html', context)



@login_required
def api_scan_ticket(request):
    """
    AJAX endpoint for the live QR scanner.
    Validates token, checks duplicates, updates check-in,
    and inserts verified record into MongoDB Atlas 'attendance' collection.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        token_str = data.get('token', '').strip()
        event_id = data.get('event_id')

        if not token_str:
            return JsonResponse({'success': False, 'message': 'QR Token is missing.'}, status=400)

        # Parse UUID
        try:
            token_uuid = uuid.UUID(token_str)
        except ValueError:
            return JsonResponse({'success': False, 'message': 'Invalid QR code format. Not a recognized pass token.'}, status=400)

        registration = Registration.objects.select_related('user', 'user__profile', 'event').filter(
            registration_token=token_uuid
        ).first()

        if not registration:
            return JsonResponse({
                'success': False,
                'status_code': 'NOT_FOUND',
                'message': 'No registration found matching this QR code.'
            }, status=404)

        # Check if pass matches this specific event
        if event_id and str(registration.event.id) != str(event_id):
            return JsonResponse({
                'success': False,
                'status_code': 'WRONG_EVENT',
                'message': f"Ticket is for '{registration.event.title}', not this event!",
                'registered_event': registration.event.title
            })

        user = registration.user
        profile = getattr(user, 'profile', None)

        # Check if already checked in
        if registration.is_checked_in:
            time_formatted = registration.checked_in_at.strftime("%I:%M %p") if registration.checked_in_at else "Earlier"
            return JsonResponse({
                'success': False,
                'status_code': 'ALREADY_CHECKED_IN',
                'message': f"Already Checked In at {time_formatted}!",
                'attendee': {
                    'name': user.get_full_name() or user.username,
                    'email': user.email,
                    'college': profile.college if profile else 'N/A',
                    'department': profile.department if profile else 'N/A',
                    'team_name': registration.team_name,
                    'checked_in_at': time_formatted,
                },
                'stats': {
                    'total': registration.event.confirmed_registrations_count,
                    'checked_in': registration.event.checked_in_count,
                    'remaining': registration.event.confirmed_registrations_count - registration.event.checked_in_count
                }
            })

        # Mark attendance!
        registration.is_checked_in = True
        registration.checked_in_at = timezone.now()
        registration.checked_in_by = request.user
        registration.save()

        # Save verified attendance document in MongoDB Atlas 'attendance' collection
        mongo_record_attendance(registration, request.user)

        return JsonResponse({
            'success': True,
            'status_code': 'SUCCESS',
            'message': 'Attendance marked successfully! Welcome to the event.',
            'attendee': {
                'name': user.get_full_name() or user.username,
                'email': user.email,
                'college': profile.college if profile else 'N/A',
                'department': profile.department if profile else 'N/A',
                'team_name': registration.team_name,
                'checked_in_at': registration.checked_in_at.strftime("%I:%M %p"),
            },
            'stats': {
                'total': registration.event.confirmed_registrations_count,
                'checked_in': registration.event.checked_in_count,
                'remaining': registration.event.confirmed_registrations_count - registration.event.checked_in_count
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Server error: {str(e)}'}, status=500)


@login_required
@user_passes_test(is_coordinator_or_admin)
def coordinator_export_attendees(request, slug):
    """
    Exports attendee roster as a clean CSV file.
    """
    event = get_object_or_404(Event, slug=slug)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{event.slug}_attendees.csv"'

    writer = csv.writer(response)
    writer.writerow(['Student Name', 'Username', 'Email', 'College', 'Department', 'Team Name', 'Checked In', 'Check-in Time', 'Registered At', 'Pass Token'])

    registrations = event.registrations.select_related('user', 'user__profile')
    for r in registrations:
        profile = getattr(r.user, 'profile', None)
        writer.writerow([
            r.user.get_full_name() or r.user.username,
            r.user.username,
            r.user.email,
            profile.college if profile else '',
            profile.department if profile else '',
            r.team_name,
            'Yes' if r.is_checked_in else 'No',
            r.checked_in_at.strftime("%Y-%m-%d %H:%M") if r.checked_in_at else '',
            r.registered_at.strftime("%Y-%m-%d %H:%M"),
            str(r.registration_token)
        ])

    return response


@login_required
@user_passes_test(is_coordinator_or_admin)
def coordinator_create_event(request):
    """
    Create a new actual campus event or hackathon.
    Persists and synchronizes directly to MongoDB Atlas 'events' collection.
    """
    categories = Category.objects.all()
    colleges = College.objects.all()

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        category_id = request.POST.get('category_id')
        short_description = request.POST.get('short_description', '').strip()
        description = request.POST.get('description', '').strip()
        event_mode = request.POST.get('event_mode', 'OFFLINE')
        venue = request.POST.get('venue', '').strip()
        college_name = request.POST.get('college_name', 'Campus Institute of Technology').strip()
        department = request.POST.get('department', 'Computer Science & Engineering').strip()
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        deadline_str = request.POST.get('registration_deadline')
        capacity = int(request.POST.get('capacity', 100))
        fee = float(request.POST.get('registration_fee', 0.0))
        prize_pool = request.POST.get('prize_pool', '').strip()
        is_team_event = 'is_team_event' in request.POST
        min_team = int(request.POST.get('min_team_size', 1))
        max_team = int(request.POST.get('max_team_size', 4))
        eligibility = request.POST.get('eligibility', '').strip()
        rules = request.POST.get('rules', '').strip()
        banner_gradient = request.POST.get('banner_gradient', 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)')

        category = Category.objects.filter(id=category_id).first()

        event = Event.objects.create(
            title=title,
            category=category,
            coordinator=request.user,
            coordinator_name=request.user.get_full_name() or request.user.username,
            coordinator_email=request.user.email,
            short_description=short_description,
            description=description,
            event_mode=event_mode,
            venue=venue,
            college_name=college_name,
            department=department,
            start_date=start_date_str,
            end_date=end_date_str,
            registration_deadline=deadline_str,
            capacity=capacity,
            registration_fee=fee,
            prize_pool=prize_pool,
            is_team_event=is_team_event,
            min_team_size=min_team,
            max_team_size=max_team,
            eligibility=eligibility,
            rules=rules,
            banner_gradient=banner_gradient,
            is_published=True
        )

        # Synchronize event to MongoDB Atlas 'events' collection
        mongo_sync_event(event)

        messages.success(request, f"Event '{event.title}' created and published successfully!")
        return redirect('event_detail', slug=event.slug)

    context = {
        'categories': categories,
        'colleges': colleges,
    }
    return render(request, 'events/coordinator_event_form.html', context)


# ==========================================
# ADMIN DASHBOARD & MONGODB DIAGNOSTICS
# ==========================================

@login_required
@user_passes_test(is_admin_user)
def admin_dashboard(request):
    """
    Campus Administrator Control Center:
    Monitors live platform statistics and MongoDB Atlas health.
    """
    coordinators = UserProfile.objects.filter(role__in=['COORDINATOR', 'ADMIN']).select_related('user')
    events = Event.objects.all().select_related('category', 'coordinator').order_by('-created_at')

    total_students = UserProfile.objects.filter(role='STUDENT').count()
    total_coordinators = UserProfile.objects.filter(role='COORDINATOR').count()
    total_events = Event.objects.count()
    total_registrations = Registration.objects.count()
    total_checkins = Registration.objects.filter(is_checked_in=True).count()

    # MongoDB Atlas Status & Collection Counts
    mongo_connected, mongo_msg = check_mongo_connection()
    atlas_counts, has_atlas_data = get_atlas_collection_counts()

    context = {
        'coordinators': coordinators,
        'events': events,
        'stats': {
            'total_students': total_students,
            'total_coordinators': total_coordinators,
            'total_events': total_events,
            'total_registrations': total_registrations,
            'total_checkins': total_checkins,
        },
        'mongo_connected': mongo_connected,
        'mongo_msg': mongo_msg,
        'atlas_counts': atlas_counts,
        'has_atlas_data': has_atlas_data,
    }
    return render(request, 'events/admin_dashboard.html', context)


@login_required
@user_passes_test(is_admin_user)
def admin_toggle_coordinator(request, profile_id):
    """
    Approve or toggle coordinator permissions.
    """
    profile = get_object_or_404(UserProfile, id=profile_id)
    profile.is_approved = not profile.is_approved
    profile.save()
    mongo_sync_user(profile.user, profile)
    messages.success(request, f"Coordinator status updated for {profile.user.username}.")
    return redirect('admin_dashboard')


def mongodb_status(request):
    """
    Diagnostic endpoint for testing MongoDB Atlas connectivity and 8 collections.
    """
    connected, details = check_mongo_connection()
    counts, has_data = get_atlas_collection_counts()

    return JsonResponse({
        'mongodb_connected': connected,
        'status_message': details,
        'collections_counts': counts,
        'target_collections': [
            'users', 'events', 'registrations', 'teams',
            'event_questions', 'attendance', 'announcements', 'feedback'
        ]
    })


# ==========================================
# AUTHENTICATION (REAL USER REGISTRATION)
# ==========================================

def auth_login(request):
    """
    Standard login page for actual accounts.
    """
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.GET.get('next')
            return redirect(next_url if next_url else 'home')
        else:
            messages.error(request, "Invalid username or password. Please try again.")

    return render(request, 'auth/login.html')


def auth_register(request):
    """
    Actual Student or Coordinator registration.
    Inserts directly into MongoDB Atlas 'users' collection.
    """
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        password = request.POST.get('password', '').strip()
        role = request.POST.get('role', 'STUDENT')
        college = request.POST.get('college', 'Apex Institute of Technology').strip()
        department = request.POST.get('department', 'Computer Science & Engineering').strip()
        year_of_study = request.POST.get('year_of_study', '3rd Year').strip()
        phone = request.POST.get('phone', '').strip()

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken. Please choose another.")
            return render(request, 'auth/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
            return render(request, 'auth/register.html')

        is_staff_role = role in ['COORDINATOR', 'ADMIN']
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_staff=is_staff_role
        )

        profile = UserProfile.objects.create(
            user=user,
            role=role,
            college=college,
            department=department,
            year_of_study=year_of_study,
            phone=phone,
            is_approved=True
        )

        # Synchronize to MongoDB Atlas 'users' collection
        mongo_sync_user(user, profile)

        login(request, user)
        messages.success(request, f"Welcome to CampusConnect, {first_name}! Your account has been registered.")
        return redirect('home')

    return render(request, 'auth/register.html')


def auth_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')
