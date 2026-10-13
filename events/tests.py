import json
from datetime import timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from events.models import UserProfile, Category, College, Event, Registration


class CampusConnectTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create category & college
        self.category = Category.objects.create(name="Hackathons", slug="hackathons")
        self.college = College.objects.create(name="Apex Tech", city="Pune")

        # Create coordinator
        self.coord_user = User.objects.create_user(
            username="coordinator", password="coordpassword", first_name="Pooja", email="coord@test.com"
        )
        self.coord_profile = UserProfile.objects.create(
            user=self.coord_user, role="COORDINATOR", college="Apex Tech", is_approved=True
        )

        # Create student
        self.student_user = User.objects.create_user(
            username="student", password="studentpassword", first_name="Aarav", email="student@test.com"
        )
        self.student_profile = UserProfile.objects.create(
            user=self.student_user, role="STUDENT", college="Apex Tech", is_approved=True
        )

        # Create event
        now = timezone.now()
        self.event = Event.objects.create(
            title="National AI Hackathon 2026",
            slug="national-ai-hackathon-2026",
            category=self.category,
            college=self.college,
            coordinator=self.coord_user,
            short_description="Flagship AI competition",
            description="Build agentic systems in 36 hours.",
            venue="Auditorium Hall A",
            start_date=now + timedelta(days=3),
            end_date=now + timedelta(days=4),
            registration_deadline=now + timedelta(days=2),
            capacity=50,
            is_team_event=True,
            is_published=True
        )

    def test_home_page_status(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "National AI Hackathon 2026")

    def test_event_detail_and_qr_poster(self):
        response = self.client.get(reverse('event_detail', args=[self.event.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "National AI Hackathon 2026")
        self.assertContains(response, "data:image/png;base64,")  # QR code generated!

    def test_event_registration_and_pass(self):
        self.client.login(username="student", password="studentpassword")
        
        # Register for event
        response = self.client.post(reverse('register_event', args=[self.event.slug]), {
            'team_name': 'CodeWarriors',
            'team_members_info': 'Aarav & Team'
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        reg = Registration.objects.filter(event=self.event, user=self.student_user).first()
        self.assertIsNotNone(reg)
        self.assertEqual(reg.team_name, 'CodeWarriors')
        self.assertFalse(reg.is_checked_in)

        # View Pass
        pass_response = self.client.get(reverse('ticket_pass', args=[reg.registration_token]))
        self.assertEqual(pass_response.status_code, 200)
        self.assertContains(pass_response, "data:image/png;base64,")
        self.assertContains(pass_response, "CodeWarriors")

    def test_qr_scan_and_checkin_validation(self):
        # Create confirmed registration
        reg = Registration.objects.create(
            event=self.event,
            user=self.student_user,
            team_name='TestTeam'
        )

        self.client.login(username="coordinator", password="coordpassword")

        # 1. First Scan -> Success
        payload = json.dumps({'token': str(reg.registration_token), 'event_id': self.event.id})
        response = self.client.post(reverse('api_scan_ticket'), payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['status_code'], 'SUCCESS')

        reg.refresh_from_db()
        self.assertTrue(reg.is_checked_in)
        self.assertIsNotNone(reg.checked_in_at)

        # 2. Second Scan -> Duplicate Warning
        response_dup = self.client.post(reverse('api_scan_ticket'), payload, content_type='application/json')
        data_dup = response_dup.json()
        self.assertFalse(data_dup['success'])
        self.assertEqual(data_dup['status_code'], 'ALREADY_CHECKED_IN')

    def test_certificate_unlock(self):
        reg = Registration.objects.create(
            event=self.event,
            user=self.student_user,
            is_checked_in=False
        )

        self.client.login(username="student", password="studentpassword")

        # Before check-in: blocked / redirected
        res_before = self.client.get(reverse('certificate_view', args=[reg.registration_token]))
        self.assertEqual(res_before.status_code, 302)

        # Mark as checked-in
        reg.is_checked_in = True
        reg.save()

        # After check-in: Certificate rendered!
        res_after = self.client.get(reverse('certificate_view', args=[reg.registration_token]))
        self.assertEqual(res_after.status_code, 200)
        self.assertContains(res_after, "Certificate of Participation")
        self.assertContains(res_after, "Aarav")

    def test_mongodb_status_endpoint(self):
        res = self.client.get(reverse('mongodb_status'))
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('target_collections', data)
        self.assertEqual(len(data['target_collections']), 8)

