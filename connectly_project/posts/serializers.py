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
    privacy = serializers.ChoiceField(
        choices=Post.PRIVACY_CHOICES,
        error_messages={
            "invalid_choice": "Invalid privacy setting '{input}'. Allowed values: public, private."
        }
    )

    post_type = serializers.ChoiceField(
        choices=Post.POST_TYPES,
        error_messages={
            "invalid_choice": "Invalid post type '{input}'. Allowed values: text, image, video."
        }
    )

    class Meta:
        model = Post
        fields = ['id', 'title', 'post_type', 'privacy', 'content', 'author', 'created_at', 'like_count','is_liked', 'comment_count','comments', 'metadata']

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
    
    def validate(self, attrs):
        request = self.context.get('request')
        if request and request.method == 'PATCH':
            instance = self.instance

            if 'metadata' in attrs:
                if instance and instance.metadata:
                    merged_metadata = instance.metadata.copy()
                else:
                    merged_metadata = {}
                if isinstance(attrs['metadata'], dict):
                    merged_metadata.update(attrs['metadata'])
                else:
                    raise serializers.ValidationError({
                        "metadata": "Metadata must be a dictionary."
                    })
                
                attrs['metadata'] = merged_metadata
            else:
                merged_metadata = instance.metadata if instance and instance.metadata else {}

            post_type = attrs.get('post_type', instance.post_type if instance else None)

            if post_type == 'image' and 'file_size' not in merged_metadata:
                raise serializers.ValidationError({
                    "metadata": "Image posts require 'file_size' in metadata."
                })
            if post_type == 'video' and 'duration' not in merged_metadata:
                raise serializers.ValidationError({
                    "metadata": "Video posts require 'duration' in metadata."
                })
        return attrs

    
class CommentSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Comment
        fields = ['id', 'text', 'author', 'post', 'created_at']

    def to_internal_value(self, data):

        post_id = data.get('post')

        if not Post.objects.filter(id=post_id).exists():
            raise serializers.ValidationError({"post": "Post not found."})

        return super().to_internal_value(data)

