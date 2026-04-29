import secrets
from django.contrib.auth.models import User
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Company


@receiver(pre_save, sender=User)
def mark_user_creation_state(sender, instance, **kwargs):
    """
    Store the first-save state before Django persists the User.
    This keeps the creation check explicit and aligned with the assignment's
    requirement to use instance._state.adding.
    """
    instance._teamboard_user_is_being_created = instance._state.adding


@receiver(post_save, sender=User)
def create_company_profile(sender, instance, created, **kwargs):
    """
    Auto-create the Company profile and API key when a User is created.
    The register view only creates the User, then updates company_name after
    this signal has generated the Company and api_key.
    """
    is_first_save = created or getattr(instance, '_teamboard_user_is_being_created', False)
    if is_first_save and not hasattr(instance, 'company'):
        Company.objects.create(
            user=instance,
            company_name=instance.email or instance.username,
            api_key=secrets.token_urlsafe(32)
        )
