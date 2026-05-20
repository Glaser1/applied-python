from django.urls import path
from . import views

app_name = "posts"

urlpatterns = [
    path("posts/<int:post_id>/", views.post_detail, name="post_detail"),
    path("create/", views.post_create, name="post_create"),
    path("posts/", views.posts_list, name="posts_list"),
    path("toggle_post_visibility/<int:post_id>/", views.toggle_post_visibility, name="toggle_post_visibility"),
    path("toggle_like/<int:post_id>/", views.toggle_like, name="toggle_like"),
]
