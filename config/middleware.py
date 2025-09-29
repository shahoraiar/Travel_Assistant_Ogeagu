# config/middleware.py
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from urllib.parse import parse_qs
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model

User = get_user_model()

@database_sync_to_async
def get_user(validated_token):
    try:
        return User.objects.get(id=validated_token["user_id"])
    except User.DoesNotExist:
        return AnonymousUser()

class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom middleware to authenticate JWT from header 'Authorization: Bearer ...'
    """
    async def __call__(self, scope, receive, send):
        headers = dict(scope.get("headers", []))
        # Headers come as list of [b'name', b'value]
        auth_header = headers.get(b'authorization', None)

        if auth_header:
            token_str = auth_header.decode().split("Bearer ")[-1]
            try:
                validated = UntypedToken(token_str)
                scope["user"] = await get_user(validated)
            except (InvalidToken, TokenError):
                scope["user"] = AnonymousUser()
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)
