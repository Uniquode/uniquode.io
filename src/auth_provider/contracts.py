"""Host-facing OAuth provider contracts."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ProviderSubject:
    """Authenticated subject supplied by the host application."""

    id: str
    active: bool = True
    email: str | None = None
    display_name: str | None = None


@dataclass(frozen=True, slots=True)
class OAuthClient:
    """OAuth client metadata supplied by the host application."""

    id: str
    redirect_uris: tuple[str, ...]
    allowed_scopes: frozenset[str]
    is_confidential: bool = True


@dataclass(frozen=True, slots=True)
class AuthorisationGrant:
    """Stored authorisation grant awaiting token exchange."""

    id: str
    client_id: str
    subject_id: str
    redirect_uri: str
    scopes: frozenset[str]
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class RefreshTokenRecord:
    """Stored refresh-token verifier record."""

    id: str
    family_id: str
    client_id: str
    subject_id: str
    verifier: str
    scopes: frozenset[str]
    issued_at: datetime
    expires_at: datetime
    consumed_at: datetime | None = None
    revoked_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class SigningKeyReference:
    """Public signing-key metadata exposed through JWKS."""

    key_id: str
    algorithm: str
    public_jwk: dict[str, object]


class SubjectResolver(Protocol):
    async def resolve_subject(self, context: object) -> ProviderSubject | None: ...


class ClientStore(Protocol):
    async def get_client(self, client_id: str) -> OAuthClient | None: ...


class GrantStore(Protocol):
    async def save_grant(self, grant: AuthorisationGrant) -> None: ...

    async def consume_grant(self, grant_id: str) -> AuthorisationGrant | None: ...


class ConsentStore(Protocol):
    async def has_consent(
        self,
        subject: ProviderSubject,
        client: OAuthClient,
        scopes: frozenset[str],
    ) -> bool: ...

    async def record_consent(
        self,
        subject: ProviderSubject,
        client: OAuthClient,
        scopes: frozenset[str],
    ) -> None: ...


class ScopePolicy(Protocol):
    async def allowed_scopes(
        self,
        subject: ProviderSubject,
        client: OAuthClient,
        requested_scopes: frozenset[str],
    ) -> frozenset[str]: ...


class RefreshTokenStore(Protocol):
    """Opaque refresh-token persistence contract.

    Implementations must treat refresh-token consumption as a single-writer
    state transition. `mark_refresh_token_consumed` must atomically mark the
    presented token consumed and store its successor in the same transaction or
    equivalent compare-and-swap operation. It must not create a second
    successor when the token is already consumed or revoked.

    Reuse detection is intentionally not idempotent: if an already consumed or
    revoked token is presented, callers should treat that as compromise and use
    `revoke_token_family` or an equivalent quarantine action before returning.

    Client-wide logout is modelled by revoking all live refresh-token families
    for the subject/client pair. This does not directly delete already issued
    stateless access tokens; it prevents further refresh and relies on short
    access-token lifetimes unless a later access-token revocation store is
    introduced.
    """

    async def store_refresh_token(self, token: RefreshTokenRecord) -> None: ...

    async def get_refresh_token_by_verifier(
        self,
        verifier: str,
    ) -> RefreshTokenRecord | None: ...

    async def mark_refresh_token_consumed(
        self,
        token_id: str,
        successor: RefreshTokenRecord,
    ) -> None: ...

    async def revoke_token_family(self, family_id: str) -> None: ...

    async def revoke_subject_client_token_families(
        self,
        subject_id: str,
        client_id: str,
    ) -> None: ...


class SigningKeyStore(Protocol):
    async def active_signing_key(self, algorithm: str) -> SigningKeyReference: ...

    async def public_signing_keys(self) -> tuple[SigningKeyReference, ...]: ...
