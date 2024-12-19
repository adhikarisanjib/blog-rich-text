from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

from .forms import (
    LoginForm,
    PasswordChangeForm,
    PasswordResetForm,
    PasswordResetRequestForm,
    RegistrationForm,
    UserUpdateForm,
)
from .models import Token, User
from .tasks import send_password_reset_email, send_user_activation_email
from .tokens import account_activation_token, password_reset_token
from .utils import pagination_helper


def check_token_is_valid(token, user):
    try:
        token_instance = Token.objects.filter(token=token).first()
        if not token_instance.is_expired and token_instance.user == user:
            return True
        else:
            return False
    except Token.DoesNotExist:
        return False


def register_view(request, *args, **kwargs):
    context = {}

    user = request.user
    if user.is_authenticated:
        messages.info(request, "You are already registered.")
        return redirect("blog:post_list")

    form = RegistrationForm(request.POST or None, request.FILES or None)

    if request.method == "POST":
        if form.is_valid():
            user = form.save()

            site = get_current_site(request)
            domain = site.domain
            if settings.CELERY_SERVER_RUNNING:
                send_user_activation_email.delay(user.id, domain)
            else:
                send_user_activation_email(user.id, domain)
            messages.success(
                request,
                f"An email with verification link is sent to your Email ID. Verify Your account before login.",
            )

            return redirect("core:login")

        else:
            messages.error(request, f"Error in data validation.")

    context["form"] = form
    return render(request, "core/register.html", context)


def login_view(request, *args, **kwargs):
    context = {}

    form = LoginForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            email = request.POST["email"]
            password = request.POST["password"]
            user = authenticate(request, email=email, password=password)

            if not user.is_active:
                user.is_active = True

            if not user.is_email_verified:
                site = get_current_site(request)
                domain = site.domain
                if settings.CELERY_SERVER_RUNNING:
                    send_user_activation_email.delay(user.id, domain)
                else:
                    send_user_activation_email(user.id, domain)
                messages.success(
                    request,
                    f"An email with verification link is sent to your Email ID. Verify Your account before login.",
                )
                return redirect("blog:post_list")

            login(request, user)
            messages.success(request, "Login Successfull.")
            redirect_url = request.GET.get("next", None)
            if redirect_url:
                return redirect(redirect_url)
            return redirect("blog:post_list")
        
        else:
            messages.error(request, f"Invalid email or password.")

    context["form"] = form
    return render(request, "core/login.html", context)


def logout_view(request, *args, **kwargs):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("core:login")


@login_required()
def profile_view(request, *args, **kwargs):
    context = {}

    user_id = kwargs.get("user_id", None)
    if user_id:
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise Http404("User not found.")
    else:
        user = request.user

    context["user"] = user
    return render(request, "core/profile.html", context)


@login_required()
def update_profile_view(request, *args, **kwargs):
    context = {}

    user = request.user
    if request.method == "GET":
        form = UserUpdateForm(instance=user)

    if request.method == "POST":
        form = UserUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            # Verify new email in case user changed their email.
            if not user.is_email_verified:
                messages.info(request, "Since you changed your email you need to verify it. Please login to verify.")
                return redirect("core:logout")
            messages.success(request, "Profile update successful.")
            return redirect("core:profile")
        else:
            messages.error(request, f"Error...")

    context["form"] = form
    return render(request, "core/profile_update.html", context)


@login_required()
def deactivate_account_view(request, *args, **kwargs):
    user = request.user

    try:
        user.is_active = False
        user.save()
        logout(request)
        messages.success(request, f"Your account has been deactivated. Login anytime to reactivate it.")
    except:
        messages.error(request, "Something went wrong.")

    return redirect("blog:post_list")


@login_required()
def delete_account_view(request, *args, **kwargs):
    user = request.user

    try:
        user.delete()
        messages.success(request, f"Your account has been deleted successfully.")
    except:
        messages.error(request, "Something went wrong.")
        
    return redirect("blog:post_list")


def search_account_view(request, *args, **kwargs):
    context = {}
    users = None
    pagination = None
    search_text = request.GET.get("q", None)

    if request.method == "GET":
        if search_text:
            users = User.objects.filter(Q(email__icontains=search_text) | Q(name__icontains=search_text))
        else:
            users = User.objects.all()

        if request.user.is_authenticated:
            users = users.exclude(id=request.user.id)

        if users.count() > 100:
            page = request.GET.get("page", 1)
            users = pagination_helper(users, page, 50)
            pagination = True

    context["search"] = search_text
    context["pagination"] = pagination
    context["users"] = users
    return render(request, "core/search_user.html", context)


def email_verify_view(request, uidb64, token, *args, **kwargs):
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(id=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    token_valid = check_token_is_valid(token=token, user=user)
    if not token_valid:
        messages.error(
            request,
            "Either the link is invalid or it is expired. Please proceed to login page and try logging in to get new link.",
        )
        return redirect("blog:post_list")

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.is_email_verified = True
        user.save()
        login(request, user)
        messages.success(request, f"An account for {user.name} created successfully.")
        return redirect("blog:post_list")
    else:
        messages.error(request, f"Something went wrong.")
        return redirect("blog:post_list")


@login_required()
def password_change_view(request, *args, **kwargs):
    context = {}

    user = request.user
    form = PasswordChangeForm(user, request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Password changed successfully. Please login with new password to continue.",
            )
            return redirect("core:logout")
        else:
            messages.error(request, "Error.")

    context["form"] = form
    context["header"] = "Change Password"
    context["button_text"] = "change"
    return render(request, "core/password/password_form.html", context)


def password_reset_request_view(request, *args, **kwargs):
    context = {}

    form = PasswordResetRequestForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            email = request.POST["email"]

            site = get_current_site(request)
            domain = site.domain
            if settings.CELERY_SERVER_RUNNING:
                send_password_reset_email.delay(email, domain)
            else:
                send_password_reset_email(email, domain)
            messages.success(
                request,
                f"An email with password reset link is sent to your Email ID. Verify Your account before login.",
            )

        else:
            messages.error(request, "Error.")

    context["form"] = form
    context["header"] = "Request Password Reset"
    context["button_text"] = "request"
    return render(request, "core/password/password_form.html", context)


def password_reset_view(request, uidb64, token, *args, **kwargs):
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(id=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    context = {}

    token_valid = check_token_is_valid(token=token, user=user)
    if not token_valid:
        messages.error(
            request,
            "Either the link is invalid or it is expired. Please request password reset again.",
        )
        return redirect("blog:post_list")

    if user is not None and password_reset_token.check_token(user, token):
        form = PasswordResetForm(user, request.POST or None)

        if request.method == "POST":
            if form.is_valid():
                form.save()
                messages.success(
                    request,
                    f"Your password has been reset. Please login to continue.",
                )
                return redirect("core:login")
            else:
                messages.error(request, "Error.")

        context["form"] = form
        context["header"] = "Request Password Reset"
        context["button_text"] = "change"
        return render(request, "core/password/password_form.html", context)
    else:
        messages.info(request, f"Something went wrong.")
        return redirect("blog:post_list")


def page_not_found_view(request, exception=None, *args, **kwargs):
    messages.error(request, "Page Not Found.")
    return render(request, "core/page_not_found.html")


def permission_denied_view(request, exception=None, *args, **kwargs):
    if isinstance(exception, PermissionDenied):
        messages.error(request, "You do not have permission to access this page.")
    return render(request, "core/permission_denied.html")