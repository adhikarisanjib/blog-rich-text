from django.urls import path

from .views import (
    post_list, 
    post_create, 
    post_update, 
    post_publish, 
    post_delete
)


app_name = 'blog'

urlpatterns = [
    path('', post_list, name='post_list'),
    path('posts/user/<int:user_id>/', post_list, name='post_list_of_user'), # update to uuid type after custom user model
    path('post/<uuid:pk>/', post_list, name='post_detail'),
    path('post/create/', post_create, name='post_create'),
    path('post/update/<uuid:pk>/', post_update, name='post_update'),
    path('post/publish/<uuid:pk>/', post_publish, name='post_publish'),
    path('post/delete/<uuid:pk>/', post_delete, name='post_delete'),

    path('login/', post_list, name='login'),
    path('logout/', post_list, name='logout'),
    path('register/', post_list, name='register'),
    path('profile/', post_list, name='profile'),
]
