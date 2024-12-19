import datetime
import uuid

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


def get_user_avatar(user, filename):
    return f"{user.id}/avatars/{filename}"


def get_default_avatar():
    return "default/dummy_image.png"


def get_default_email_verified_value():
    if settings.DEBUG:
        return True
    return False


class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None):
        if not email:
            raise ValueError("User must have an email address.")
        if not name:
            raise ValueError("User must have a name.")
        user = self.model(
            email=self.normalize_email(email=email),
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None):
        user = self.create_user(
            email=email,
            name=name,
            password=password,
        )
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.is_email_verified = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(
        verbose_name=_("ID"),
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    email = models.EmailField(
        verbose_name=_("Email"),
        max_length=127,
        unique=True,
        error_messages={
            "null": _("Email field is required."),
            "unique": _("An account with that email already exists. Please login to continue."),
            "invalid": _("Enter a valid email address."),
        },
    )
    name = models.CharField(
        verbose_name=_("Full Name"),
        max_length=255,
        null=True,
        blank=True,
    )
    avatar = models.ImageField(
        verbose_name=_("Avatar"),
        blank=True,
        null=True,
        default=get_default_avatar,
        upload_to=get_user_avatar,
    )
    contact_number = models.CharField(
        verbose_name=_("Contact Number"),
        validators=[RegexValidator(r"^(?:\+977|\+91)[\s_]?(\d{10})$")],
        max_length=15,
        null=True,
        blank=True,
        help_text=_("In format: CountryCode PhoneNumber (+977 9812345678)"),
    )
    is_email_verified = models.BooleanField(
        verbose_name=_("Email Verification Status"),
        default=get_default_email_verified_value,
        help_text=_("Designates whether this user is verified or not."),
    )
    is_active = models.BooleanField(
        verbose_name=_("Active Status"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active."
            "Unselect this field instead of deleting accounts."
        ),
    )
    is_staff = models.BooleanField(
        verbose_name=_("Staff Status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    date_joined = models.DateTimeField(
        verbose_name=_("Date Joined"),
        auto_now_add=True,
        editable=False,
    )

    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ("-date_joined",)

    def __str__(self):
        return self.email


class Token(models.Model):
    id = models.UUIDField(
        verbose_name=_("ID"),
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        editable=False,
    )
    token = models.CharField(
        verbose_name=_("Token"),
        max_length=256,
        editable=False,
    )
    created_at = models.DateTimeField(
        verbose_name=_("Date Created"),
        auto_now_add=True,
        editable=False,
    )

    def __str__(self):
        return self.user.name

    @property
    def is_expired(self):
        return self.created_at.replace(tzinfo=datetime.timezone.utc) + datetime.timedelta(
            minutes=5,
        ) < datetime.datetime.now(datetime.timezone.utc)
