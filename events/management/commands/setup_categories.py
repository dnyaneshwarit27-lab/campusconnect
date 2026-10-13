from django.core.management.base import BaseCommand
from events.models import Category


class Command(BaseCommand):
    help = 'Ensures standard event taxonomy categories exist for coordinators to choose from.'

    def handle(self, *args, **options):
        categories_data = [
            {"name": "Hackathons", "slug": "hackathons", "icon": "bi-code-slash", "badge_color": "#6366f1"},
            {"name": "AI & Tech Workshops", "slug": "workshops", "icon": "bi-cpu", "badge_color": "#8b5cf6"},
            {"name": "Coding Competitions", "slug": "coding", "icon": "bi-terminal", "badge_color": "#ec4899"},
            {"name": "Project Exhibitions", "slug": "exhibitions", "icon": "bi-display", "badge_color": "#06b6d4"},
            {"name": "Cultural & Tech Fests", "slug": "fests", "icon": "bi-stars", "badge_color": "#f59e0b"},
            {"name": "Robotics & Hardware", "slug": "robotics", "icon": "bi-robot", "badge_color": "#10b981"},
        ]
        created_count = 0
        for cat in categories_data:
            _, created = Category.objects.get_or_create(
                slug=cat["slug"],
                defaults={
                    "name": cat["name"],
                    "icon": cat["icon"],
                    "badge_color": cat["badge_color"],
                }
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Standard event categories verified ({created_count} new initialized)."))
