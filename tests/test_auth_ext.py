import ast
import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from auth_ext import (
    ERROR_ALREADY_EXISTS,
    ERROR_INVALID_PASSWORD,
    ERROR_PASSWORD_TOO_SHORT,
    ERROR_PASSWORD_TOO_WEAK,
    ChallengeDecision,
    ChallengeKind,
    ChallengeRecord,
    DefaultPasswordPolicy,
    IdentityOptions,
    NoChallengePolicy,
    PasswordStrength,
    PrimaryAuthenticationContext,
    Result,
    RouteReplacement,
    RouterExtensionPlan,
    complete_challenge,
)
from auth_ext.manager import public_password_failure_message


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


def test_auth_ext_result_carries_success_values_and_failure_reason() -> None:
    result = Result.ok({"id": "user-1"})

    assert result.is_ok() is True
    assert result.is_failure() is False
    assert result.value == {"id": "user-1"}
    assert result.error_type is None

    failure = Result.failure(ERROR_ALREADY_EXISTS, "Already exists.")

    assert failure.is_failure() is True
    assert failure.is_ok() is False
    assert failure.error_type == ERROR_ALREADY_EXISTS
    assert failure.message == "Already exists."
    assert failure.value is None

    empty_success = Result.ok()

    assert empty_success.is_ok() is True
    assert empty_success.is_failure() is False
    assert empty_success.value is None
    assert empty_success.error_type is None


def test_auth_ext_default_password_policy_scores_and_accepts_passphrases() -> None:
    policy = DefaultPasswordPolicy()

    strength = policy.strength("correct horse")
    validation = policy.validate("correct horse")

    assert strength.score >= policy.minimum_score
    assert strength.label in {"fair", "good", "strong"}
    assert validation.is_ok() is True


@pytest.mark.parametrize(
    ("password", "error_type"),
    [
        ("   ", ERROR_INVALID_PASSWORD),
        ("short 1", ERROR_PASSWORD_TOO_SHORT),
        ("admin password 123!", ERROR_PASSWORD_TOO_WEAK),
        ("changeme 123!", ERROR_PASSWORD_TOO_WEAK),
        ("changeit 123!", ERROR_PASSWORD_TOO_WEAK),
        ("p4ssw0rd 123!", ERROR_PASSWORD_TOO_WEAK),
        ("pass phrase 123!", ERROR_PASSWORD_TOO_WEAK),
        ("tester account 123!", ERROR_PASSWORD_TOO_WEAK),
        ("test account 123!", ERROR_PASSWORD_TOO_WEAK),
        ("abcdefghijkl", ERROR_PASSWORD_TOO_WEAK),
    ],
)
def test_auth_ext_default_password_policy_rejects_invalid_values(
    password: str,
    error_type: str,
) -> None:
    result = DefaultPasswordPolicy().validate(password)

    assert result.is_failure() is True
    assert result.error_type == error_type
    assert result.message


@pytest.mark.parametrize(
    ("password", "user"),
    [
        (
            "signup 12345!",
            SimpleNamespace(email="signup@example.com"),
        ),
        (
            "operator 123!",
            SimpleNamespace(display_name="Operator Example"),
        ),
        (
            "david 123456!",
            SimpleNamespace(preferred_name="David"),
        ),
        (
            "identity 123!",
            SimpleNamespace(username="identity-admin"),
        ),
    ],
)
def test_auth_ext_default_password_policy_rejects_account_detail_fragments(
    password: str,
    user: object,
) -> None:
    result = DefaultPasswordPolicy().validate(password, user)

    assert result.is_failure() is True
    assert result.error_type == ERROR_PASSWORD_TOO_WEAK
    assert result.message


def test_auth_ext_identity_options_accept_custom_password_policy() -> None:
    class RejectingPasswordPolicy:
        def strength(
            self,
            password: str,
            user: object | None = None,
        ) -> PasswordStrength:
            del password, user
            return PasswordStrength(
                score=0.0,
                label="weak",
                feedback=("Rejected by custom policy.",),
            )

        def validate(
            self,
            password: str,
            user: object | None = None,
        ) -> Result[str]:
            del password, user
            return Result.failure(
                ERROR_PASSWORD_TOO_WEAK,
                "Rejected by custom policy.",
            )

    options = IdentityOptions(password_policy=RejectingPasswordPolicy())
    validation = options.resolved_password_policy().validate("correct horse")

    assert validation.is_failure() is True
    assert validation.error_type == ERROR_PASSWORD_TOO_WEAK
    assert validation.message == "Rejected by custom policy."


def test_auth_ext_password_failure_message_filters_unrecognised_reasons() -> None:
    assert (
        public_password_failure_message(
            "Internal breach provider matched tenant-specific denylist."
        )
        == "Password is invalid."
    )
    assert (
        public_password_failure_message(
            "Password does not meet the strength requirement."
        )
        == "Password does not meet the strength requirement."
    )


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
