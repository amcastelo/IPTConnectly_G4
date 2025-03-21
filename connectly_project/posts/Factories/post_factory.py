from posts.models import Post
from django.contrib.auth.models import User
from posts.Singleton.config_manager import ConfigManager

class PostFactory:
    @staticmethod
    def create_post(post_type, title, content='', metadata=None, author=None, privacy='public'):

        titleConfig = ConfigManager()
        titleConfig.set_setting("Default_Title", "Default title")

        if post_type not in dict(Post.POST_TYPES):
            raise ValueError(f"Invalid post type: '{post_type}'. Allowed values: {', '.join([choice[0] for choice in Post.POST_TYPES])}")

    
        if privacy not in [choice[0] for choice in Post.PRIVACY_CHOICES]:  
            raise ValueError(f"Invalid privacy setting: '{privacy}'. Allowed values: {', '.join([choice[0] for choice in Post.PRIVACY_CHOICES])}")

        if author:
            try:
                author = User.objects.get(id=author)
            except User.DoesNotExist:
                raise ValueError("Invalid author ID: No user found with the given ID.")
            
        if not title:
            title = ConfigManager().get_setting("Default_Title")
            
        if post_type == 'image' and 'file_size' not in metadata:
            raise ValueError("Image posts require 'file_size' in metadata")
        if post_type == 'video' and 'duration' not in metadata:
            raise ValueError("Video posts require 'duration' in metadata")

        return Post.objects.create(
            post_type=post_type,
            title=title,
            author=author,
            content=content,
            metadata=metadata,
            privacy=privacy  # New privacy field
        )
