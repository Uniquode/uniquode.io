"""Reusable FastAPI OAuth2/OIDC provider boundary.

This package is intentionally independent of FastAPI Users, `auth_ext`, and
host application packages. Runtime OAuth2/OIDC endpoint implementation remains
deferred until local users and authorisation scopes/groups are stable.
"""

from auth_provider.configuration import ProviderConfigurationError
from auth_provider.contracts import (
    AuthorisationGrant,
    ClientStore,
    ConsentStore,
    GrantStore,
    OAuthClient,
    ProviderSubject,
    RefreshTokenRecord,
    RefreshTokenStore,
    ScopePolicy,
    SigningKeyReference,
    SigningKeyStore,
    SubjectResolver,
)
from auth_provider.options import OAuthProviderOptions
from auth_provider.tokens import (
    DEFAULT_ACCESS_TOKEN_LIFETIME_SECONDS,
    DEFAULT_AUTHORISATION_CODE_LIFETIME_SECONDS,
    DEFAULT_ID_TOKEN_LIFETIME_SECONDS,
    DEFAULT_JWT_SIGNING_ALGORITHM,
    DEFAULT_REFRESH_TOKEN_LIFETIME_SECONDS,
    RefreshTokenReuseAction,
    RefreshTokenStoragePolicy,
    RefreshTokenVerifierKind,
)

__all__ = (
    "DEFAULT_ACCESS_TOKEN_LIFETIME_SECONDS",
    "DEFAULT_AUTHORISATION_CODE_LIFETIME_SECONDS",
    "DEFAULT_ID_TOKEN_LIFETIME_SECONDS",
    "DEFAULT_JWT_SIGNING_ALGORITHM",
    "DEFAULT_REFRESH_TOKEN_LIFETIME_SECONDS",
    "AuthorisationGrant",
    "ClientStore",
    "ConsentStore",
    "GrantStore",
    "OAuthClient",
    "OAuthProviderOptions",
    "ProviderConfigurationError",
    "ProviderSubject",
    "RefreshTokenRecord",
    "RefreshTokenReuseAction",
    "RefreshTokenStoragePolicy",
    "RefreshTokenStore",
    "RefreshTokenVerifierKind",
    "ScopePolicy",
    "SigningKeyReference",
    "SigningKeyStore",
    "SubjectResolver",
)
