"""
Signal handlers.

A signal is Django's pub/sub system: "when X happens, call this function".
We use one signal here whenever a new User row is created, automatically
make a matching UserDetail row and a default Free Subscription.

This matters because Users can be created from a bunch of different
places: the signup form, Google or GitHub OAuth, admin-created accounts.
The signal catches them all so we don't have to remember to create the
profile row in each place separately.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

from .models import UserDetail, Subscription


@receiver(post_save, sender=User)
def create_user_detail(sender, instance, created, **kwargs):
    """Whenever a brand-new User is saved, set them up with a profile + plan."""
    if created:
        UserDetail.objects.get_or_create(
            user=instance,
            defaults={
                'firstname': instance.first_name or '',
                'surname': instance.last_name or '',
            },
        )
        Subscription.objects.get_or_create(
            owner=instance,
            defaults={
                'name': f"{instance.username}'s workspace",
                'plan_type': 'free',
                'is_active': True,
            },
        )
