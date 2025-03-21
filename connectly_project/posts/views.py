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
from django.db.models import Q
from django.core.cache import cache

# Initialize the logger (using your singleton logger)
logger = LoggerSingleton().get_logger()
logger.info("API initialized successfully.")


# Pagination class to define page size and handle missing pages gracefully
class post_pagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 10

    def paginate_queryset(self, queryset, request, view=None):
        try:
            return super().paginate_queryset(queryset, request, view)
        except NotFound:
            # If a page is not found, raise a custom error message.
            raise NotFound({"error": "Page does not exist. Please check the page number."})


# Paginated post feed view
class PaginatedPostList(ListCreateAPIView):
    """
    Provides a paginated list of posts (feed) with optional filtering based on likes and user ownership.
    Implements caching to improve performance.
    """
    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostSerializer
    pagination_class = post_pagination

    def get_serializer_context(self):
        # Include the request in the serializer context for URL building and other context-dependent logic.
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    def get_queryset(self):
        user = self.request.user
        liked_param = self.request.query_params.get('liked')
        user_posts = self.request.query_params.get('user_posts')

        # Create a unique cache key based on user and filter parameters.
        cache_key = f"paginated_posts_{user.id if user.is_authenticated else 'anon'}_{liked_param}_{user_posts}"
        cached_queryset = cache.get(cache_key)

        if cached_queryset:
            logger.info(f"Cache HIT: {cache_key}")
            return cached_queryset  # Return the cached queryset if available.
        else:
            logger.info(f"Cache MISS: {cache_key}")

        queryset = Post.objects.all().order_by('-created_at')

        # Privacy enforcement:
        # - Admins see all posts.
        # - Regular authenticated users see public posts and their own posts.
        # - Anonymous users see only public posts.
        if user.is_authenticated:
            if user.is_staff or user.is_superuser:
                pass  # Admins see everything.
            else:
                queryset = queryset.filter(Q(privacy='public') | Q(author=user))
        else:
            queryset = queryset.filter(privacy='public')

        # Filter posts based on whether they are liked by the user.
        if liked_param == 'true' and user.is_authenticated:
            queryset = queryset.filter(likes__user=user)
        elif liked_param == 'false' and user.is_authenticated:
            queryset = queryset.exclude(likes__user=user)

        # Filter posts to include only posts authored by the user.
        if user_posts == 'true' and user.is_authenticated:
            queryset = queryset.filter(author=user)

        # Cache the queryset for 5 minutes.
        cache.set(cache_key, queryset, timeout=300)
        return queryset


# Utility function to check and print Google social authentication token.
def check_google_token(user):
    """
    Check if the user has a Google social account token and print it.
    """
    google_account = SocialAccount.objects.filter(user=user, provider='google').first()
    if google_account:
        token = SocialToken.objects.filter(account=google_account).first()
        if token:
            print(f"Access Token: {token.token}")
        else:
            print("❌ No token found!")
    else:
        print("❌ No Google account associated with this user.")


# Render the login HTML page.
def login_view(request):
    return render(request, 'login.html')


# Endpoint for listing and creating users.
class UserListCreate(APIView):
    """
    GET: Return a list of all users (requires authentication).
    POST: Create a new user (no authentication required).
    """
    def get(self, request):
        logger.info("Fetching all users.")
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')

        # Ensure all required fields are provided.
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

    def get_permissions(self):
        # Require authentication for GET requests, but not for creating a user (POST).
        if self.request.method == "GET":
            return [IsAuthenticated()]
        elif self.request.method == "POST":
            return []  # Allow unauthenticated user creation.
        return []


# Endpoint for listing and creating posts.
class PostListCreate(APIView):
    """
    GET: Retrieve all posts (with appropriate filtering based on user permissions).
    POST: Create a new post (requires authentication).
    PATCH: Update an existing post (requires that the user is the author or an admin).
    DELETE: Delete a post (requires that the user is the author or an admin).
    """
    serializer_class = PostSerializer

    def get(self, request):
        logger.info("Fetching all posts.")
        posts = Post.objects.all()
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data
        try:
            # Create a new post using the PostFactory.
            post = PostFactory.create_post(
                post_type=data['post_type'],
                title=data['title'],
                author=request.user.id,
                content=data.get('content', ''),
                metadata=data.get('metadata', {}),
                privacy=data['privacy']
            )
            logger.info(f"Post created successfully: ID {post.id}")
            serializer = self.get_serializer(post)
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

        serializer = self.get_serializer(post, data=request.data, partial=True)
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
        # Permissions vary by method:
        # - PATCH and DELETE require authentication and either authorship or admin rights.
        # - POST requires authentication.
        # - GET requires authentication plus admin rights.
        if self.request.method in ["PATCH", "DELETE"]:
            return [IsAuthenticated(), IsPostAuthorOrAdmin()]
        elif self.request.method == "POST":
            return [IsAuthenticated()]
        elif self.request.method == "GET":
            return [IsAuthenticated(), IsAdmin()]
        return []

    def get_serializer(self, *args, **kwargs):
        kwargs.setdefault("context", {"request": self.request})
        return self.serializer_class(*args, **kwargs)


# Endpoint for handling comments on posts.
class CommentListCreate(APIView):
    """
    GET: Retrieve a specific comment if a pk is provided, or list all comments.
    POST: Create a new comment on a specified post (requires authentication).
    PATCH: Update a comment (requires appropriate permissions).
    DELETE: Delete a comment (requires appropriate permissions).
    """
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
        # Log comment creation attempt on the given post.
        logger.info(f"Creating a new comment on post ID {pk} by user: {request.user}")
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

        # Prepare comment data, setting the author to the logged-in user and associating it with the post.
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
        # For PATCH and DELETE, require authentication and check that the user is either the post author or an admin.
        if self.request.method in ["PATCH", "DELETE"]:
            return [IsAuthenticated(), IsPostAuthorOrAdmin()]
        return []


# Endpoint for toggling likes on posts.
class ToggleLikeView(APIView):
    """
    POST: Toggle the like state for a given post by the logged-in user.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        post = self.get_post(post_id)
        if not post:
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)
        
        like = request.data.get("like", True)
        # If like is provided as a string, convert it to a boolean.
        if isinstance(like, str):
            like = like.lower() == 'true'

        response_data = LikeFactory.toggle_like(request.user, post, like)
        # Update like count from the post.
        like_count = post.likes.count()
        response_data["like_count"] = like_count

        return Response(response_data, status=response_data["status"])

    def get_post(self, post_id):
        try:
            return Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return None


# Endpoint for retrieving post details.
class PostDetailView(APIView):
    """
    GET: Retrieve detailed information for a specific post.
         Enforces privacy: private posts are visible only to their authors or admins.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            # Optimize query by prefetching related likes and comments.
            post = Post.objects.prefetch_related('likes', 'comments').get(pk=pk)
            # Enforce privacy settings.
            if post.privacy == 'private' and request.user != post.author and not request.user.is_staff:
                logger.warning(f"Unauthorized access attempt on private post ID {pk} by '{request.user}'.")
                return Response({"error": "You do not have permission to view this post."}, status=status.HTTP_403_FORBIDDEN)

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


# A simple endpoint to test if a user is authenticated.
class ProtectedView(APIView):
    """
    GET: Returns a success message if the user is authenticated.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        logger.info(f"Protected route accessed by '{request.user}'.")
        return Response({"message": "Authenticated!"})


# View to fetch Google social token; accessible only when logged in.
@login_required
def fetch_google_token(request):
    try:
        social_token = SocialToken.objects.get(account__user=request.user, account__provider='google')
        return JsonResponse({'access_token': social_token.token})
    except SocialToken.DoesNotExist:
        return JsonResponse({'error': 'Token not found'}, status=404)
    

# Render the dashboard HTML page.
@login_required
def dashboard_view(request):
    return render(request, 'dashboard.html')


# Render the user list HTML page.
@login_required
def user_list_view(request):
    return render(request, 'user_list.html')


# Render the feed HTML page.
@login_required
def feed_view(request):
    return render(request, 'feed.html')
