from dataclasses import dataclass
from typing import Any, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from uniquode.identity.delivery import IdentityDelivery
from uniquode.identity.options import IdentityOptions
from uniquode.identity.schemas import UserCreate
from uniquode.identity.users import create_user_manager
from uniquode.models import User


@dataclass(frozen=True, slots=True)
class InitialAdminCredentials:
    email: str
    password: str


@dataclass(frozen=True, slots=True)
class InitialAdminBootstrapResult:
    created: bool
    user: User


async def find_administrative_user(session: AsyncSession) -> User | None:
    is_superuser = cast(Any, User.is_superuser)
    result = await session.execute(select(User).where(is_superuser.is_(True)).limit(1))
    return result.scalar_one_or_none()


async def bootstrap_initial_admin(
    session: AsyncSession,
    options: IdentityOptions,
    credentials: InitialAdminCredentials,
    delivery: IdentityDelivery | None = None,
) -> InitialAdminBootstrapResult:
    existing_admin = await find_administrative_user(session)
    if existing_admin is not None:
        return InitialAdminBootstrapResult(created=False, user=existing_admin)

    manager = create_user_manager(session, options, delivery)
    user = await manager.create(
        UserCreate(
            email=credentials.email,
            password=credentials.password,
            is_superuser=True,
            is_verified=True,
        ),
        safe=False,
    )
    return InitialAdminBootstrapResult(created=True, user=user)
