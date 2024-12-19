import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver


User = get_user_model()

@receiver(pre_delete, sender=User)
def user_delete(sender, instance, **kwargs):
    """
    Deleting the specific image of a Post after delete it
    """
    if instance.avatar and instance.avatar != "default/dummy_image.png":
        if os.path.isfile(instance.avatar.path):
            os.remove(instance.avatar.path)
            os.rmdir(settings.BASE_DIR / f"media/{instance.id}/avatars")


@receiver(pre_save, sender=User)
def user_update(sender, instance, **kwargs):
    """
    Replacing the specific image of a Post after update
    """

    try:
        old_avatar = sender.objects.get(id=instance.id).avatar
        new_avatar = instance.avatar
        if not (old_avatar == new_avatar or old_avatar == "default/dummy_image.png"):
            if os.path.isfile(old_avatar.path):
                os.remove(old_avatar.path)
    except Exception:
        return
    