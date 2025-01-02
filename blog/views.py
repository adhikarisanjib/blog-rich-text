from django.db.models import Count, Prefetch
from django.contrib import messages
from django.shortcuts import render, redirect

from .models import Post, Comment
from .forms import PostForm
from .utils import create_post_slug


def post_list(request, pk=None, user_id=None):
    context = {}

    if pk:
        # post = Post.objects.select_related('user').prefetch_related(
        #     'likes', 
        #     'dislikes', 
        #     Prefetch('comments', queryset=Comment.objects.select_related('user').prefetch_related(
        #             Prefetch('replies', queryset=Comment.objects.select_related('user').prefetch_related('replies'))
        #         ).filter(parent=None).order_by('-created_at')
        # )).annotate(
        #     like_count=Count('likes'),
        #     dislike_count=Count('dislikes'),
        # ).get(pk=pk)

        post = Post.objects.select_related('user').prefetch_related(
            'likes', 
            'dislikes', 
            Prefetch('comments', queryset=Comment.objects.select_related('user') \
                    .prefetch_related('replies').annotate(reply_count=Count('replies')).filter(parent=None).order_by('-created_at')
        )).annotate(
            like_count=Count('likes'),
            dislike_count=Count('dislikes'),
        ).get(pk=pk)
        
        context['post'] = post
        return render(request, 'blog/post_detail.html', context)
    
    if user_id:
        if user_id == request.user.id:
            posts = Post.objects.select_related('user').prefetch_related('likes', 'dislikes').filter(user=request.user) \
                .annotate(like_count=Count('likes'), dislike_count=Count('dislikes')).order_by('-created_at')
        else:
            posts = Post.objects.select_related('user').prefetch_related('likes', 'dislikes').filter(user__id=user_id, status=Post.PostStatus.PUBLISHED) \
                .annotate(like_count=Count('likes'), dislike_count=Count('dislikes')).order_by('-created_at')

        context['posts'] = posts
        return render(request, 'blog/post_list.html', context)

    posts = Post.objects.select_related('user').prefetch_related('likes', 'dislikes').filter(status=Post.PostStatus.PUBLISHED) \
        .annotate(like_count=Count('likes'), dislike_count=Count('dislikes')).order_by('-created_at')
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


def post_like(request, pk=None):
    context = {}
    user = request.user

    post = Post.objects.get(pk=pk)
    if user.is_authenticated:
        post.likes.add(user)
        post.dislikes.remove(user)
    else:
        messages.error(request, 'You must be logged in to like a post.')
        context['show_message'] = True 

    post = Post.objects.select_related('user').prefetch_related('likes', 'dislikes') \
        .annotate(like_count=Count('likes'), dislike_count=Count('dislikes')).get(pk=pk)
    context['post'] = post

    return render(request, 'blog/snippets/likes.html', context)


def post_dislike(request, pk=None):
    context = {}
    user = request.user

    post = Post.objects.get(pk=pk)
    if user.is_authenticated:
        post.dislikes.add(user)
        post.likes.remove(user)
    else:
        messages.error(request, 'You must be logged in to dislike a post.')
        context['show_message'] = True

    post = Post.objects.select_related('user').prefetch_related('likes', 'dislikes') \
        .annotate(like_count=Count('likes'), dislike_count=Count('dislikes')).get(pk=pk)
    context['post'] = post
    return render(request, 'blog/snippets/likes.html', context)


def comment_create(request, post_id=None, comment_id=None):
    context = {}
    user = request.user

    if post_id and not comment_id:
        post = Post.objects.get(pk=post_id)
        if request.method == 'POST':
            content = request.POST.get('content')
            comment = Comment.objects.create(content=content, user=user, post=post)
            context['comment'] = comment
            context['post'] = post
            return render(request, 'blog/snippets/htmx/comment_snippet.html', context)
        
    return redirect('blog:post_list')


def replies_list(request, comment_id=None):
    context = {}

    if comment_id:
        replies = Comment.objects.select_related('user') \
            .prefetch_related('replies').annotate(reply_count=Count('replies')).filter(parent_id=comment_id).order_by('created_at')
        context['replies'] = replies

    return render(request, 'blog/snippets/reply.html', context)


def reply_create(request, comment_id=None):
    context = {}
    user = request.user

    if comment_id:
        comment = Comment.objects.select_related('post').get(pk=comment_id)
        if request.method == 'POST':
            content = request.POST.get('content')
            reply = Comment.objects.create(content=content, user=user, post=comment.post, parent=comment)
            comment = Comment.objects.select_related('user').prefetch_related('replies').annotate(reply_count=Count('replies')).get(pk=comment_id)
            context['reply'] = comment
            return render(request, 'blog/snippets/htmx/reply_snippet.html', context)
        
    return redirect('blog:post_list')
