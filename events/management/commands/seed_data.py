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
)


class Command(BaseCommand):
    help = 'Seeds realistic sample data for CampusConnect'

    def handle(self, *args, **options):
        self.stdout.write("Seeding CampusConnect database...")

        # 1. Colleges
        colleges_data = [
            {"name": "Apex Institute of Technology", "code": "AIT", "city": "Pune"},
            {"name": "National College of Engineering", "code": "NCE", "city": "Mumbai"},
            {"name": "Metropolitan Institute of Science & Tech", "code": "MIST", "city": "Bengaluru"},
        ]
        colleges = {}
        for cdata in colleges_data:
            col, _ = College.objects.get_or_create(
                name=cdata["name"],
                defaults={"code": cdata["code"], "city": cdata["city"], "is_partner": True}
            )
            colleges[cdata["code"]] = col

        # 2. Categories
        categories_data = [
            {
                "name": "Hackathons",
                "slug": "hackathons",
                "icon": "bi-code-slash",
                "badge_color": "#6366f1",
                "description": "36-48 hour intensive coding and prototyping competitions."
            },
            {
                "name": "AI & Tech Workshops",
                "slug": "workshops",
                "icon": "bi-cpu",
                "badge_color": "#8b5cf6",
                "description": "Hands-on masterclasses on GenAI, Cloud, and modern developer toolchains."
            },
            {
                "name": "Coding Competitions",
                "slug": "coding",
                "icon": "bi-terminal",
                "badge_color": "#ec4899",
                "description": "Speed coding, algorithmic problem solving and bug hunting contests."
            },
            {
                "name": "Project Exhibitions",
                "slug": "exhibitions",
                "icon": "bi-display",
                "badge_color": "#06b6d4",
                "description": "Showcase final year innovations, hardware prototypes & research."
            },
            {
                "name": "Cultural & Tech Fests",
                "slug": "fests",
                "icon": "bi-stars",
                "badge_color": "#f59e0b",
                "description": "College flagship fests with concerts, gaming arenas & entertainment."
            },
            {
                "name": "Robotics & Hardware",
                "slug": "robotics",
                "icon": "bi-robot",
                "badge_color": "#10b981",
                "description": "Line followers, bot fights, and embedded IoT innovation arenas."
            },
        ]
        categories = {}
        for cat in categories_data:
            c, _ = Category.objects.get_or_create(
                slug=cat["slug"],
                defaults={
                    "name": cat["name"],
                    "icon": cat["icon"],
                    "badge_color": cat["badge_color"],
                    "description": cat["description"]
                }
            )
            categories[cat["slug"]] = c

        # 3. Create Users (Admin, Coordinator, Student)
        # Admin
        admin_user, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@campusconnect.edu",
                "first_name": "Dr. Rajesh",
                "last_name": "Kulkarni",
                "is_staff": True,
                "is_superuser": True
            }
        )
        admin_user.set_password("admin123")
        admin_user.save()
        UserProfile.objects.get_or_create(
            user=admin_user,
            defaults={
                "role": "ADMIN",
                "college": "Apex Institute of Technology",
                "department": "Campus Administration & Dean Office",
                "year_of_study": "Faculty Head",
                "is_approved": True,
                "avatar_color": "#ef4444"
            }
        )

        # Coordinator 1
        coord_user, _ = User.objects.get_or_create(
            username="coordinator",
            defaults={
                "email": "coordinator@campusconnect.edu",
                "first_name": "Pooja",
                "last_name": "Deshmukh",
                "is_staff": True
            }
        )
        coord_user.set_password("coord123")
        coord_user.save()
        UserProfile.objects.get_or_create(
            user=coord_user,
            defaults={
                "role": "COORDINATOR",
                "college": "Apex Institute of Technology",
                "department": "Computer Science & Engineering",
                "year_of_study": "4th Year Lead",
                "phone": "+91 98765 43210",
                "skills": "Event Planning, Full-stack Dev, Community Building",
                "bio": "Lead coordinator for AIT Tech Council and Hackathon Committee.",
                "is_approved": True,
                "avatar_color": "#8b5cf6"
            }
        )

        # Coordinator 2
        coord_user2, _ = User.objects.get_or_create(
            username="rohit_coord",
            defaults={
                "email": "rohit@campusconnect.edu",
                "first_name": "Rohit",
                "last_name": "Verma",
                "is_staff": True
            }
        )
        coord_user2.set_password("coord123")
        coord_user2.save()
        UserProfile.objects.get_or_create(
            user=coord_user2,
            defaults={
                "role": "COORDINATOR",
                "college": "Apex Institute of Technology",
                "department": "AI & Data Science",
                "year_of_study": "3rd Year",
                "phone": "+91 98220 11223",
                "is_approved": True,
                "avatar_color": "#06b6d4"
            }
        )

        # Student 1 (Default Student Demo)
        student_user, _ = User.objects.get_or_create(
            username="student",
            defaults={
                "email": "student@campusconnect.edu",
                "first_name": "Aarav",
                "last_name": "Sharma"
            }
        )
        student_user.set_password("student123")
        student_user.save()
        UserProfile.objects.get_or_create(
            user=student_user,
            defaults={
                "role": "STUDENT",
                "college": "Apex Institute of Technology",
                "department": "Computer Science & Engineering",
                "year_of_study": "3rd Year",
                "phone": "+91 91234 56789",
                "skills": "Python, Django, React, Machine Learning",
                "bio": "Enthusiastic developer looking for hackathon teams and open-source projects.",
                "avatar_color": "#10b981"
            }
        )

        # Student 2 & 3
        s2, _ = User.objects.get_or_create(
            username="sneha_patil",
            defaults={"email": "sneha@campusconnect.edu", "first_name": "Sneha", "last_name": "Patil"}
        )
        s2.set_password("student123")
        s2.save()
        UserProfile.objects.get_or_create(
            user=s2,
            defaults={"role": "STUDENT", "college": "Apex Institute of Technology", "department": "Information Technology", "skills": "Figma, UI/UX, Flutter", "avatar_color": "#f59e0b"}
        )

        s3, _ = User.objects.get_or_create(
            username="vikram_singh",
            defaults={"email": "vikram@campusconnect.edu", "first_name": "Vikram", "last_name": "Singh"}
        )
        s3.set_password("student123")
        s3.save()
        UserProfile.objects.get_or_create(
            user=s3,
            defaults={"role": "STUDENT", "college": "National College of Engineering", "department": "Electronics & Telecomm", "skills": "Arduino, Embedded C, Robotics", "avatar_color": "#ec4899"}
        )

        # 4. Realistic Events
        now = timezone.now()
        events_data = [
            {
                "title": "Smart Campus Hackathon 2026",
                "slug": "smart-campus-hackathon-2026",
                "category": categories["hackathons"],
                "coordinator": coord_user,
                "college": colleges["AIT"],
                "department": "Computer Science & Engineering",
                "short_description": "36-hour flagship hackathon building AI, IoT & Web solutions for sustainable smart campuses.",
                "description": """Welcome to the biggest student hackathon of the season!

Smart Campus Hackathon 2026 invites innovative coders, designers, and creators from colleges nationwide to build impactful software and hardware prototypes.

### Tracks:
1. **AI & Campus Automation:** Chatbots, smart attendance, energy optimization.
2. **Student Well-being & Community:** Mental health, campus marketplace, collaborative tools.
3. **Smart City & Green Campus:** Solar monitoring, waste segregation, IoT sensors.
4. **Open Innovation:** Any creative solution solving real-world college problems.

### What is provided:
- 24/7 High-speed Gigabit WiFi & power sockets at every workstation
- Complimentary meals, snacks, red bull & midnight pizza
- Mentorship sessions from Google, Microsoft & Startup founders
- Digital badges and participation certificates for all who attend""",
                "event_mode": "OFFLINE",
                "venue": "Main Tech Complex, Auditorium Block B, Apex Campus",
                "start_date": now + timedelta(days=5, hours=9),
                "end_date": now + timedelta(days=7, hours=18),
                "registration_deadline": now + timedelta(days=4, hours=23),
                "capacity": 150,
                "registration_fee": 0.00,
                "prize_pool": "₹75,000 Cash + Cloud Credits + Goodie Hampers",
                "is_team_event": True,
                "min_team_size": 2,
                "max_team_size": 4,
                "eligibility": "Open to all undergraduate & postgraduate college students with valid student ID.",
                "rules": "1. All code must be written during the hackathon.\n2. Open-source libraries are permitted; pre-built full applications are prohibited.\n3. Every team member must check in at the registration desk using their unique QR pass.\n4. Decisions of the jury are final.",
                "banner_gradient": "linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)",
                "is_featured": True,
            },
            {
                "title": "GenAI & Agentic Systems Workshop",
                "slug": "genai-agentic-systems-workshop",
                "category": categories["workshops"],
                "coordinator": coord_user,
                "college": colleges["AIT"],
                "department": "AI & Data Science",
                "short_description": "Hands-on deep dive into building autonomous AI agents, multi-tool LLMs, and RAG architectures.",
                "description": """Accelerate your AI skills in this intensive 1-day masterclass!

Learn how modern LLM applications are built beyond simple prompt engineering. We will build practical AI agents that can search documents, call external APIs, and execute python scripts.

### Curriculum:
- **Module 1:** Foundations of LLMs, Function Calling, and Structured Outputs.
- **Module 2:** Building Vector Search & RAG (Retrieval Augmented Generation) pipelines.
- **Module 3:** Agentic workflows with autonomous loops and error correction.
- **Module 4:** Deployment and production observability.

**Prerequisites:** Basic knowledge of Python. Please bring your personal laptop with Python 3.10+ installed.""",
                "event_mode": "HYBRID",
                "venue": "Lab 402, CS Building & Zoom Live Stream",
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
                "rules": "Attendance will be verified through the QR Code pass at the beginning of the workshop session.",
                "banner_gradient": "linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%)",
                "is_featured": True,
            },
            {
                "title": "Algorithm Arena: CodeSprint 2026",
                "slug": "algorithm-arena-codesprint-2026",
                "category": categories["coding"],
                "coordinator": coord_user2,
                "college": colleges["AIT"],
                "department": "Computer Science & Engineering",
                "short_description": "Speed coding contest featuring dynamic programming, graph theory and lightning rounds.",
                "description": """Test your algorithmic mastery and problem-solving speed under the clock!

CodeSprint 2026 brings together the sharpest minds to battle across 3 intense rounds.

### Round Details:
- **Round 1 (Speed Run):** 5 algorithmic problems in 45 minutes.
- **Round 2 (Bug Hunt & Code Optimization):** Identify subtle race conditions and memory leaks.
- **Round 3 (Grand Finals):** Live 1v1 bracket tournament projected on the main hall screen!

Languages supported: C++, Java, Python, Go, Rust.""",
                "event_mode": "ONLINE",
                "venue": "CampusConnect Arena Platform (Online)",
                "start_date": now + timedelta(days=8, hours=15),
                "end_date": now + timedelta(days=8, hours=18),
                "registration_deadline": now + timedelta(days=7, hours=23),
                "capacity": 200,
                "registration_fee": 0.00,
                "prize_pool": "₹25,000 + Top Coder Trophies",
                "is_team_event": False,
                "min_team_size": 1,
                "max_team_size": 1,
                "eligibility": "All college students.",
                "rules": "Strict plagiarism detection and automated code analysis will be enforced.",
                "banner_gradient": "linear-gradient(135deg, #ec4899 0%, #f43f5e 100%)",
                "is_featured": False,
            },
            {
                "title": "RoboClash: Autonomous Robot Battles",
                "slug": "roboclash-autonomous-robot-battles",
                "category": categories["robotics"],
                "coordinator": coord_user2,
                "college": colleges["NCE"],
                "department": "Mechanical & Robotics",
                "short_description": "Exciting combat robotics and obstacle race championship in the campus central arena.",
                "description": """Sparks will fly! RoboClash is the ultimate combat robotics tournament.

Categories include:
1. **RoboWars (15kg & 30kg featherweight robots)**
2. **Line Follower & Maze Runner**
3. **RoboSoccer Showdown**

Arena equipped with safety bulletproof acrylic walls and live scoreboard.""",
                "event_mode": "OFFLINE",
                "venue": "Central Sports Ground Arena, NCE Campus",
                "start_date": now + timedelta(days=12, hours=11),
                "end_date": now + timedelta(days=13, hours=19),
                "registration_deadline": now + timedelta(days=10, hours=18),
                "capacity": 60,
                "registration_fee": 250.00,
                "prize_pool": "₹50,000 Cash + Championship Shields",
                "is_team_event": True,
                "min_team_size": 2,
                "max_team_size": 5,
                "eligibility": "All engineering and polytechnic college teams.",
                "rules": "All bots must pass the technical inspection and fail-safe switch test on day 1.",
                "banner_gradient": "linear-gradient(135deg, #10b981 0%, #059669 100%)",
                "is_featured": True,
            },
            {
                "title": "DesignForge: UI/UX & Product Designathon",
                "slug": "designforge-ui-ux-designathon",
                "category": categories["workshops"],
                "coordinator": coord_user,
                "college": colleges["AIT"],
                "department": "Design & Human Computer Interaction",
                "short_description": "24-hour design sprint solving real user pain points with Figma prototypes and user research.",
                "description": """Great products begin with empathetic design.

DesignForge tasks participants with redesigning digital student experiences. You will conduct quick user interviews, create wireframes, test interactive prototypes in Figma, and pitch to product managers.""",
                "event_mode": "OFFLINE",
                "venue": "Innovation Studio 204, Architecture & Design Wing",
                "start_date": now + timedelta(days=15, hours=9),
                "end_date": now + timedelta(days=16, hours=12),
                "registration_deadline": now + timedelta(days=14, hours=21),
                "capacity": 50,
                "registration_fee": 0.00,
                "prize_pool": "₹30,000 + Figma Pro Subscriptions",
                "is_team_event": True,
                "min_team_size": 1,
                "max_team_size": 3,
                "eligibility": "Students interested in UI/UX, Product Management and Graphic Design.",
                "rules": "Submissions must include Figma link, problem statement rationale, and component system.",
                "banner_gradient": "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)",
                "is_featured": False,
            },
            {
                "title": "Nexus 2026: Annual Inter-College Tech Fest",
                "slug": "nexus-2026-annual-inter-college-tech-fest",
                "category": categories["fests"],
                "coordinator": coord_user,
                "college": colleges["AIT"],
                "department": "Central Student Council",
                "short_description": "The mega celebration of technology, music, gaming tournaments, laser shows and tech exhibits.",
                "description": """Nexus is the landmark annual fest celebrating innovation, engineering creativity, and student culture.

### Highlights:
- 20+ Tech Competitions & Gaming Arenas (Valorant, FIFA, BGMI)
- Keynotes from industry icons
- Project Exhibition with 100+ hardware and software prototypes
- Grand Evening Celebrity DJ Night!""",
                "event_mode": "OFFLINE",
                "venue": "Campus Open Amphitheater & Entire Tech Quadrangle",
                "start_date": now + timedelta(days=20, hours=10),
                "end_date": now + timedelta(days=22, hours=22),
                "registration_deadline": now + timedelta(days=19, hours=23),
                "capacity": 500,
                "registration_fee": 0.00,
                "prize_pool": "₹1,50,000 Prizes Across All Events",
                "is_team_event": False,
                "min_team_size": 1,
                "max_team_size": 1,
                "eligibility": "Open to students of all colleges and universities.",
                "rules": "College ID card is mandatory at the security gates.",
                "banner_gradient": "linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)",
                "is_featured": True,
            }
        ]

        created_events = {}
        for edata in events_data:
            ev, _ = Event.objects.get_or_create(
                slug=edata["slug"],
                defaults={
                    "title": edata["title"],
                    "category": edata["category"],
                    "coordinator": edata["coordinator"],
                    "college": edata["college"],
                    "college_name": edata["college"].name,
                    "department": edata["department"],
                    "short_description": edata["short_description"],
                    "description": edata["description"],
                    "event_mode": edata["event_mode"],
                    "venue": edata["venue"],
                    "start_date": edata["start_date"],
                    "end_date": edata["end_date"],
                    "registration_deadline": edata["registration_deadline"],
                    "capacity": edata["capacity"],
                    "registration_fee": edata["registration_fee"],
                    "prize_pool": edata["prize_pool"],
                    "is_team_event": edata["is_team_event"],
                    "min_team_size": edata["min_team_size"],
                    "max_team_size": edata["max_team_size"],
                    "eligibility": edata["eligibility"],
                    "rules": edata["rules"],
                    "banner_gradient": edata["banner_gradient"],
                    "is_featured": edata["is_featured"],
                    "is_published": True,
                }
            )
            created_events[edata["slug"]] = ev

        # 5. Registrations for Student
        hackathon = created_events["smart-campus-hackathon-2026"]
        workshop = created_events["genai-agentic-systems-workshop"]

        # Register Aarav (student) for Hackathon
        r1, _ = Registration.objects.get_or_create(
            event=hackathon,
            user=student_user,
            defaults={
                "status": "CONFIRMED",
                "team_name": "CodeCrafters",
                "team_members_info": "1. Aarav Sharma (Lead - Fullstack)\n2. Sneha Patil (UI/UX)\n3. Vikram Singh (IoT/Robotics)",
                "notes": "Looking forward to building the smart energy campus tracker."
            }
        )

        # Register Aarav for Workshop, and mark as checked-in so they can download Certificate!
        r2, _ = Registration.objects.get_or_create(
            event=workshop,
            user=student_user,
            defaults={
                "status": "CONFIRMED",
                "is_checked_in": True,
                "checked_in_at": now - timedelta(hours=2),
                "checked_in_by": coord_user,
                "notes": "Interested in building autonomous LLM agents."
            }
        )

        # Register Sneha for Hackathon
        Registration.objects.get_or_create(
            event=hackathon,
            user=s2,
            defaults={"status": "CONFIRMED", "team_name": "CodeCrafters"}
        )

        # Register Vikram for Hackathon and mark checked in
        Registration.objects.get_or_create(
            event=hackathon,
            user=s3,
            defaults={
                "status": "CONFIRMED",
                "team_name": "HardwareGeeks",
                "is_checked_in": True,
                "checked_in_at": now - timedelta(minutes=45),
                "checked_in_by": coord_user
            }
        )

        # 6. Event Questions & Coordinator Answers
        EventQuestion.objects.get_or_create(
            event=hackathon,
            student=student_user,
            question="Is it compulsory to bring our own laptops, or will campus lab computers be available during the hackathon?",
            defaults={
                "answer": "Hi Aarav! Yes, bringing your personal laptop is strongly recommended. We will provide power strips, Wi-Fi, and external monitors in limited quantities.",
                "answered_by": coord_user,
                "answered_at": now - timedelta(days=1),
                "is_public": True
            }
        )
        EventQuestion.objects.get_or_create(
            event=hackathon,
            student=s2,
            question="Can teams consist of students from different departments or colleges?",
            defaults={
                "answer": "Absolutely! Cross-department and inter-college collaboration is actively encouraged.",
                "answered_by": coord_user,
                "answered_at": now - timedelta(hours=18),
                "is_public": True
            }
        )
        EventQuestion.objects.get_or_create(
            event=workshop,
            student=student_user,
            question="Will we get access to API keys for OpenAI/Gemini during the workshop session?",
            defaults={
                "answer": "Yes! Temporary workshop API credits and sample sandbox environments will be provided to all attendees.",
                "answered_by": coord_user,
                "answered_at": now - timedelta(days=1),
                "is_public": True
            }
        )

        # 7. Announcements
        Announcement.objects.get_or_create(
            event=hackathon,
            title="Sponsor Update: Google Cloud & Devfolio partnering for prizes!",
            defaults={
                "content": "Exciting news! We have partnered with Google Cloud to provide $100 credits to all submitting teams, plus special category prizes for best use of Gemini AI.",
                "posted_by": coord_user,
                "is_urgent": False
            }
        )
        Announcement.objects.get_or_create(
            event=hackathon,
            title="Important: Reporting Time and Venue Check-in Instructions",
            defaults={
                "content": "Please arrive at the Auditorium Block B registration desk between 8:30 AM and 9:30 AM with your CampusConnect digital QR ticket pass ready on your phone for quick check-in.",
                "posted_by": coord_user,
                "is_urgent": True
            }
        )

        # 8. Team Finder Posts
        TeamFinderPost.objects.get_or_create(
            event=hackathon,
            user=student_user,
            title="Looking for a UI/UX Designer & Mobile Dev for Smart Campus Hackathon",
            defaults={
                "description": "We are building an intelligent campus companion app with automated timetable sync and cafeteria queue prediction. We have backend ready with Django & PostgreSQL, looking for someone skilled in Figma or Flutter/React Native.",
                "skills_offered": "Python, Django, Machine Learning, FastAPIs",
                "skills_needed": "Figma, React Native or Flutter, Tailwind",
                "contact_handle": "aarav.dev@discord / +91 91234 56789",
                "is_open": True
            }
        )
        TeamFinderPost.objects.get_or_create(
            event=hackathon,
            user=s3,
            title="Hardware & IoT Enthusiast available for Smart Campus Hackathon team",
            defaults={
                "description": "I have ESP32, Raspberry Pi, ultrasonic sensors, and solar battery packs ready. Looking to join an energetic software team aiming for the Green Campus or IoT track.",
                "skills_offered": "Embedded C, ESP32, Arduino, Circuit Design, MQTT",
                "skills_needed": "Cloud Dashboard, Web Frontend, API integration",
                "contact_handle": "vikram_iot@gmail.com",
                "is_open": True
            }
        )

        self.stdout.write(self.style.SUCCESS("Successfully seeded CampusConnect database!"))
