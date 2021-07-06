from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Comment, Follow
from yatube.settings import PER_PAGE


@cache_page(20)
def index(request):
    post_list = Post.objects.select_related('group').all()
    paginator = Paginator(post_list, PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group)
    paginator = Paginator(posts, PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'group.html', {'group': group, 'page': page})


def profile(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    paginator = Paginator(posts, PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    count = paginator.count
    if request.user.is_authenticated:
        following = Follow.objects.filter(user=user, author=author).exists()
    else:
        following = False
    followers = Follow.objects.filter(author=author).count()
    followings = Follow.objects.filter(user=author).count()
    return render(
        request, 'profile.html', {
            'author': author,
            'page': page,
            'count': count,
            'following': following,
            'followings': followings,
            'followers': followers
        }
    )


def post_view(request, username, post_id):
    post = get_object_or_404(Post.objects.select_related('author'),
                             id=post_id, author__username=username)
    count = Post.objects.select_related('author').filter(
        author__username=username).count()
    author = post.author
    form = CommentForm()
    comments = Comment.objects.select_related('post').filter(post__id=post_id)
    followers = Follow.objects.filter(author=author).count()
    followings = Follow.objects.filter(user=author).count()
    return render(
        request, 'post.html', {
            'post': post,
            'count': count,
            'author': author,
            'comments': comments,
            'form': form,
            'followings': followings,
            'followers': followers
        }
    )


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('index')
    return render(request, 'newpost.html', {'form': form})


@login_required
def post_edit(request, username, post_id):
    if request.user.username != username:
        return redirect('post', username=username, post_id=post_id)
    post = get_object_or_404(Post.objects.select_related('author'),
                             id=post_id, author__username=username)
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )
    if form.is_valid():
        post = form.save()
        return redirect('post', username=username, post_id=post_id)
    return render(request, 'postedit.html', {'form': form, 'post': post})


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    post = Post.objects.select_related('author').get(
        id=post_id, author__username=username
    )
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('post', username=username, post_id=post_id)
    comments = Comment.objects.select_related('post').filter(post__id=post_id)
    return render(request, 'post.html',
                  {'post': post, 'comments': comments, 'form': form})


@login_required
def follow_index(request):
    user = request.user
    posts = Post.objects.filter(author__following__user=user)
    paginator = Paginator(posts, PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'follow.html', {'page': page})


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if user != author:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect('profile', username)


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=user, author=author).delete()
    return redirect('profile', username)
