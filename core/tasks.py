from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import Token, User
from .tokens import account_activation_token, password_reset_token


def get_user_by_id(id):
    try:
        user = User.objects.get(id=id)
    except User.DoesNotExist:
        user = None
    return user


def get_user_by_email(email):
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        user = None
    return user


@shared_task()
def send_user_activation_email(user_id, domain):
    user = get_user_by_id(id=user_id)
    token = account_activation_token.make_token(user)
    Token.objects.create(user=user, token=token)
    try:
        subject = "Activate your account."
        message = render_to_string(
            "email/account_activation_email.html",
            {
                "user": user,
                "domain": domain,
                "uid": urlsafe_base64_encode(force_bytes(user.id)),
                "token": token,
            },
        )
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )
    except Exception as e:
        print(e)


@shared_task()
def send_password_reset_email(email, domain):
    user = get_user_by_email(email=email)
    token = password_reset_token.make_token(user)
    Token.objects.create(user=user, token=token)
    try:
        subject = "Reset your password."
        message = render_to_string(
            "email/password_reset_email.html",
            {
                "user": user,
                "domain": domain,
                "uid": urlsafe_base64_encode(force_bytes(user.id)),
                "token": password_reset_token.make_token(user),
            },
        )
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )
    except Exception as e:
        print(e)


@shared_task(bind=True)
def remove_expired_tokens(self, message):
    tokens = Token.objects.all()
    for token in tokens:
        if token.is_expired:
            token.delete()
    print(message)
