from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Post, Comment
from .serializers import UserSerializer, PostSerializer, CommentSerializer
from django.contrib.auth.models import Group, User
from django.contrib.auth import authenticate
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from .permissions import IsPostAuthor, IsAdmin, IsPostAuthorOrAdmin
from posts.Singleton.logger_singleton import LoggerSingleton
from posts.Factories.post_factory import PostFactory
from posts.Factories.like_factory import LikeFactory
from django.shortcuts import render
from allauth.socialaccount.models import SocialToken, SocialAccount

logger = LoggerSingleton().get_logger()
logger.info("API initialized successfully.")

def check_google_token(user):
    google_account = SocialAccount.objects.filter(user=user, provider='google').first()
    if google_account:
        token = SocialToken.objects.filter(account=google_account).first()
        if token:
            print(f"Access Token: {token.token}")
        else:
            print("❌ No token found!")

def login_view(request):
    return render(request, 'login.html')

class UserListCreate(APIView):
    def get(self, request):
        logger.info("Fetching all users.")
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')

        if username and password and email:
            try:
                user = User.objects.create_user(username=username, password=password, email=email)
                logger.info(f"User '{username}' created successfully.")
                return Response({"message": "User created successfully!"}, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Error creating user '{username}': {str(e)}")
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.warning("Missing username, password, or email in request.")
            return Response({"error": "Username, password, and email are required."}, status=status.HTTP_400_BAD_REQUEST)


class PostListCreate(APIView):
    def get(self, request):
        logger.info("Fetching all posts.")
        posts = Post.objects.all()
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data

        try:
            post = PostFactory.create_post(
                post_type=data['post_type'],
                title=data['title'],
                author=data.get('author'),
                content=data.get('content', ''),
                metadata=data.get('metadata', {})
            )
            logger.info(f"Post created successfully: ID {post.id}")

            serializer = PostSerializer(post)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


    def patch(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
            self.check_object_permissions(request, post)
            logger.info(f"Updating post ID: {pk}.")
        except Post.DoesNotExist:
            logger.warning(f"Post ID {pk} not found.")
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = PostSerializer(post, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Post ID {pk} updated successfully.")
            return Response(serializer.data, status=status.HTTP_200_OK)
        logger.error(f"Failed to update post ID {pk} due to validation errors.")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)  
            self.check_object_permissions(request, post)
            logger.info(f"Deleting post ID: {pk}.")
        except Post.DoesNotExist:
            logger.warning(f"Post ID {pk} not found.")
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

        post.delete()
        logger.info(f"Post ID {pk} deleted successfully.")
        return Response({"message": "Post deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    
    def get_permissions(self):
        if self.request.method in ["PATCH", "DELETE"]:
            return [IsAuthenticated(), IsPostAuthorOrAdmin()] 
        return [] 
    
    def get_authenticators(self):
        if self.request.method in ["PATCH", "DELETE"]:
            return [TokenAuthentication()]
        return []

class CommentListCreate(APIView):
    def get(self, request):
        logger.info("Fetching all comments.")
        comments = Comment.objects.all()
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    def post(self, request):
        logger.info("Creating a new comment.")
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info("Comment created successfully.")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error("Comment creation failed due to validation errors.")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        try:
            comment = Comment.objects.get(pk=pk)
            self.check_object_permissions(request, comment)
            logger.info(f"Updating comment ID: {pk}.")
        except Comment.DoesNotExist:
            logger.warning(f"Comment ID {pk} not found.")
            return Response({"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = CommentSerializer(comment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Comment ID {pk} updated successfully.")
            return Response(serializer.data, status=status.HTTP_200_OK)
        logger.error(f"Failed to update comment ID {pk} due to validation errors.")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            comment = Comment.objects.get(pk=pk)
            self.check_object_permissions(request, comment)
            logger.info(f"Deleting comment ID: {pk}.")
        except Comment.DoesNotExist:
            logger.warning(f"Comment ID {pk} not found.")
            return Response({"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND)

        comment.delete()
        logger.info(f"Comment ID {pk} deleted successfully.")
        return Response({"message": "Comment deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    
    def get_permissions(self):
        if self.request.method in ["PATCH", "DELETE"]:
            return [IsAuthenticated(), IsPostAuthorOrAdmin()] 
        return [] 
    
    def get_authenticators(self):
        if self.request.method in ["PATCH", "DELETE"]:
            return [TokenAuthentication()]
        return []

class ToggleLikeView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        post = self.get_post(post_id)
        if not post:
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

        like = request.data.get("like", True)  # Default to True (like)
        response_data = LikeFactory.toggle_like(request.user, post, like)
        return Response({"message": response_data["message"]}, status=response_data["status"])

    def get_post(self, post_id):
        try:
            return Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return None 


class PostDetailView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsPostAuthor | IsAdmin]

    def get(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
            self.check_object_permissions(request, post)
            logger.info(f"Post ID {pk} accessed by user '{request.user}'.")
            return Response({"content": post.content})
        except Post.DoesNotExist:
            logger.warning(f"Post ID {pk} not found.")
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)


class ProtectedView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        logger.info(f"Protected route accessed by '{request.user}'.")
        return Response({"message": "Authenticated!"})
