from rest_framework.authentication import BaseAuthentication, TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from allauth.socialaccount.models import SocialToken
from django.utils import timezone

# class BearerAuthentication(BaseAuthentication):
#     def authenticate(self, request):
#         # Get the Authorization header
#         auth_header = request.headers.get('Authorization')
#         if not auth_header:
#             return None

#         # Bearer <token>
#         try:
#             token = auth_header.split(" ")[1]
#         except IndexError:
#             raise AuthenticationFailed('Invalid token header. No credentials provided.')

#         try:
#             # Check if the token is a valid OAuth2 token from social authentication
#             social_token = SocialToken.objects.get(token=token)

#             # Check if the token is expired
#             if social_token.expires_at and social_token.expires_at < timezone.now():
#                 raise AuthenticationFailed('Token is expired, relogin')

#             user = social_token.account.user
#             return (user, None)  # Return the user and no DRF token
#         except SocialToken.DoesNotExist:
#             raise AuthenticationFailed('Invalid or expired token.')
# authentication.py

from rest_framework.authentication import TokenAuthentication
from allauth.socialaccount.models import SocialToken
from rest_framework.exceptions import AuthenticationFailed
from django.utils.timezone import now

class BearerAuthentication(TokenAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        token = request.headers.get("Authorization")
        if not token:
            return None

        # Extract the token value
        try:
            token_key = token.split("Bearer ")[-1].strip()
        except IndexError:
            raise AuthenticationFailed("Invalid token format.")

        try:
            # Get the social token
            social_token = SocialToken.objects.get(token=token_key)
        except SocialToken.DoesNotExist:
            raise AuthenticationFailed("Invalid token.")

        # Check if the token is expired
        if social_token.expires_at and social_token.expires_at < now():
            raise AuthenticationFailed("Token has expired.")

        # Return authenticated user
        user = social_token.account.user
        return (user, None)

