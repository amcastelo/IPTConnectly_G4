from django.urls import path
from . import views

from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = [
    path('users/', views.UserListCreate.as_view(), name='user-list-create'),
    path('posts/', views.PostListCreate.as_view(), name='post-list-create'),
    path('posts/<int:pk>/', views.PostListCreate.as_view(), name='post-update-delete'),
    path('comments/', views.CommentListCreate.as_view(), name='comment-list-'),
    path('comments/<int:pk>/', views.CommentListCreate.as_view(), name='comment-post-update-delete'),
    path('posts/<int:post_id>/like/', views.ToggleLikeView.as_view(), name='toggle-like'),
    path('<int:pk>/', views.PostDetailView.as_view(), name='post-detail'),
    path('pv/', views.ProtectedView.as_view(), name='protected-view'),
    path('token-auth/', obtain_auth_token, name='obtain-token-auth'),
    path('login/', views.login_view, name='login'),
    path('api/get-google-token/', views.fetch_google_token, name='get_google_token'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('user-list/', views.user_list_view, name='user_list'),
    path('feed/', views.feed_view, name='post_page'),
    path('paginated-posts/', views.PaginatedPostList.as_view(), name='paginated-posts'),
]

