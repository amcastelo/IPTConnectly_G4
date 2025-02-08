from posts.models import Post
from django.contrib.auth.models import User
from posts.Singleton.config_manager import ConfigManager

class PostFactory:
    @staticmethod
    def create_post(post_type, title, content='', metadata=None, author=None):

        titleConfig = ConfigManager()
        titleConfig.set_setting("Default_Title", "Default title")

        if post_type not in dict(Post.POST_TYPES):
            raise ValueError("Invalid post type")

        if author:
            try:
                author = User.objects.get(id=author)  # Fetch user from ID
            except User.DoesNotExist:
                raise ValueError("Invalid author ID: No user found with the given ID.")
            
        if not title:  # Handle empty string cases
            title = ConfigManager().get_setting("Default_Title")
            
        # Validate type-specific requirements
        if post_type == 'image' and 'file_size' not in metadata:
            raise ValueError("Image posts require 'file_size' in metadata")
        if post_type == 'video' and 'duration' not in metadata:
            raise ValueError("Video posts require 'duration' in metadata")


        return Post.objects.create(
            post_type=post_type,
            title=title,
            author=author,
            content=content,
            metadata=metadata
        )

