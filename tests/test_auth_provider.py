from typing import get_type_hints

import pytest

from auth_provider import (
    DEFAULT_ACCESS_TOKEN_LIFETIME_SECONDS,
    DEFAULT_AUTHORISATION_CODE_LIFETIME_SECONDS,
    DEFAULT_ID_TOKEN_LIFETIME_SECONDS,
    DEFAULT_JWT_SIGNING_ALGORITHM,
    DEFAULT_REFRESH_TOKEN_LIFETIME_SECONDS,
    OAuthClient,
    OAuthProviderOptions,
    ProviderConfigurationError,
    ProviderSubject,
    RefreshTokenStoragePolicy,
    RefreshTokenStore,
)


def _frozen_instance_error() -> tuple[type[Exception], ...]:
    return AttributeError, TypeError


def _assign_attribute(instance: object, name: str, value: object) -> None:
    setattr(instance, name, value)


def test_auth_provider_options_default_to_disabled_provider() -> None:
    options = OAuthProviderOptions()

    assert options.enabled is False
    assert options.issuer is None
    assert options.mount_path == "/oauth"
    assert options.signing_algorithm == DEFAULT_JWT_SIGNING_ALGORITHM
    assert (
        options.access_token_lifetime_seconds == DEFAULT_ACCESS_TOKEN_LIFETIME_SECONDS
    )
    assert options.id_token_lifetime_seconds == DEFAULT_ID_TOKEN_LIFETIME_SECONDS
    assert (
        options.authorisation_code_lifetime_seconds
        == DEFAULT_AUTHORISATION_CODE_LIFETIME_SECONDS
    )
    assert (
        options.refresh_token_lifetime_seconds == DEFAULT_REFRESH_TOKEN_LIFETIME_SECONDS
    )
    assert options.refresh_tokens == RefreshTokenStoragePolicy()


def test_auth_provider_options_require_issuer_when_enabled() -> None:
    with pytest.raises(ProviderConfigurationError):
        OAuthProviderOptions(enabled=True)

    with pytest.raises(ProviderConfigurationError):
        OAuthProviderOptions(enabled=True, issuer=" ")


@pytest.mark.parametrize(
    ("mount_path", "expected"),
    [
        ("oauth", "/oauth"),
        ("oauth/", "/oauth"),
        ("/oauth/", "/oauth"),
        ("/", "/"),
    ],
)
def test_auth_provider_options_normalise_mount_path(
    mount_path: str,
    expected: str,
) -> None:
    options = OAuthProviderOptions(
        issuer="https://auth.example",
        mount_path=mount_path,
    )

    assert options.issuer == "https://auth.example"
    assert options.mount_path == expected


@pytest.mark.parametrize(
    ("mount_path", "message"),
    [
        ("", "mount_path must not be blank"),
        (" ", "mount_path must not be blank"),
        ("///", "must not contain only slashes"),
    ],
)
def test_auth_provider_rejects_unsafe_mount_paths(
    mount_path: str,
    message: str,
) -> None:
    with pytest.raises(ProviderConfigurationError, match=message):
        OAuthProviderOptions(mount_path=mount_path)


def test_auth_provider_refresh_token_policy_defaults() -> None:
    policy = RefreshTokenStoragePolicy()

    assert policy.verifier_kind == "keyed-hash"
    assert policy.rotate_on_use is True
    assert policy.reuse_action == "revoke-token-family"


def test_auth_provider_allows_quarantine_token_family_reuse_action() -> None:
    policy = RefreshTokenStoragePolicy(reuse_action="quarantine-token-family")

    assert policy.reuse_action == "quarantine-token-family"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"verifier_kind": "plaintext"},
        {"rotate_on_use": False},
        {"reuse_action": "ignore"},
    ],
)
def test_auth_provider_rejects_insecure_refresh_token_policy(
    kwargs: dict[str, object],
) -> None:
    with pytest.raises(ProviderConfigurationError):
        match kwargs:
            case {"verifier_kind": verifier_kind}:
                RefreshTokenStoragePolicy(verifier_kind=verifier_kind)  # type: ignore[arg-type]
            case {"rotate_on_use": rotate_on_use}:
                RefreshTokenStoragePolicy(rotate_on_use=rotate_on_use)  # type: ignore[arg-type]
            case {"reuse_action": reuse_action}:
                RefreshTokenStoragePolicy(reuse_action=reuse_action)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "field_name",
    [
        "access_token_lifetime_seconds",
        "id_token_lifetime_seconds",
        "authorisation_code_lifetime_seconds",
        "refresh_token_lifetime_seconds",
    ],
)
def test_auth_provider_rejects_non_positive_lifetimes(field_name: str) -> None:
    with pytest.raises(ProviderConfigurationError):
        match field_name:
            case "access_token_lifetime_seconds":
                OAuthProviderOptions(access_token_lifetime_seconds=0)
            case "id_token_lifetime_seconds":
                OAuthProviderOptions(id_token_lifetime_seconds=0)
            case "authorisation_code_lifetime_seconds":
                OAuthProviderOptions(authorisation_code_lifetime_seconds=0)
            case "refresh_token_lifetime_seconds":
                OAuthProviderOptions(refresh_token_lifetime_seconds=0)


def test_auth_provider_contract_values_are_host_neutral_and_defaulted() -> None:
    subject = ProviderSubject(id="user-1", email="user@example.test")
    client = OAuthClient(
        id="client-1",
        redirect_uris=("https://client.example/callback",),
        allowed_scopes=frozenset({"profile", "email"}),
    )

    assert subject.id == "user-1"
    assert subject.active is True
    assert subject.email == "user@example.test"
    assert subject.display_name is None

    assert client.id == "client-1"
    assert client.is_confidential is True
    assert client.redirect_uris == ("https://client.example/callback",)
    assert client.allowed_scopes == frozenset({"profile", "email"})

    default_subject = ProviderSubject(id="user-2")

    assert default_subject.active is True
    assert default_subject.email is None
    assert default_subject.display_name is None


def test_auth_provider_contract_values_are_frozen() -> None:
    subject = ProviderSubject(id="user-1")
    client = OAuthClient(
        id="client-1",
        redirect_uris=("https://client.example/callback",),
        allowed_scopes=frozenset({"profile"}),
    )

    with pytest.raises(_frozen_instance_error()):
        _assign_attribute(subject, "id", "other-user")

    with pytest.raises(_frozen_instance_error()):
        _assign_attribute(client, "id", "other-client")


def test_refresh_token_consume_contract_signals_state_transition() -> None:
    hints = get_type_hints(RefreshTokenStore.mark_refresh_token_consumed)

    assert hints["return"] is bool
