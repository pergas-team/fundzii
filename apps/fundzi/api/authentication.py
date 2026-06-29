from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """Session auth without CSRF enforcement — safe for same-origin SPA + cookie sessions."""

    def enforce_csrf(self, request):
        return
