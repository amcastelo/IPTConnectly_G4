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
from .authentications import BearerAuthentication
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import ListCreateAPIView
from rest_framework.exceptions import NotFound

logger = LoggerSingleton().get_logger()
logger.info("API initialized successfully.")

class post_pagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 10

    def paginate_queryset(self, queryset, request, view=None):
        try:
            return super().paginate_queryset(queryset, request, view)
        except NotFound:
            raise NotFound({"error": "Page does not exist. Please check the page number."})

class PaginatedPostList(ListCreateAPIView):
    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostSerializer
    pagination_class = post_pagination

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    def get_queryset(self):
        queryset = Post.objects.all().order_by('-created_at')
        user = self.request.user

        liked_param = self.request.query_params.get('liked')

        if liked_param == 'true':
            if user.is_authenticated:
                queryset = queryset.filter(likes__user=user)
            else:
                queryset = Post.objects.none()

        elif liked_param == 'false':
            if user.is_authenticated:
                queryset = queryset.exclude(likes__user=user)
            else:
                queryset = queryset.all()

        return queryset

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
                author=request.user.id,
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
        elif self.request.method in ["POST"]:
            return [IsAuthenticated()]
        return [] 
    
    def get_authenticators(self):
        if self.request.method in ["PATCH", "DELETE"]:
            return [BearerAuthentication()]
        elif self.request.method in ["POST"]:
            return [BearerAuthentication()]
        return []

class CommentListCreate(APIView):
    def get(self, request, pk=None):

        if pk is not None:
            try:
                comment = Comment.objects.get(pk=pk)
                serializer = CommentSerializer(comment)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Comment.DoesNotExist:
                return Response({"error": "Comment not found."}, status=status.HTTP_404_NOT_FOUND)
        
        comments = Comment.objects.all()
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, pk):
        logger.info(f"Creating a new comment on post ID {pk} by user: {request.user}")

        if not request.user.is_authenticated:
            return Response({"error": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

        comment_data = request.data.copy()
        comment_data["author"] = request.user.id
        comment_data["post"] = pk

        serializer = CommentSerializer(data=comment_data)

        if serializer.is_valid():
            serializer.save()
            logger.info(f"Comment on post {pk} created successfully.")
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        logger.error(f"Comment creation failed on post {pk} due to validation errors.")
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
        if self.request.method in ["POST", "PATCH", "DELETE"]:
            return [BearerAuthentication()]
        return []

class ToggleLikeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        post = self.get_post(post_id)
        if not post:
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)
        
        like = request.data.get("like", True)  
        if isinstance(like, str):
            like = like.lower() == 'true'

        response_data = LikeFactory.toggle_like(request.user, post, like)

        like_count = post.likes.count()
        response_data["like_count"] = like_count

        return Response(response_data, status=response_data["status"])

    def get_post(self, post_id):
        try:
            return Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return None

class PostDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            post = Post.objects.prefetch_related('likes', 'comments').get(pk=pk)  # Optimize query
            self.check_object_permissions(request, post)

            logger.info(f"Post ID {pk} accessed by user '{request.user}'.")

            return Response({
                "title": post.title,
                "author": post.author.username,
                "created at": post.created_at,
                "content": post.content,
                "likes": post.like_count(),
                "comment_count": post.comment_count(),

            })

        except Post.DoesNotExist:
            logger.warning(f"Post ID {pk} not found.")
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)


class ProtectedView(APIView):
    authentication_classes = [BearerAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        logger.info(f"Protected route accessed by '{request.user}'.")
        return Response({"message": "Authenticated!"})

@login_required
def fetch_google_token(request):
    try:
        social_token = SocialToken.objects.get(account__user=request.user, account__provider='google')
        return JsonResponse({'access_token': social_token.token})
    except SocialToken.DoesNotExist:
        return JsonResponse({'error': 'Token not found'}, status=404)
    
@login_required
def dashboard_view(request):
    return render(request, 'dashboard.html')

@login_required
def user_list_view(request):
    return render(request, 'user_list.html')

@login_required
def feed_view(request):
    return render(request, 'feed.html')
