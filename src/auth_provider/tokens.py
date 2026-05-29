"""Token policy contracts for the OAuth provider boundary."""

from dataclasses import dataclass
from typing import Literal

from auth_provider.configuration import ProviderConfigurationError

DEFAULT_JWT_SIGNING_ALGORITHM = "RS256"
DEFAULT_ACCESS_TOKEN_LIFETIME_SECONDS = 3_600
DEFAULT_ID_TOKEN_LIFETIME_SECONDS = 3_600
DEFAULT_AUTHORISATION_CODE_LIFETIME_SECONDS = 600
DEFAULT_REFRESH_TOKEN_LIFETIME_SECONDS = 2_592_000

RefreshTokenVerifierKind = Literal["keyed-hash"]
RefreshTokenReuseAction = Literal[
    "revoke-token-family",
    "quarantine-token-family",
]


@dataclass(frozen=True, slots=True)
class RefreshTokenStoragePolicy:
    """Opaque refresh-token storage and reuse-detection policy."""

    verifier_kind: RefreshTokenVerifierKind = "keyed-hash"
    rotate_on_use: bool = True
    reuse_action: RefreshTokenReuseAction = "revoke-token-family"

    def __post_init__(self) -> None:
        if self.verifier_kind != "keyed-hash":
            raise ProviderConfigurationError(
                "Refresh token verifiers must be stored as keyed hashes."
            )

        if not self.rotate_on_use:
            raise ProviderConfigurationError("Refresh tokens must rotate on use.")

        if self.reuse_action not in (
            "revoke-token-family",
            "quarantine-token-family",
        ):
            raise ProviderConfigurationError(
                "Refresh token reuse action must revoke or quarantine the token family."
            )
