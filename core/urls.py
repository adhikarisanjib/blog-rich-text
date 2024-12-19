from django.urls import path

from .views import (
    register_view,
    email_verify_view, 
    login_view, 
    logout_view, 
    profile_view, 
    update_profile_view, 
    deactivate_account_view,
    delete_account_view,
    password_change_view, 
    password_reset_request_view, 
    password_reset_view,
    search_account_view,
)

app_name = 'core'


urlpatterns = [
    path('register/', register_view, name='register'),
    path('email-verify/<uidb64>/<token>/', email_verify_view, name='email-verify'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('profile/<uuid:user_id>/', profile_view, name='profile'),
    path('update-profile/', update_profile_view, name='update-profile'),
    path('deactivate-account/', deactivate_account_view, name='deactivate-account'),
    path('delete-account/', delete_account_view, name='delete-account'),
    path('password-change/', password_change_view, name='password-change'),
    path('password-reset-request/', password_reset_request_view, name='password-reset-request'),
    path('password-reset/<uidb>/<token>/', password_reset_view, name='password-reset'),
    path('search-account/', search_account_view, name='search-account'),
]
