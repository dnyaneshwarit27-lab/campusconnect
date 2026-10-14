import uuid
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from events.models import (
    UserProfile,
    Category,
    College,
    Event,
    Registration,
    EventQuestion,
    Announcement,
    TeamFinderPost,
    EventFeedback,
)
from events.mongodb import (
    get_mongo_db,
    check_mongo_connection,
    mongo_sync_user,
    mongo_sync_event,
    mongo_sync_registration,
    mongo_record_attendance,
    mongo_sync_question,
    mongo_sync_announcement,
)


class Command(BaseCommand):
    help = 'Initializes and populates all 8 MongoDB Atlas collections with live dynamic data'

    def handle(self, *args, **options):
        self.stdout.write("Checking MongoDB Atlas connection...")
        connected, msg = check_mongo_connection()
        if not connected:
            self.stdout.write(self.style.WARNING(f"MongoDB connection notice: {msg}"))
            self.stdout.write(self.style.WARNING("Proceeding to initialize local Django database first..."))
            db = None
        else:
            self.stdout.write(self.style.SUCCESS(f"Connected: {msg}"))
            db = get_mongo_db()
        now = timezone.now()

        # 1. Categories
        categories_data = [
            {"name": "Hackathons", "slug": "hackathons", "icon": "bi-code-slash", "badge_color": "#6366f1"},
            {"name": "AI & Tech Workshops", "slug": "workshops", "icon": "bi-cpu", "badge_color": "#8b5cf6"},
            {"name": "Coding Competitions", "slug": "coding", "icon": "bi-terminal", "badge_color": "#ec4899"},
            {"name": "Project Exhibitions", "slug": "exhibitions", "icon": "bi-display", "badge_color": "#06b6d4"},
            {"name": "Cultural & Tech Fests", "slug": "fests", "icon": "bi-stars", "badge_color": "#f59e0b"},
            {"name": "Robotics & Hardware", "slug": "robotics", "icon": "bi-robot", "badge_color": "#10b981"},
        ]
        categories = {}
        for cdata in categories_data:
            cat, _ = Category.objects.get_or_create(slug=cdata["slug"], defaults=cdata)
            categories[cdata["slug"]] = cat

        # 2. Colleges
        college, _ = College.objects.get_or_create(
            name="Apex Institute of Technology",
            defaults={"code": "AIT", "city": "Pune", "is_partner": True}
        )

        # 3. Users (Student, Coordinator, Admin)
        # Student: Dnyaneshwari
        student_user, _ = User.objects.get_or_create(
            username="dnyaneshwari",
            defaults={
                "email": "dnyaneshwarit27@gmail.com",
                "first_name": "Dnyaneshwari",
                "last_name": "T",
            }
        )
        student_user.set_password("student123")
        student_user.save()
        student_profile, _ = UserProfile.objects.get_or_create(
            user=student_user,
            defaults={
                "role": "STUDENT",
                "college": "Apex Institute of Technology",
                "department": "Computer Science & Engineering",
                "year_of_study": "3rd Year",
                "phone": "+91 98765 43210",
                "skills": "Python, Django, React, MongoDB, UI/UX",
                "avatar_color": "#10b981",
                "is_approved": True,
            }
        )
        mongo_sync_user(student_user, student_profile)

        # Student: Dnyanu Thorat
        dnyanu_user, _ = User.objects.get_or_create(
            username="dnyanu@",
            defaults={
                "email": "dnyanu@gmail.com",
                "first_name": "dnyanu",
                "last_name": "thorat",
            }
        )
        dnyanu_user.set_password("dnyanu@01")
        dnyanu_user.save()
        dnyanu_profile, _ = UserProfile.objects.get_or_create(
            user=dnyanu_user,
            defaults={
                "role": "STUDENT",
                "college": "Apex Institute of Technology",
                "department": "Computer Science & Engineering",
                "year_of_study": "3rd Year",
                "phone": "6783938292",
                "avatar_color": "#06b6d4",
                "is_approved": True,
            }
        )
        mongo_sync_user(dnyanu_user, dnyanu_profile)

        # Coordinator: Pooja
        coord_user, _ = User.objects.get_or_create(
            username="coordinator",
            defaults={
                "email": "coordinator@campusconnect.edu",
                "first_name": "Pooja",
                "last_name": "Deshmukh",
                "is_staff": True,
            }
        )
        coord_user.set_password("coord123")
        coord_user.save()
        coord_profile, _ = UserProfile.objects.get_or_create(
            user=coord_user,
            defaults={
                "role": "COORDINATOR",
                "college": "Apex Institute of Technology",
                "department": "Computer Science & Engineering",
                "year_of_study": "Event Lead",
                "phone": "+91 91234 56789",
                "skills": "Event Planning, Full-stack Dev",
                "avatar_color": "#8b5cf6",
                "is_approved": True,
            }
        )
        mongo_sync_user(coord_user, coord_profile)

        # Admin: Dr. Rajesh Kulkarni
        admin_user, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@campusconnect.edu",
                "first_name": "Dr. Rajesh",
                "last_name": "Kulkarni",
                "is_staff": True,
                "is_superuser": True,
            }
        )
        admin_user.set_password("admin123")
        admin_user.save()
        admin_profile, _ = UserProfile.objects.get_or_create(
            user=admin_user,
            defaults={
                "role": "ADMIN",
                "college": "Apex Institute of Technology",
                "department": "Campus Administration",
                "year_of_study": "Dean Office",
                "avatar_color": "#ef4444",
                "is_approved": True,
            }
        )
        mongo_sync_user(admin_user, admin_profile)

        # 4. Events
        events_data = [
            {
                "title": "Smart Campus Hackathon 2026",
                "slug": "smart-campus-hackathon-2026",
                "category": categories["hackathons"],
                "coordinator": coord_user,
                "college": college,
                "college_name": college.name,
                "department": "Computer Science & Engineering",
                "short_description": "36-hour flagship hackathon building AI, IoT & Web solutions for sustainable smart campuses.",
                "description": """Welcome to Smart Campus Hackathon 2026!
Tracks:
1. AI & Campus Automation (Smart chatbots, automated timetable sync)
2. Student Community & Well-being
3. Green Campus & IoT Sustainability

Perks: 24/7 High-speed WiFi, complimentary meals & midnight snacks, mentorship from tech leads, cash prizes and digital certificates.""",
                "event_mode": "OFFLINE",
                "venue": "Main Tech Complex, Auditorium Block B",
                "start_date": now + timedelta(days=5, hours=9),
                "end_date": now + timedelta(days=7, hours=18),
                "registration_deadline": now + timedelta(days=4, hours=23),
                "capacity": 150,
                "registration_fee": 0.00,
                "prize_pool": "₹75,000 Cash + Cloud Credits",
                "is_team_event": True,
                "min_team_size": 2,
                "max_team_size": 4,
                "eligibility": "All college and polytechnic students with valid college ID.",
                "rules": "1. All code must be developed during the hackathon.\n2. Valid college ID is compulsory.\n3. QR Attendance check-in at entrance is mandatory.",
                "banner_gradient": "linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)",
                "is_featured": True,
            },
            {
                "title": "GenAI & Agentic Systems Workshop",
                "slug": "genai-agentic-systems-workshop",
                "category": categories["workshops"],
                "coordinator": coord_user,
                "college": college,
                "college_name": college.name,
                "department": "AI & Data Science",
                "short_description": "Hands-on deep dive into building autonomous AI agents, multi-tool LLMs, and RAG architectures.",
                "description": """Learn how modern LLM applications are built beyond simple prompt engineering.
Curriculum:
- Module 1: Tool calling & Structured Outputs
- Module 2: Vector Search & Retrieval Augmented Generation (RAG)
- Module 3: Agentic autonomous loops & error recovery
- Module 4: Deployment & evaluation""",
                "event_mode": "HYBRID",
                "venue": "Lab 402, CS Building & Online Zoom Stream",
                "start_date": now + timedelta(days=2, hours=10),
                "end_date": now + timedelta(days=2, hours=16),
                "registration_deadline": now + timedelta(days=1, hours=20),
                "capacity": 80,
                "registration_fee": 99.00,
                "prize_pool": "Certificate of Completion + GPU Compute Credits",
                "is_team_event": False,
                "min_team_size": 1,
                "max_team_size": 1,
                "eligibility": "Students of any year/department with interest in Artificial Intelligence.",
                "rules": "Bring personal laptops with Python installed.",
                "banner_gradient": "linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%)",
                "is_featured": True,
            },
            {
                "title": "Algorithm Arena: CodeSprint 2026",
                "slug": "algorithm-arena-codesprint-2026",
                "category": categories["coding"],
                "coordinator": coord_user,
                "college": college,
                "college_name": college.name,
                "department": "Computer Science & Engineering",
                "short_description": "Speed coding contest featuring dynamic programming, graph theory and lightning rounds.",
                "description": """3 intense algorithmic rounds under the clock!
Languages: C++, Java, Python, Go.""",
                "event_mode": "ONLINE",
                "venue": "CampusConnect Arena (Online)",
                "start_date": now + timedelta(days=8, hours=15),
                "end_date": now + timedelta(days=8, hours=18),
                "registration_deadline": now + timedelta(days=7, hours=23),
                "capacity": 200,
                "registration_fee": 0.00,
                "prize_pool": "₹25,000 + Top Coder Trophies",
                "is_team_event": False,
                "min_team_size": 1,
                "max_team_size": 1,
                "eligibility": "All enrolled college students.",
                "rules": "Strict automated plagiarism check enforced.",
                "banner_gradient": "linear-gradient(135deg, #ec4899 0%, #f43f5e 100%)",
                "is_featured": False,
            },
            {
                "title": "RoboClash: Autonomous Robot Battles",
                "slug": "roboclash-autonomous-robot-battles",
                "category": categories["robotics"],
                "coordinator": coord_user,
                "college": college,
                "college_name": college.name,
                "department": "Mechanical & Robotics",
                "short_description": "Exciting combat robotics and obstacle race championship in the campus central arena.",
                "description": """Combat robotics tournament: RoboWars (15kg featherweight) and Line Followers.""",
                "event_mode": "OFFLINE",
                "venue": "Central Sports Ground Arena",
                "start_date": now + timedelta(days=12, hours=11),
                "end_date": now + timedelta(days=13, hours=19),
                "registration_deadline": now + timedelta(days=10, hours=18),
                "capacity": 60,
                "registration_fee": 250.00,
                "prize_pool": "₹50,000 Cash + Championship Shields",
                "is_team_event": True,
                "min_team_size": 2,
                "max_team_size": 5,
                "eligibility": "Engineering & polytechnic teams.",
                "rules": "All bots must pass safety inspection.",
                "banner_gradient": "linear-gradient(135deg, #10b981 0%, #059669 100%)",
                "is_featured": True,
            }
        ]

        created_events = {}
        for edata in events_data:
            ev, _ = Event.objects.get_or_create(
                slug=edata["slug"],
                defaults=edata
            )
            mongo_sync_event(ev)
            created_events[edata["slug"]] = ev

        # 5. Registrations & Teams
        hackathon = created_events["smart-campus-hackathon-2026"]
        workshop = created_events["genai-agentic-systems-workshop"]

        # Student registered for Hackathon
        r1, _ = Registration.objects.get_or_create(
            event=hackathon,
            user=student_user,
            defaults={
                "status": "CONFIRMED",
                "team_name": "CodeCrafters",
                "team_members_info": "1. Dnyaneshwari T (Team Lead)\n2. Sneha Patil (UI/UX)\n3. Vikram Singh (ML/Backend)",
                "notes": "Building smart campus companion app."
            }
        )
        mongo_sync_registration(r1)

        # Student registered for Workshop & Checked in
        r2, _ = Registration.objects.get_or_create(
            event=workshop,
            user=student_user,
            defaults={
                "status": "CONFIRMED",
                "is_checked_in": True,
                "checked_in_at": now - timedelta(hours=1),
                "checked_in_by": coord_user,
                "notes": "Interested in AI agentic workflows."
            }
        )
        mongo_sync_registration(r2)
        mongo_record_attendance(r2, coord_user)

        # 6. Event Questions & Answers
        q1, _ = EventQuestion.objects.get_or_create(
            event=hackathon,
            student=student_user,
            question="Is it compulsory to bring our own laptops, or will lab workstations be provided?",
            defaults={
                "answer": "Bringing your personal laptop is strongly recommended. Power sockets, high-speed Wi-Fi, and secondary monitors will be provided.",
                "answered_by": coord_user,
                "answered_at": now - timedelta(hours=6),
                "is_public": True
            }
        )
        mongo_sync_question(q1)

        # 7. Announcements
        ann1, _ = Announcement.objects.get_or_create(
            event=hackathon,
            title="Important: Check-In & Venue Reporting Instructions",
            defaults={
                "content": "Please arrive at Auditorium Block B between 8:30 AM and 9:30 AM with your CampusConnect digital QR pass ready on your phone for instant check-in.",
                "posted_by": coord_user,
                "is_urgent": True
            }
        )
        mongo_sync_announcement(ann1)

        # 8. Team Finder
        TeamFinderPost.objects.get_or_create(
            event=hackathon,
            user=student_user,
            title="Looking for a Full-Stack or Flutter developer for Smart Campus Hackathon",
            defaults={
                "description": "We are building an automated campus companion app with AI attendance sync. Backend is in Django & MongoDB, looking for mobile or frontend dev.",
                "skills_offered": "Python, Django, MongoDB, Machine Learning",
                "skills_needed": "Flutter, React Native, UI/UX",
                "contact_handle": "dnyaneshwarit27@gmail.com",
                "is_open": True
            }
        )

        # 9. Feedback
        if db is not None:
            db['feedback'].update_one(
                {'registration_token': str(r2.registration_token)},
                {'$set': {
                    'event_title': workshop.title,
                    'student_username': student_user.username,
                    'rating': 5,
                    'comments': 'Excellent hands-on session on GenAI agents and RAG pipelines!',
                    'submitted_at': now.isoformat()
                }},
                upsert=True
            )

            # Display collection counts directly from MongoDB Atlas
            self.stdout.write("\n=== MongoDB Atlas Collection Document Counts ===")
            for col_name in ['users', 'events', 'registrations', 'teams', 'event_questions', 'attendance', 'announcements', 'feedback']:
                cnt = db[col_name].count_documents({})
                self.stdout.write(f"  • {col_name}: {cnt} documents")

            self.stdout.write(self.style.SUCCESS(
                "\nSuccessfully initialized all 8 collections in MongoDB Atlas ('campusconnect_db') with live dynamic data!"
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                "\nSuccessfully seeded all Django models (Colleges, Categories, Users, Events, Registrations)!"
            ))
            self.stdout.write(self.style.WARNING(
                "MongoDB Atlas sync was skipped because MONGODB_URI is not set. Add MONGODB_URI in Render dashboard to sync with Atlas."
            ))
