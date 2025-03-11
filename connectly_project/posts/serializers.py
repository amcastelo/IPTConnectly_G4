from rest_framework import serializers
from .models import User, Post, Comment
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','username', 'email']  # Exclude sensitive fields like password



class PostSerializer(serializers.ModelSerializer):
    comments = serializers.StringRelatedField(many=True, read_only=True)
    author = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'title', 'post_type', 'content', 'author', 'created_at', 'like_count','is_liked', 'comment_count','comments']

    def validate_author(self, value):
        if not User.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Author not found.")
        return value
    
    def get_author(self, obj):
        return {"id": obj.author.id, "username": obj.author.username}
    
    def get_like_count(self, obj):
        return obj.likes.count()
    
    def get_is_liked(self, obj):

        user = self.context['request'].user
        if user.is_authenticated:
            return obj.likes.filter(user=user).exists()
        return False
    
    def get_comment_count(self, obj):
        return obj.comments.count()  
    
class CommentSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Comment
        fields = ['id', 'text', 'author', 'post', 'created_at']

    def to_internal_value(self, data):

        post_id = data.get('post')

        if not Post.objects.filter(id=post_id).exists():
            raise serializers.ValidationError({"post": "Post not found."})

        return super().to_internal_value(data)

