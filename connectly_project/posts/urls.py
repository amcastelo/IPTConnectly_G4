from django.urls import path
from .views import UserListCreate, PostListCreate, CommentListCreate, ProtectedView
from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = [
    path('users/', UserListCreate.as_view(), name='user-list-create'),
    path('posts/', PostListCreate.as_view(), name='post-list-create'),
    path('comments/', CommentListCreate.as_view(), name='comment-list-create'),
    path('pv/', ProtectedView.as_view(), name='protected-view'),
    path('token-auth/', obtain_auth_token, name='obtain-token-auth'),
]

