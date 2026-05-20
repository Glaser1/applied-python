from django.contrib import admin
from .models import Post, Comment


class PostAdmin(admin.ModelAdmin):
    list_display = ("pk", "topic", "text", "author", "is_hidden", "likes_count", "created_at")
    list_editable = ("author", "is_hidden")
    search_fields = ("topic",)
    empty_value_display = "-пусто-"

    def likes_count(self, obj):
        return len(obj.likes.all())

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).prefetch_related("likes")


class CommentAdmin(admin.ModelAdmin):
    list_display = ("pk", "post", "text", "author", "created_at")
    list_editable = ("author",)
    search_fields = ("text",)
    empty_value_display = "-пусто-"


admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
