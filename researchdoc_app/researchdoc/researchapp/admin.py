"""
Django admin configuration.

Django ships with a built-in admin panel that auto-generates pages for
every model you register. This file is where we customise how each one
looks which columns appear in the list, what filters and search
fields are available, and the bulk actions you can run from the list.

The interesting one is SubscriptionAdmin it disables the delete
button and replaces it with an "archive" action (flips is_active
instead of dropping the row). That matches how real billing systems
behave: you almost never hard-delete a subscription, you mark it
cancelled and keep the record for audit.
"""
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    UserDetail, Subscription,
    ResearchProject, Resource, ResearchSummary, Citation,
    ComparisonTable, ComparisonColumn, ComparisonRow, ComparisonCell,
)



# Extend the built-in User admin to show UserDetail + Subscription inline
class UserDetailInline(admin.StackedInline):
    """Show UserDetail fields inside the User edit page."""
    model = UserDetail
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class SubscriptionInline(admin.TabularInline):
    """Show the user's Subscriptions on their User edit page."""
    model = Subscription
    extra = 0
    fields = ('name', 'plan_type', 'is_active', 'created_at')
    readonly_fields = ('created_at',)


# Unregister Django's default User admin so we can replace it
admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """Replaces Django's built-in User admin so we can show profile + plan inline.

    Everything Django's default admin gives you still works (change
    password, deactivate, search) we're just adding the UserDetail
    fields and a Subscription tab next to it.
    """
    inlines = (UserDetailInline, SubscriptionInline)
    list_display = (
        'username', 'email', 'first_name', 'last_name',
        'is_active', 'is_staff', 'date_joined',
    )
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_per_page = 20
    actions = ['deactivate_users', 'activate_users']

    @admin.action(description='Deactivate selected users (cannot login)')
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} user(s) deactivated.", messages.SUCCESS)

    @admin.action(description='Activate selected users')
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} user(s) activated.", messages.SUCCESS)
