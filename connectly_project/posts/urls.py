from django.urls import path
from .views import UserListCreate, PostListCreate, CommentListCreate, ProtectedView, PostDetailView, ToggleLikeView, login_view
from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = [
    path('users/', UserListCreate.as_view(), name='user-list-create'),
    path('posts/', PostListCreate.as_view(), name='post-list-create'),
    path('posts/<int:pk>/', PostListCreate.as_view(), name='post-update-delete'),
    path('comments/', CommentListCreate.as_view(), name='comment-list-create'),
    path('comments/<int:pk>/', CommentListCreate.as_view(), name='comment-update-delete'),
    path('posts/<int:post_id>/like/', ToggleLikeView.as_view(), name='toggle-like'),
    path('<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('pv/', ProtectedView.as_view(), name='protected-view'),
    path('token-auth/', obtain_auth_token, name='obtain-token-auth'),
    path('login/', login_view, name='login'),
]

