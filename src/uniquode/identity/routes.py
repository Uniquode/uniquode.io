from dataclasses import dataclass

from fastapi import APIRouter, Request

from uniquode.identity.users import resolve_current_user
from uniquode.identity.views import (
    AccountPageView,
    LoginPageView,
    LoginSubmitView,
    LogoutPageView,
    LogoutSubmitView,
    PasswordResetConfirmView,
    PasswordResetPageView,
    PasswordResetRequestView,
    VerificationConfirmView,
    VerificationPageView,
    VerificationRequestView,
)
from uniquode.web.dispatcher import HtmlRouteDefinition
from uniquode.web.route_contract import API_PATH_PREFIX


@dataclass(frozen=True, slots=True)
class IdentityRouteSet:
    page_routes: tuple[HtmlRouteDefinition, ...]
    api_router: APIRouter


async def current_user_state(request: Request) -> dict[str, object]:
    user = await resolve_current_user(request)
    if user is None:
        return {"authenticated": False}

    return {
        "authenticated": True,
        "email": user.email,
        # Keep this optional state endpoint out of authorisation decisions.
        "is_verified": user.is_verified,
    }


def build_identity_route_set() -> IdentityRouteSet:
    normalised_api_prefix = API_PATH_PREFIX.rstrip("/")
    api_router = APIRouter(prefix=f"{normalised_api_prefix}/identity")
    api_router.add_api_route(
        "/current-user",
        current_user_state,
        methods=["GET"],
        include_in_schema=False,
        name="identity:api:current-user",
    )

    return IdentityRouteSet(
        page_routes=(
            HtmlRouteDefinition(
                path="/login",
                name="identity:login",
                methods=("GET",),
                surface="page",
                view=LoginPageView(),
            ),
            HtmlRouteDefinition(
                path="/login",
                name="identity:login-submit",
                methods=("POST",),
                surface="page",
                view=LoginSubmitView(),
            ),
            HtmlRouteDefinition(
                path="/logout",
                name="identity:logout-page",
                methods=("GET",),
                surface="page",
                view=LogoutPageView(),
            ),
            HtmlRouteDefinition(
                path="/logout",
                name="identity:logout",
                methods=("POST",),
                surface="page",
                view=LogoutSubmitView(),
            ),
            HtmlRouteDefinition(
                path="/account",
                name="identity:account",
                methods=("GET",),
                surface="page",
                view=AccountPageView(),
            ),
            HtmlRouteDefinition(
                path="/password/reset",
                name="identity:password-reset",
                methods=("GET",),
                surface="page",
                view=PasswordResetPageView(),
            ),
            HtmlRouteDefinition(
                path="/password/reset",
                name="identity:password-reset-request",
                methods=("POST",),
                surface="page",
                view=PasswordResetRequestView(),
            ),
            HtmlRouteDefinition(
                path="/password/reset/confirm",
                name="identity:password-reset-confirm",
                methods=("POST",),
                surface="page",
                view=PasswordResetConfirmView(),
            ),
            HtmlRouteDefinition(
                path="/verify",
                name="identity:verify",
                methods=("GET",),
                surface="page",
                view=VerificationPageView(),
            ),
            HtmlRouteDefinition(
                path="/verify",
                name="identity:verify-request",
                methods=("POST",),
                surface="page",
                view=VerificationRequestView(),
            ),
            HtmlRouteDefinition(
                path="/verify/confirm",
                name="identity:verify-confirm",
                methods=("POST",),
                surface="page",
                view=VerificationConfirmView(),
            ),
        ),
        api_router=api_router,
    )
