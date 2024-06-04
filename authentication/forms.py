from allauth.account.adapter import get_adapter
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from dj_rest_auth.forms import AllAuthPasswordResetForm as DefaultAllAuthPasswordResetForm

class AllAuthPasswordResetForm(DefaultAllAuthPasswordResetForm):
    def save(self, request, **kwargs):
        current_site = get_current_site(request)
        email_template_name = "authentication/password_reset_key"
        for user in self.users:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            protocol =  "https" if request.is_secure() else "http"
            context = {
                "user": user,
                "uid": uid,
                "token": token,
                "current_site": current_site,
                "protocol": protocol,
                "frontend_url": f"{protocol}://{current_site.domain}/auth/reset_password/?uid={uid}&token={token}",
            }
            get_adapter(request).send_mail(email_template_name, user.email, context)
