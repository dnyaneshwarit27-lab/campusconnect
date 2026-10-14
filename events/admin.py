from django.contrib import admin
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


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'college', 'department', 'year_of_study', 'is_approved')
    list_filter = ('role', 'is_approved', 'department')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email', 'college')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon', 'badge_color')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'is_partner')
    search_fields = ('name', 'city')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'event_mode', 'start_date', 'capacity', 'confirmed_registrations_count', 'checked_in_count', 'is_published', 'is_featured')
    list_filter = ('category', 'event_mode', 'is_published', 'is_featured', 'department')
    search_fields = ('title', 'short_description', 'venue', 'coordinator_name')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'registration_token', 'status', 'is_checked_in', 'checked_in_at', 'registered_at')
    list_filter = ('status', 'is_checked_in', 'event')
    search_fields = ('user__username', 'user__email', 'event__title', 'registration_token', 'team_name')
    readonly_fields = ('registration_token', 'registered_at', 'checked_in_at')


@admin.register(EventQuestion)
class EventQuestionAdmin(admin.ModelAdmin):
    list_display = ('event', 'student', 'question', 'answered_by', 'created_at', 'is_public')
    list_filter = ('is_public', 'event')
    search_fields = ('question', 'answer', 'student__username', 'event__title')


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'event', 'posted_by', 'is_urgent', 'created_at')
    list_filter = ('is_urgent', 'event')
    search_fields = ('title', 'content', 'event__title')


@admin.register(TeamFinderPost)
class TeamFinderPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'event', 'skills_needed', 'is_open', 'created_at')
    list_filter = ('is_open', 'event')
    search_fields = ('title', 'description', 'skills_needed', 'user__username')


@admin.register(EventFeedback)
class EventFeedbackAdmin(admin.ModelAdmin):
    list_display = ('registration', 'rating', 'created_at')
    list_filter = ('rating',)


@admin.register(TeamCollaborationRequest)
class TeamCollaborationRequestAdmin(admin.ModelAdmin):
    list_display = ('post', 'sender', 'sender_contact', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('post__title', 'sender__username', 'sender_contact', 'message')


@admin.register(EventCoordinatorTeam)
class EventCoordinatorTeamAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'role', 'status', 'joined_at')
    list_filter = ('role', 'status', 'event')
    search_fields = ('event__title', 'user__username', 'user__email', 'custom_role', 'pitch_note')


