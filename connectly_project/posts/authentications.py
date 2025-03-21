from rest_framework.authentication import BaseAuthentication, TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from allauth.socialaccount.models import SocialToken
from django.utils.timezone import now

class BearerAuthentication(TokenAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None

        # Only handle the request if the header starts with "Bearer "
        if not auth_header.startswith("Bearer "):
            return None  # Let other authentication classes (like TokenAuthentication) process it

        try:
            token_key = auth_header.split("Bearer ")[-1].strip()
        except IndexError:
            raise AuthenticationFailed("Invalid token format.")

        try:
            # Get the social token based on your model
            social_token = SocialToken.objects.get(token=token_key)
        except SocialToken.DoesNotExist:
            raise AuthenticationFailed("Invalid token.")

        # Check if the token is expired
        if social_token.expires_at and social_token.expires_at < now():
            raise AuthenticationFailed("Token has expired.")

        user = social_token.account.user
        return (user, None)
