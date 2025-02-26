from allauth.socialaccount.signals import social_account_added
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from allauth.account.signals import user_logged_in
from allauth.socialaccount.models import SocialToken
import time

User = get_user_model()

def link_or_create_user(google_data):
    email = google_data.get('email')
    user = User.objects.filter(email=email).first()

    if user:
        # Link Google account if not linked
        if not SocialAccount.objects.filter(user=user, provider='google').exists():
            SocialAccount.objects.create(user=user, uid=google_data['sub'], provider='google')
        return user
    else:
        # Create new user
        user = User.objects.create_user(email=email, username=email.split('@')[0])
        SocialAccount.objects.create(user=user, uid=google_data['sub'], provider='google')
        return user

@receiver(social_account_added)
def handle_google_login(request, sociallogin, **kwargs):
    if sociallogin.account.provider == 'google':
        google_data = sociallogin.account.extra_data
        link_or_create_user(google_data)

# @receiver(user_logged_in)
# def ensure_social_token(sender, request, user, **kwargs):
#     from allauth.socialaccount.models import SocialAccount
#     google_account = SocialAccount.objects.filter(user=user, provider='google').first()

#     if google_account and not SocialToken.objects.filter(account=google_account).exists():
#         print("Google account linked, but no token found!")

def check_google_token(user):
    google_account = SocialAccount.objects.filter(user=user, provider='google').first()
    
    # Wait to ensure the token is stored
    if google_account:
        time.sleep(3)  # Wait 3 seconds before checking
        
        token = SocialToken.objects.filter(account=google_account).first()
        if token:
            print(f"✅ Access Token: {token.token}")
        else:
            print("❌ No token found after delay!")

@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    check_google_token(user)
