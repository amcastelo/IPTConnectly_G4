from django.db import models
from django.contrib.auth.models import User


class Post(models.Model):
    TEXT = 'text'
    IMAGE = 'image'
    VIDEO = 'video'

    POST_TYPES = [
        (TEXT, 'Text'),
        (IMAGE, 'Image'),
        (VIDEO, 'Video'),
    ]

    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(User, related_name='posts', on_delete=models.CASCADE)
    post_type = models.CharField(max_length=10, choices=POST_TYPES, default=TEXT)
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict)

    def __str__(self):
        return f"Post by {self.author.username} at {self.created_at}"


class Comment(models.Model):
    text = models.TextField()
    author = models.ForeignKey(User, related_name='comments', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"Comment by {self.author.username} on Post {self.post.id}"
