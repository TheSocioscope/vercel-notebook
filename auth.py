import os
from fasthtml.oauth import GoogleAppClient
from fasthtml.oauth import OAuth

client = GoogleAppClient(os.getenv("GOOGLE_AUTH_CLIENT_ID"),
                         os.getenv("GOOGLE_AUTH_CLIENT_SECRET"))

class Auth(OAuth):
    def get_auth(self, info, ident, session, state):
        email = info.email or ''
        if info.email_verified and email.split('@')[-1]=='gmail.com':
            return RedirectResponse('/', status_code=303)