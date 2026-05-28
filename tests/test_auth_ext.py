import ast
import asyncio
from datetime import UTC, datetime, timedelta
from importlib import import_module
from pathlib import Path

import auth_ext
from auth_ext import (
    AccountCreationPolicy,
    AdvancedAuthenticationPolicy,
    ChallengeDecision,
    ChallengeKind,
    ChallengeRecord,
    ChallengeStore,
    ConfigurationError,
    IdentityDelivery,
    IdentityIntegration,
    IdentityOptions,
    NoChallengePolicy,
    NullIdentityDelivery,
    PrimaryAuthenticationContext,
    RecoveryCodeStore,
    RouteReplacement,
    RouterExtensionPlan,
    TOTPCredentialStore,
    UserCreate,
    UserRead,
    UserUpdate,
    WebAuthnCredentialStore,
    complete_challenge,
    is_generate_local_identity_secret,
)
from auth_ext.sqlalchemy import AccessToken, OAuthAccount, User


class MemoryChallengeStore:
    def __init__(self) -> None:
        self.records: dict[str, ChallengeRecord] = {}
        self.consumed: list[str] = []

    async def create_challenge(
        self,
        user_id: str,
        kind: ChallengeKind,
        expires_at: datetime,
        metadata: dict[str, object] | None = None,
    ) -> ChallengeRecord:
        record = ChallengeRecord(
            id=f"challenge-{len(self.records) + 1}",
            user_id=user_id,
            kind=kind,
            expires_at=expires_at,
            metadata=dict(metadata or {}),
        )
        self.records[record.id] = record
        return record

    async def get_challenge(self, challenge_id: str) -> ChallengeRecord | None:
        return self.records.get(challenge_id)

    async def consume_challenge(self, challenge_id: str) -> None:
        self.consumed.append(challenge_id)
        self.records.pop(challenge_id, None)


def test_auth_ext_package_is_independent_from_application_modules() -> None:
    source_root = Path(__file__).resolve().parents[1] / "src"

    for package_name in ("auth_ext", "auth_provider"):
        for path in (source_root / package_name).rglob("*.py"):
            tree = ast.parse(path.read_text(), filename=str(path))
            imported_modules = {
                alias.name
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            } | {
                node.module
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module is not None
            }
            assert not any(
                module == "uniquode" or module.startswith("uniquode.")
                for module in imported_modules
            )


def test_auth_ext_top_level_exports_curated_storage_agnostic_api() -> None:
    assert set(auth_ext.__all__) == {
        "AccountCreationPolicy",
        "AdvancedAuthenticationPolicy",
        "ChallengeDecision",
        "ChallengeKind",
        "ChallengeRecord",
        "ChallengeStore",
        "ConfigurationError",
        "IdentityDelivery",
        "IdentityIntegration",
        "IdentityOptions",
        "NoChallengePolicy",
        "NullIdentityDelivery",
        "PrimaryAuthenticationContext",
        "RecoveryCodeStore",
        "RouteReplacement",
        "RouterExtensionPlan",
        "TOTPCredentialStore",
        "UserCreate",
        "UserRead",
        "UserUpdate",
        "WebAuthnCredentialStore",
        "complete_challenge",
        "is_generate_local_identity_secret",
    }


def test_auth_ext_top_level_exports_resolve_to_expected_objects() -> None:
    expected_objects = {
        "AccountCreationPolicy": AccountCreationPolicy,
        "AdvancedAuthenticationPolicy": AdvancedAuthenticationPolicy,
        "ChallengeDecision": ChallengeDecision,
        "ChallengeKind": ChallengeKind,
        "ChallengeRecord": ChallengeRecord,
        "ChallengeStore": ChallengeStore,
        "ConfigurationError": ConfigurationError,
        "IdentityDelivery": IdentityDelivery,
        "IdentityIntegration": IdentityIntegration,
        "IdentityOptions": IdentityOptions,
        "NoChallengePolicy": NoChallengePolicy,
        "NullIdentityDelivery": NullIdentityDelivery,
        "PrimaryAuthenticationContext": PrimaryAuthenticationContext,
        "RecoveryCodeStore": RecoveryCodeStore,
        "RouteReplacement": RouteReplacement,
        "RouterExtensionPlan": RouterExtensionPlan,
        "TOTPCredentialStore": TOTPCredentialStore,
        "UserCreate": UserCreate,
        "UserRead": UserRead,
        "UserUpdate": UserUpdate,
        "WebAuthnCredentialStore": WebAuthnCredentialStore,
        "complete_challenge": complete_challenge,
        "is_generate_local_identity_secret": is_generate_local_identity_secret,
    }

    assert {
        name: getattr(auth_ext, name) for name in auth_ext.__all__
    } == expected_objects


def test_auth_ext_sqlalchemy_exports_adapter_specific_models() -> None:
    assert not {"AccessToken", "OAuthAccount", "User"} & set(auth_ext.__all__)

    sqlalchemy_adapter = import_module("auth_ext.sqlalchemy")
    assert sqlalchemy_adapter.AccessToken is AccessToken
    assert sqlalchemy_adapter.OAuthAccount is OAuthAccount
    assert sqlalchemy_adapter.User is User


def test_auth_ext_no_challenge_policy_allows_direct_login() -> None:
    async def assert_policy() -> None:
        decision = await NoChallengePolicy().after_primary_authentication(
            PrimaryAuthenticationContext(user_id="user-1"),
            MemoryChallengeStore(),
        )

        assert isinstance(decision, ChallengeDecision)
        assert decision.requires_challenge is False
        assert decision.challenge is None

    asyncio.run(assert_policy())


def test_auth_ext_challenge_completion_consumes_existing_challenge() -> None:
    async def assert_challenge_completion() -> None:
        store = MemoryChallengeStore()
        challenge = await store.create_challenge(
            user_id="user-1",
            kind="totp",
            expires_at=datetime.now(UTC) + timedelta(minutes=5),
        )

        assert await complete_challenge(store, challenge.id) is True
        assert challenge.id in store.consumed
        assert await complete_challenge(store, challenge.id) is False

    asyncio.run(assert_challenge_completion())


def test_auth_ext_router_extension_plan_tracks_explicit_replacements() -> None:
    plan = RouterExtensionPlan(
        additive_route_names=("auth_ext:challenge",),
        replacements=(
            RouteReplacement(
                method="POST",
                path="/login",
                reason="Pause primary login for MFA challenge.",
            ),
        ),
    )

    assert plan.replaces("post", "/login") is True
    assert plan.replaces("GET", "/login") is False
