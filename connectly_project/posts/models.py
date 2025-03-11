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

    def like_count(self):
        return self.likes.count()
    
    def __str__(self):
        return f"Post by {self.author.username} at {self.created_at}"
    
    def comment_count(self):
        return self.comments.count()


class Comment(models.Model):
    text = models.TextField()
    author = models.ForeignKey(User, related_name='comments', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"Comment by {self.author.username} on Post {self.post.id}"

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    is_liked = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')

    def __str__(self):
        return f"{self.user.username} {'liked' if self.is_liked else 'unliked'} {self.post.title}"
