import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

from auth_ext import (
    ChallengeDecision,
    ChallengeKind,
    ChallengeRecord,
    NoChallengePolicy,
    PrimaryAuthenticationContext,
    RouteReplacement,
    RouterExtensionPlan,
    complete_challenge,
)


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
            assert "uniquode" not in path.read_text()


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
