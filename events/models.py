import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('STUDENT', 'Student'),
        ('COORDINATOR', 'Event Coordinator'),
        ('ADMIN', 'Campus Administrator'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STUDENT')
    college = models.CharField(max_length=200, default='Apex Institute of Technology')
    department = models.CharField(max_length=150, default='Computer Science & Engineering')
    year_of_study = models.CharField(max_length=50, blank=True, default='3rd Year')
    phone = models.CharField(max_length=30, blank=True)
    skills = models.CharField(max_length=300, blank=True, help_text="e.g. Python, React, UI/UX, Cloud, ML")
    bio = models.TextField(blank=True)
    avatar_color = models.CharField(max_length=30, default='#4f46e5')
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"

    @property
    def is_student(self):
        return self.role == 'STUDENT'

    @property
    def is_coordinator(self):
        return self.role in ['COORDINATOR', 'ADMIN']

    @property
    def is_admin(self):
        return self.role == 'ADMIN' or self.user.is_superuser


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    icon = models.CharField(max_length=60, default='bi-lightning-charge', help_text="Bootstrap icon class")
    badge_color = models.CharField(max_length=40, default='#4f46e5')
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class College(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100, default='Metro Campus')
    is_partner = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Event(models.Model):
    MODE_CHOICES = [
        ('OFFLINE', 'In-Person / On Campus'),
        ('ONLINE', 'Online / Virtual'),
        ('HYBRID', 'Hybrid'),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='events')
    college = models.ForeignKey(College, on_delete=models.SET_NULL, null=True, blank=True)
    college_name = models.CharField(max_length=200, default='Apex Institute of Technology')
    department = models.CharField(max_length=150, default='Computer Science & Engineering')
    coordinator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coordinated_events')
    coordinator_name = models.CharField(max_length=120, blank=True)
    coordinator_email = models.EmailField(blank=True)
    coordinator_phone = models.CharField(max_length=30, blank=True)
    
    short_description = models.CharField(max_length=350)
    description = models.TextField(help_text="Detailed overview, agenda, perks, criteria")
    event_mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='OFFLINE')
    venue = models.CharField(max_length=255, default='Tech Auditorium, Block C')
    
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    registration_deadline = models.DateTimeField()
    
    capacity = models.PositiveIntegerField(default=100)
    registration_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    prize_pool = models.CharField(max_length=200, blank=True, default='₹50,000 + Merit Certificates')
    
    is_team_event = models.BooleanField(default=False)
    min_team_size = models.PositiveIntegerField(default=1)
    max_team_size = models.PositiveIntegerField(default=4)
    eligibility = models.CharField(max_length=255, default='All registered College & University Students')
    rules = models.TextField(blank=True, default='1. Valid college ID is required.\n2. Respect code of conduct.\n3. Bring your own laptops for coding/hackathon events.')
    
    banner_url = models.CharField(max_length=500, blank=True)
    banner_gradient = models.CharField(max_length=200, default='linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)')
    
    is_published = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_date']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Event.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        if not self.coordinator_name and self.coordinator:
            self.coordinator_name = self.coordinator.get_full_name() or self.coordinator.username
        if not self.coordinator_email and self.coordinator:
            self.coordinator_email = self.coordinator.email
        super().save(*args, **kwargs)

    @property
    def confirmed_registrations_count(self):
        return self.registrations.filter(status='CONFIRMED').count()

    @property
    def checked_in_count(self):
        return self.registrations.filter(status='CONFIRMED', is_checked_in=True).count()

    @property
    def seats_left(self):
        left = self.capacity - self.confirmed_registrations_count
        return max(left, 0)

    @property
    def is_registration_open(self):
        now = timezone.now()
        return now <= self.registration_deadline and self.seats_left > 0

    @property
    def is_past(self):
        return timezone.now() > self.end_date

    @property
    def is_ongoing(self):
        now = timezone.now()
        return self.start_date <= now <= self.end_date

    @property
    def checkin_percentage(self):
        total = self.confirmed_registrations_count
        if total == 0:
            return 0
        return round((self.checked_in_count / total) * 100)


class Registration(models.Model):
    STATUS_CHOICES = [
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registrations')
    registration_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CONFIRMED')
    
    is_checked_in = models.BooleanField(default=False)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    checked_in_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='checked_in_attendees')
    
    team_name = models.CharField(max_length=150, blank=True)
    team_members_info = models.TextField(blank=True, help_text="Roster of team member names & emails")
    notes = models.TextField(blank=True)
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event', 'user')
        ordering = ['-registered_at']

    def __str__(self):
        return f"{self.user.username} -> {self.event.title} ({self.status})"

    @property
    def pass_token_short(self):
        return str(self.registration_token).replace('-', '')[:10].upper()


class EventQuestion(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='questions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='asked_questions')
    question = models.TextField()
    answer = models.TextField(blank=True)
    answered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='answered_questions')
    created_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(null=True, blank=True)
    is_public = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Q for {self.event.title} by {self.student.username}"


class Announcement(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(max_length=255)
    content = models.TextField()
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    is_urgent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.event.title}] {self.title}"


class TeamFinderPost(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True, related_name='team_requests')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_posts')
    title = models.CharField(max_length=255)
    description = models.TextField()
    skills_offered = models.CharField(max_length=255, help_text="Skills you bring, e.g. Backend, UI/UX")
    skills_needed = models.CharField(max_length=255, help_text="Skills you are looking for")
    contact_handle = models.CharField(max_length=150, help_text="Discord / WhatsApp / Email")
    is_open = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} by {self.user.username}"


class EventFeedback(models.Model):
    registration = models.OneToOneField(Registration, on_delete=models.CASCADE, related_name='feedback')
    rating = models.PositiveSmallIntegerField(default=5)  # 1 to 5
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback {self.rating}* by {self.registration.user.username} for {self.registration.event.title}"


class TeamCollaborationRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('DECLINED', 'Declined'),
    ]
    post = models.ForeignKey(TeamFinderPost, on_delete=models.CASCADE, related_name='collaboration_requests')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_collaboration_requests')
    message = models.TextField()
    sender_contact = models.CharField(max_length=150, help_text="Email, Phone, Discord or Telegram")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Collab Request from {self.sender.username} on '{self.post.title}'"

