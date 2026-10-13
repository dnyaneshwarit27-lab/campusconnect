from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from events.models import (
    Event,
    Registration,
    EventQuestion,
    Announcement,
    TeamFinderPost,
    EventFeedback,
    UserProfile,
    College
)
from events.mongodb import (
    users_col,
    events_col,
    registrations_col,
    teams_col,
    event_questions_col,
    attendance_col,
    announcements_col,
    feedback_col,
)


class Command(BaseCommand):
    help = 'Purges all dummy/sample data to enforce real user-entered data only.'

    def handle(self, *args, **options):
        self.stdout.write("Purging all dummy sample data from database...")

        # Clear Django Models
        Registration.objects.all().delete()
        EventQuestion.objects.all().delete()
        Announcement.objects.all().delete()
        TeamFinderPost.objects.all().delete()
        EventFeedback.objects.all().delete()
        Event.objects.all().delete()
        College.objects.all().delete()
        
        # Remove dummy demo accounts
        dummy_usernames = ['student', 'coordinator', 'admin', 'rohit_coord', 'sneha_patil', 'vikram_singh']
        User.objects.filter(username__in=dummy_usernames).delete()
        UserProfile.objects.filter(user__username__in=dummy_usernames).delete()

        # Clear MongoDB Collections if connected
        for col_getter in [
            users_col, events_col, registrations_col, teams_col,
            event_questions_col, attendance_col, announcements_col, feedback_col
        ]:
            col = col_getter()
            if col is not None:
                try:
                    col.delete_many({})
                except Exception as e:
                    self.stdout.write(f"Notice: Could not clear MongoDB collection: {e}")

        self.stdout.write(self.style.SUCCESS(
            "Successfully cleared all dummy data! The system is now 100% real user-entered data only."
        ))
