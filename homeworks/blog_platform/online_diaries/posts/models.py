from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.indexes import GinIndex

User = get_user_model()


class Post(models.Model):
    topic = models.CharField(max_length=200)
    text = models.TextField()
    is_hidden = models.BooleanField(default=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.topic

    class Meta:
        indexes = [
            GinIndex(fields=["topic"], name="post_topic_gin_idx", opclasses=["gin_trgm_ops"]),
            models.Index(fields=["is_hidden", "-created_at"], name="post_visibility_created_idx"),
            models.Index(fields=["author", "-created_at"], name="post_author_created_idx"),
        ]


class PostView(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="post_views")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="post_views")
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("post", "user")

    def __str__(self):
        return f"View of {self.post.topic} by {self.user.username}"


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment on {self.post.topic}"

    class Meta:
        indexes = [
            models.Index(
                fields=["post", "-created_at"],
                name="comment_post_created_idx",
            )
        ]


class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")

    class Meta:
        unique_together = ("post", "user")

    def __str__(self):
        return f"Like on {self.post.topic} by {self.user.username}"
