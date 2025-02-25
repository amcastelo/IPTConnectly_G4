from posts.models import Like

class LikeFactory:
    @staticmethod
    def toggle_like(user, post, like=True):
        if like:
            return LikeFactory.like_post(user, post)
        return LikeFactory.unlike_post(user, post)

    @staticmethod
    def like_post(user, post):
        like_obj, created = Like.objects.get_or_create(user=user, post=post)
        if created:
            return {"message": "Post liked successfully!", "status": 201}
        return {"message": "You already liked this post.", "status": 200}

    @staticmethod
    def unlike_post(user, post):
        try:
            like_obj = Like.objects.get(user=user, post=post)
            like_obj.delete()
            return {"message": "Like removed successfully!", "status": 200}
        except Like.DoesNotExist:
            return {"message": "You haven't liked this post yet.", "status": 400}
    # if toggle only
    # @staticmethod
    # def toggle_like(user, post):
    #     like_obj, created = Like.objects.get_or_create(user=user, post=post)
        
    #     if created:
    #         return {"message": "Post liked successfully!", "status": 201}
        
    #     like_obj.delete()
    #     return {"message": "Like removed successfully!", "status": 200}