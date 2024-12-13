import uuid

from django.shortcuts import render, redirect

from .models import Post
from .forms import PostForm
from .utils import create_post_slug


def post_list(request, pk=None, user_id=None):
    context = {}

    if pk:
        post = Post.objects.select_related('user').get(pk=pk)
        context['post'] = post
        return render(request, 'blog/post_detail.html', context)
    
    if user_id:
        if user_id == request.user.id:
            posts = Post.objects.select_related('user').filter(user=request.user)
        else:
            posts = Post.objects.select_related('user').filter(user__id=user_id, status=Post.PostStatus.PUBLISHED)

        context['posts'] = posts
        return render(request, 'blog/post_list.html', context)

    posts = Post.objects.select_related('user').filter(status=Post.PostStatus.PUBLISHED)
    context['posts'] = posts
    return render(request, 'blog/post_list.html', context)
    

def post_create(request):
    context = {}
    user = request.user

    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            slug = create_post_slug(post.title)
            post.slug = slug
            post.user = user
            post.save()
            return redirect('blog:post_list')
        
    else:
        form = PostForm()

    context['form'] = form
    return render(request, 'blog/post_create.html', context)


def post_update(request, pk=None):
    context = {}
    user = request.user

    post = Post.objects.select_related().get(pk=pk)
    if post.user != user:
        return redirect('blog:post_list')

    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            return redirect('blog:post_list')
        
    else:
        form = PostForm(instance=post)

    context['form'] = form
    return render(request, 'blog/post_update.html', context)


def post_publish(request, pk=None):
    user = request.user

    post = Post.objects.select_related().get(pk=pk)
    if post.user != user:
        return redirect('blog:post_list')

    post.status = Post.PostStatus.PUBLISHED
    post.save()
    return redirect('blog:post_list')


def post_delete(request, pk=None):
    user = request.user

    post = Post.objects.select_related().get(pk=pk)
    if post.user != user:
        return redirect('blog:post_list')

    post.delete()
    return redirect('blog:post_list')