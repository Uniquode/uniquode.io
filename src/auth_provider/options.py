"""Provider options supplied by host applications."""

from dataclasses import dataclass, field

from auth_provider.configuration import ProviderConfigurationError
from auth_provider.tokens import (
    DEFAULT_ACCESS_TOKEN_LIFETIME_SECONDS,
    DEFAULT_AUTHORISATION_CODE_LIFETIME_SECONDS,
    DEFAULT_ID_TOKEN_LIFETIME_SECONDS,
    DEFAULT_JWT_SIGNING_ALGORITHM,
    DEFAULT_REFRESH_TOKEN_LIFETIME_SECONDS,
    RefreshTokenStoragePolicy,
)


@dataclass(frozen=True, slots=True)
class OAuthProviderOptions:
    """Host-owned OAuth provider enablement and public URL options."""

    enabled: bool = False
    issuer: str | None = None
    mount_path: str = "/oauth"
    signing_algorithm: str = DEFAULT_JWT_SIGNING_ALGORITHM
    access_token_lifetime_seconds: int = DEFAULT_ACCESS_TOKEN_LIFETIME_SECONDS
    id_token_lifetime_seconds: int = DEFAULT_ID_TOKEN_LIFETIME_SECONDS
    authorisation_code_lifetime_seconds: int = (
        DEFAULT_AUTHORISATION_CODE_LIFETIME_SECONDS
    )
    refresh_token_lifetime_seconds: int = DEFAULT_REFRESH_TOKEN_LIFETIME_SECONDS
    refresh_tokens: RefreshTokenStoragePolicy = field(
        default_factory=RefreshTokenStoragePolicy
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "mount_path", _normalise_mount_path(self.mount_path))
        object.__setattr__(
            self,
            "signing_algorithm",
            _normalise_required(self.signing_algorithm, "signing_algorithm"),
        )
        _validate_positive_lifetime(
            "access_token_lifetime_seconds",
            self.access_token_lifetime_seconds,
        )
        _validate_positive_lifetime(
            "id_token_lifetime_seconds",
            self.id_token_lifetime_seconds,
        )
        _validate_positive_lifetime(
            "authorisation_code_lifetime_seconds",
            self.authorisation_code_lifetime_seconds,
        )
        _validate_positive_lifetime(
            "refresh_token_lifetime_seconds",
            self.refresh_token_lifetime_seconds,
        )

        if self.issuer is None:
            if self.enabled:
                raise ProviderConfigurationError(
                    "Enabled OAuth providers must define an issuer."
                )
            return

        issuer = self.issuer.strip()
        if not issuer:
            raise ProviderConfigurationError("OAuth provider issuer must not be blank.")

        object.__setattr__(self, "issuer", issuer)


def _normalise_mount_path(value: str) -> str:
    """Normalise a host-configured provider mount path.

    A root mount is allowed only when configured explicitly as ``"/"``. Empty
    values are rejected by `_normalise_required`, and slash-only values other
    than ``"/"`` are rejected to avoid accidentally exposing provider routes at
    the application root.
    """

    path = _normalise_required(value, "mount_path")
    if path != "/" and not path.strip("/"):
        raise ProviderConfigurationError(
            "OAuth provider mount_path must not contain only slashes; "
            "use '/' explicitly to mount at the application root."
        )

    if not path.startswith("/"):
        path = f"/{path}"

    return path.rstrip("/") or "/"


def _normalise_required(value: str, field_name: str) -> str:
    normalised = value.strip()
    if not normalised:
        raise ProviderConfigurationError(f"{field_name} must not be blank.")

    return normalised


def _validate_positive_lifetime(field_name: str, value: int) -> None:
    if value <= 0:
        raise ProviderConfigurationError(f"{field_name} must be positive.")
