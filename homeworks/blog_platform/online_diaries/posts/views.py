from django.db.models.query import Prefetch
from cmath import log
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import CommentForm, PostForm
from .models import Like, Post, PostView, Comment

User = get_user_model()

SORT_OPTIONS = {
    "created_at": "-created_at",
    "views": "-views_count",
}


def post_detail(request, post_id):
    post_with_comments = (
        Post.objects
        .annotate(views_count=Count("post_views"))
        .annotate(likes_count=Count("likes"))
        .select_related("author")
        .get(pk=post_id)
    )

    comments_qs = Comment.objects.filter(post_id=post_id).select_related("author").order_by("created_at")

    paginator = Paginator(comments_qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    if request.user.is_authenticated:
        post_view, created = PostView.objects.get_or_create(post=post_with_comments, user=request.user)
        if created:
            post_with_comments.refresh_from_db()

    if request.method != "POST":
        form = CommentForm()
        context = {"post": post_with_comments, "form": form, "page_obj": page_obj}
        return render(request, "posts/post_detail.html", context)

    form = CommentForm(request.POST)

    if not form.is_valid():
        return render(request, "posts:post_detail.html", {"form": form})

    new_comment = form.save(commit=False)
    new_comment.author = request.user
    new_comment.post = post_with_comments
    form.save()
    return redirect("posts:post_detail", post_id=post_id)


@login_required
def post_create(request):
    if request.method != "POST":
        form = PostForm()
        return render(request, "posts/post_create.html", {"form": form})
    form = PostForm(request.POST)
    if not form.is_valid():
        return render(request, "posts/post_create.html", {"form": form})
    new_post = form.save(commit=False)
    new_post.author = request.user
    form.save()
    return redirect("posts:posts_list")


def posts_list(request):
    sort_by = request.GET.get("sort")
    search_box = request.GET.get("search_box")
    top_posts_period = request.GET.get("period")

    posts = Post.objects.filter(is_hidden=False).annotate(views_count=Count("post_views"))

    today = timezone.now()

    if top_posts_period:
        match top_posts_period:
            case "day":
                posts = posts.filter(created_at__date=today.date())
            case "month":
                posts = posts.filter(created_at__month=today.month, created_at__year=today.year)
            case "year":
                posts = posts.filter(created_at__year=today.year)
            case "hour":
                posts = posts.filter(created_at__gte=today - timedelta(hours=1))

        posts = posts.order_by("-views_count")

    if sort_by and not top_posts_period:
        posts = posts.order_by(SORT_OPTIONS.get(sort_by, "-created_at"))

    if search_box:
        posts = posts.filter(topic__icontains=search_box)

    return render(request, "posts/posts_list.html", {"posts": posts, "current_sort": sort_by})


@login_required
@require_POST
def toggle_post_visibility(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect("posts:post_detail", post_id=post_id)

    post.is_hidden = not post.is_hidden
    post.save()
    return redirect("posts:post_detail", post_id=post_id)


@login_required
def toggle_like(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)

    if not created:
        like.delete()

    return redirect("posts:post_detail", post_id=post_id)
