from dotenv.cli import get
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.query import Prefetch
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView
from posts.models import Comment, Post

from .forms import UserCreationForm

User = get_user_model()


class SignUp(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy("posts:posts_list")
    template_name = "users/signup.html"


class UserDetailView(DetailView):
    model = User
    template_name = "users/profile.html"

    def get_object(self, queryset=None):
        user = get_object_or_404(
            User.objects.prefetch_related(
                Prefetch("posts", queryset=Post.objects.order_by("-created_at")),
                Prefetch("comments", queryset=Comment.objects.select_related("post").order_by("-created_at")),
            ),
            username=self.kwargs["username"],
        )
        return user


class EditProfileView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ("first_name", "last_name", "username")
    template_name = "users/signup.html"
    success_url = reverse_lazy("posts:posts_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "edit_profile"
        return context

    def get_object(self, queryset=None):
        return self.request.user
