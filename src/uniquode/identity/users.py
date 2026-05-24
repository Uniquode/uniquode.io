from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterator, Callable

from fastapi import HTTPException, Request, status
from fastapi.responses import Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import AuthenticationBackend, CookieTransport
from fastapi_users.authentication.strategy.db import DatabaseStrategy
from fastapi_users.exceptions import FastAPIUsersException, UserNotExists
from fastapi_users.password import PasswordHelper
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from fastapi_users_db_sqlalchemy.access_token import SQLAlchemyAccessTokenDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from uniquode.identity.delivery import IdentityDelivery, NullIdentityDelivery
from uniquode.identity.options import IdentityOptions
from uniquode.models import AccessToken, OAuthAccount, User
from uniquode.persistence import Database, session_scope

_CURRENT_USER_CACHE_TOKEN_ATTR = "identity_current_user_token"
_CURRENT_USER_CACHE_VALUE_ATTR = "identity_current_user"
_CURRENT_USER_CACHE_MISSING = object()
logger = logging.getLogger(__name__)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    """FastAPI Users manager for the canonical local account model."""

    def __init__(
        self,
        user_db: SQLAlchemyUserDatabase[User, uuid.UUID],
        options: IdentityOptions,
        delivery: IdentityDelivery | None = None,
        password_helper: PasswordHelper | None = None,
    ) -> None:
        super().__init__(user_db, password_helper)
        self.delivery = delivery or NullIdentityDelivery()
        self.reset_password_token_secret = options.reset_password_token_secret
        self.verification_token_secret = options.verification_token_secret

    async def on_after_forgot_password(
        self,
        user: User,
        token: str,
        request: Request | None = None,
    ) -> None:
        await self.delivery.send_reset_password_token(user, token, request)

    async def on_after_request_verify(
        self,
        user: User,
        token: str,
        request: Request | None = None,
    ) -> None:
        await self.delivery.send_verification_token(user, token, request)


def create_password_helper() -> PasswordHelper:
    return PasswordHelper()


def create_user_database(
    session: AsyncSession,
) -> SQLAlchemyUserDatabase[User, uuid.UUID]:
    return SQLAlchemyUserDatabase(session, User, OAuthAccount)


def create_user_manager(
    session: AsyncSession,
    options: IdentityOptions,
    delivery: IdentityDelivery | None = None,
) -> UserManager:
    return UserManager(
        create_user_database(session),
        options,
        delivery,
        create_password_helper(),
    )


def create_access_token_database(
    session: AsyncSession,
) -> SQLAlchemyAccessTokenDatabase[AccessToken]:
    return SQLAlchemyAccessTokenDatabase(session, AccessToken)


def create_database_strategy(
    session: AsyncSession,
    options: IdentityOptions,
) -> DatabaseStrategy[User, uuid.UUID, AccessToken]:
    return DatabaseStrategy(
        create_access_token_database(session),
        lifetime_seconds=options.session_lifetime_seconds,
    )


def _database_from_request(request: Request) -> Database:
    database = getattr(request.app.state, "database", None)
    if not isinstance(database, Database):
        raise RuntimeError("Database is not configured on the application.")

    return database


def _identity_options_from_request(request: Request) -> IdentityOptions:
    options = request.app.state.settings.identity_options
    if not isinstance(options, IdentityOptions):
        raise RuntimeError("Identity options are not configured on the application.")

    return options


def _delivery_from_request(request: Request) -> IdentityDelivery:
    delivery = getattr(request.app.state, "identity_delivery", None)
    if delivery is None:
        return NullIdentityDelivery()

    return delivery


def create_user_manager_dependency(
    options: IdentityOptions,
) -> Callable[[Request], AsyncIterator[UserManager]]:
    async def get_user_manager(request: Request) -> AsyncIterator[UserManager]:
        database = _database_from_request(request)
        async with session_scope(database.session_factory) as session:
            yield create_user_manager(session, options, _delivery_from_request(request))

    return get_user_manager


def create_database_strategy_dependency(
    options: IdentityOptions,
) -> Callable[[Request], AsyncIterator[DatabaseStrategy[User, uuid.UUID, AccessToken]]]:
    async def get_database_strategy(
        request: Request,
    ) -> AsyncIterator[DatabaseStrategy[User, uuid.UUID, AccessToken]]:
        database = _database_from_request(request)
        async with session_scope(database.session_factory) as session:
            yield create_database_strategy(session, options)

    return get_database_strategy


def create_authentication_backend(
    options: IdentityOptions,
) -> AuthenticationBackend[User, uuid.UUID]:
    transport = CookieTransport(
        cookie_name=options.session_cookie_name,
        cookie_max_age=options.session_lifetime_seconds,
        cookie_secure=options.session_cookie_secure,
        cookie_httponly=True,
        cookie_samesite="lax",
    )
    return AuthenticationBackend(
        name="session",
        transport=transport,
        get_strategy=create_database_strategy_dependency(options),
    )


def create_fastapi_users(options: IdentityOptions) -> FastAPIUsers[User, uuid.UUID]:
    return FastAPIUsers(
        create_user_manager_dependency(options),
        [create_authentication_backend(options)],
    )


def set_session_cookie(
    response: Response,
    token: str,
    options: IdentityOptions,
) -> None:
    response.set_cookie(
        options.session_cookie_name,
        token,
        max_age=options.session_lifetime_seconds,
        path="/",
        secure=options.session_cookie_secure,
        httponly=True,
        samesite="lax",
    )


def clear_session_cookie(response: Response, options: IdentityOptions) -> None:
    response.set_cookie(
        options.session_cookie_name,
        "",
        max_age=0,
        path="/",
        secure=options.session_cookie_secure,
        httponly=True,
        samesite="lax",
    )


def _cached_current_user(request: Request, token: str | None) -> User | None | object:
    cached_token = getattr(request.state, _CURRENT_USER_CACHE_TOKEN_ATTR, None)
    if cached_token != token:
        return _CURRENT_USER_CACHE_MISSING

    return getattr(
        request.state,
        _CURRENT_USER_CACHE_VALUE_ATTR,
        _CURRENT_USER_CACHE_MISSING,
    )


def _cache_current_user(
    request: Request,
    token: str | None,
    user: User | None,
) -> User | None:
    setattr(request.state, _CURRENT_USER_CACHE_TOKEN_ATTR, token)
    setattr(request.state, _CURRENT_USER_CACHE_VALUE_ATTR, user)
    return user


async def resolve_current_user(request: Request) -> User | None:
    options = _identity_options_from_request(request)
    token = request.cookies.get(options.session_cookie_name)
    cached_user = _cached_current_user(request, token)
    if cached_user is None or isinstance(cached_user, User):
        return cached_user

    if token is None:
        return _cache_current_user(request, token, None)

    database = _database_from_request(request)
    async with session_scope(database.session_factory) as session:
        manager = create_user_manager(
            session,
            options,
            _delivery_from_request(request),
        )
        strategy = create_database_strategy(session, options)
        user = await strategy.read_token(token, manager)
        if user is not None and not user.is_active:
            await _delete_session_token_by_value(session, token)
            return _cache_current_user(request, token, None)

        return _cache_current_user(request, token, user)


async def optional_current_user(request: Request) -> User | None:
    return await resolve_current_user(request)


async def require_current_user(request: Request) -> User:
    user = await resolve_current_user(request)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    return user


async def require_anonymous_user(request: Request) -> None:
    user = await resolve_current_user(request)
    if user is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Already authenticated.",
        )


async def authenticate_user(
    request: Request,
    email: str,
    password: str,
) -> User | None:
    options = _identity_options_from_request(request)
    database = _database_from_request(request)
    credentials = OAuth2PasswordRequestForm(username=email, password=password)

    async with session_scope(database.session_factory) as session:
        manager = create_user_manager(
            session,
            options,
            _delivery_from_request(request),
        )
        user = await manager.authenticate(credentials)
        if user is None or not user.is_active:
            return None

        return user


async def create_session_token(request: Request, user: User) -> str:
    options = _identity_options_from_request(request)
    database = _database_from_request(request)

    async with session_scope(database.session_factory) as session:
        strategy = create_database_strategy(session, options)
        return await strategy.write_token(user)


async def destroy_session_token(request: Request) -> None:
    options = _identity_options_from_request(request)
    token = request.cookies.get(options.session_cookie_name)
    if token is None:
        return

    database = _database_from_request(request)
    async with session_scope(database.session_factory) as session:
        await _delete_session_token_by_value(session, token)

    _cache_current_user(request, token, None)


async def _delete_session_token_by_value(session: AsyncSession, token: str) -> None:
    access_token_database = create_access_token_database(session)
    access_token = await access_token_database.get_by_token(token)
    if access_token is not None:
        await access_token_database.delete(access_token)


async def request_password_reset(request: Request, email: str) -> None:
    options = _identity_options_from_request(request)
    database = _database_from_request(request)

    async with session_scope(database.session_factory) as session:
        manager = create_user_manager(
            session,
            options,
            _delivery_from_request(request),
        )
        try:
            user = await manager.get_by_email(email)
        except UserNotExists:
            return

        try:
            await manager.forgot_password(user, request)
        except FastAPIUsersException:
            logger.warning(
                "Password reset request was rejected by the identity backend.",
                exc_info=True,
            )
            return


async def reset_password(request: Request, token: str, password: str) -> bool:
    options = _identity_options_from_request(request)
    database = _database_from_request(request)

    async with session_scope(database.session_factory) as session:
        manager = create_user_manager(
            session,
            options,
            _delivery_from_request(request),
        )
        try:
            await manager.reset_password(token, password, request)
        except FastAPIUsersException:
            return False

        return True


async def request_verification(request: Request, email: str) -> None:
    options = _identity_options_from_request(request)
    database = _database_from_request(request)

    async with session_scope(database.session_factory) as session:
        manager = create_user_manager(
            session,
            options,
            _delivery_from_request(request),
        )
        try:
            user = await manager.get_by_email(email)
        except UserNotExists:
            return

        try:
            await manager.request_verify(user, request)
        except FastAPIUsersException:
            logger.warning(
                "Verification request was rejected by the identity backend.",
                exc_info=True,
            )
            return


async def verify_user(request: Request, token: str) -> bool:
    options = _identity_options_from_request(request)
    database = _database_from_request(request)

    async with session_scope(database.session_factory) as session:
        manager = create_user_manager(
            session,
            options,
            _delivery_from_request(request),
        )
        try:
            await manager.verify(token, request)
        except FastAPIUsersException:
            return False

        return True
