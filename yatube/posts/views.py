from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.views.decorators.cache import cache_page
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from django.shortcuts import redirect
from django.conf import settings


def paginator(posts, request):
    """Формирует страницу с постами"""
    paginator = Paginator(posts, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


CACHE_UPDATE_FREQUENCY = 20


@cache_page(CACHE_UPDATE_FREQUENCY, key_prefix='index_page')
def index(request):
    """Главная страница"""
    template = 'posts/index.html'
    title = 'Последние обновления на сайте'
    post_list = Post.objects.select_related('author').all()
    page_obj = paginator(post_list, request)
    context = {
        'title': title,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    """Страница постов группы"""
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author').all()
    page_obj = paginator(post_list, request)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    """Страница польователя"""
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    page_obj = paginator(post_list, request)
    following = False
    if request.user.is_authenticated:
        if Follow.objects.filter(user=request.user).filter(author=author):
            following = True
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,

    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Страница поста"""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm()
    comments = post.comments.select_related('author').all()
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Создание нового поста"""
    if request.method == 'POST':
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
        )
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.author = request.user
            new_post.save()
            return redirect('posts:profile', request.user.username)
        return render(request, 'posts/create_post.html', {'form': form})
    form = PostForm()
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'post_id': post_id,
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    """Создание комментария к посту"""
    post = Post.objects.get(id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Станица подписок"""
    follows = request.user.follower.select_related('author').all()
    authors = []
    for follow in follows:
        authors.append(follow.author)
    post_list = Post.objects.filter(author__in=authors)
    page_obj = paginator(post_list, request)
    context = {
        'page_obj': page_obj,
        'title': f'Подписки пользователя {request.user}'
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Создание подписки"""
    author = get_object_or_404(User, username=username)
    if author != request.user:
        if not Follow.objects.filter(user=request.user).filter(author=author):
            Follow.objects.create(
                user=request.user,
                author=author
            )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    """Удаление подписки"""
    author = get_object_or_404(User, username=username)
    follow = get_object_or_404(Follow, author=author, user=request.user)
    follow.delete()
    return redirect('posts:profile', username=username)
