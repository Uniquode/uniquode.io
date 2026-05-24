from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

from fastapi import Request
from fastapi.responses import RedirectResponse, Response
from starlette.datastructures import FormData

from uniquode.identity.users import (
    authenticate_user,
    clear_session_cookie,
    create_session_token,
    destroy_session_token,
    request_password_reset,
    request_verification,
    reset_password,
    resolve_current_user,
    set_session_cookie,
    verify_user,
)
from uniquode.web.csrf import request_form_data
from uniquode.web.dispatcher import HtmlView
from uniquode.web.renderer import TemplateRenderer
from uniquode.web.theme import theme_template_context


def _identity_context(request: Request, **extra: Any) -> dict[str, Any]:
    return (
        theme_template_context(request)
        | {
            "theme_update_path": request.url_for("public:partial:theme-mode"),
            "theme_return_path": request.url.path,
        }
        | extra
    )


def _form_value(form_data: FormData, name: str, default: str = "") -> str:
    value = form_data.get(name, default)
    return value if isinstance(value, str) else default


def normalise_return_to(value: str | None, default: str = "/account") -> str:
    candidate = (value or "").strip()
    if (
        not candidate.startswith("/")
        or candidate.startswith("//")
        or "\\" in candidate
        or "\r" in candidate
        or "\n" in candidate
    ):
        return default

    parsed = urlsplit(candidate)
    if parsed.scheme or parsed.netloc:
        return default

    return candidate


@dataclass(frozen=True, slots=True)
class LoginPageView(HtmlView):
    template_name: str = "identity/pages/login.html"

    async def render(self, request: Request, renderer: TemplateRenderer) -> Response:
        context = _identity_context(
            request,
            page_title="Sign in",
            return_to=normalise_return_to(request.query_params.get("return_to")),
        )
        return renderer.render_page(self.template_name, request, context)


@dataclass(frozen=True, slots=True)
class LoginSubmitView(HtmlView):
    template_name: str = "identity/pages/login.html"

    async def render(self, request: Request, renderer: TemplateRenderer) -> Response:
        form_data = await request_form_data(request)
        email = _form_value(form_data, "email").strip()
        password = _form_value(form_data, "password")
        return_to = normalise_return_to(_form_value(form_data, "return_to"))

        user = await authenticate_user(request, email, password)
        if user is None:
            context = _identity_context(
                request,
                page_title="Sign in",
                email=email,
                return_to=return_to,
                form_error="Email or password is incorrect.",
            )
            return renderer.render_page(
                self.template_name,
                request,
                context,
                status_code=401,
            )

        token = await create_session_token(request, user)
        response = RedirectResponse(url=return_to, status_code=303)
        set_session_cookie(response, token, request.app.state.settings.identity_options)
        return response


@dataclass(frozen=True, slots=True)
class LogoutSubmitView(HtmlView):
    async def render(self, request: Request, renderer: TemplateRenderer) -> Response:
        await destroy_session_token(request)
        response = RedirectResponse(url="/", status_code=303)
        clear_session_cookie(response, request.app.state.settings.identity_options)
        return response


@dataclass(frozen=True, slots=True)
class LogoutPageView(HtmlView):
    template_name: str = "identity/pages/logout.html"

    async def render(self, request: Request, renderer: TemplateRenderer) -> Response:
        context = _identity_context(request, page_title="Sign out")
        return renderer.render_page(self.template_name, request, context)


@dataclass(frozen=True, slots=True)
class AccountPageView(HtmlView):
    template_name: str = "identity/pages/account.html"

    async def render(self, request: Request, renderer: TemplateRenderer) -> Response:
        user = await resolve_current_user(request)
        context = _identity_context(
            request,
            page_title="Account",
            current_user=user,
        )
        return renderer.render_page(self.template_name, request, context)


@dataclass(frozen=True, slots=True)
class PasswordResetPageView(HtmlView):
    template_name: str = "identity/pages/password_reset.html"

    async def render(self, request: Request, renderer: TemplateRenderer) -> Response:
        context = _identity_context(request, page_title="Reset password")
        return renderer.render_page(
            self.template_name,
            request,
            context,
        )


@dataclass(frozen=True, slots=True)
class PasswordResetRequestView(HtmlView):
    template_name: str = "identity/pages/password_reset.html"

    async def render(self, request: Request, renderer: TemplateRenderer) -> Response:
        form_data = await request_form_data(request)
        email = _form_value(form_data, "email").strip()
        await request_password_reset(request, email)
        context = _identity_context(
            request,
            page_title="Reset password",
            email=email,
            form_message="If the account exists, a reset link has been queued.",
        )
        return renderer.render_page(
            self.template_name,
            request,
            context,
        )


@dataclass(frozen=True, slots=True)
class PasswordResetConfirmView(HtmlView):
    template_name: str = "identity/pages/password_reset.html"

    async def render(self, request: Request, renderer: TemplateRenderer) -> Response:
        form_data = await request_form_data(request)
        token = _form_value(form_data, "token")
        password = _form_value(form_data, "password")
        did_reset = await reset_password(request, token, password)
        context = _identity_context(
            request,
            page_title="Reset password",
            form_message="Password reset complete." if did_reset else None,
            form_error=None if did_reset else "The reset token is invalid or expired.",
        )
        return renderer.render_page(
            self.template_name,
            request,
            context,
            status_code=200 if did_reset else 400,
        )


@dataclass(frozen=True, slots=True)
class VerificationPageView(HtmlView):
    template_name: str = "identity/pages/verify.html"

    async def render(self, request: Request, renderer: TemplateRenderer) -> Response:
        context = _identity_context(request, page_title="Verify email")
        return renderer.render_page(self.template_name, request, context)


@dataclass(frozen=True, slots=True)
class VerificationRequestView(HtmlView):
    template_name: str = "identity/pages/verify.html"

    async def render(self, request: Request, renderer: TemplateRenderer) -> Response:
        form_data = await request_form_data(request)
        email = _form_value(form_data, "email").strip()
        await request_verification(request, email)
        context = _identity_context(
            request,
            page_title="Verify email",
            email=email,
            form_message=(
                "If the account can be verified, a verification link has been queued."
            ),
        )
        return renderer.render_page(self.template_name, request, context)


@dataclass(frozen=True, slots=True)
class VerificationConfirmView(HtmlView):
    template_name: str = "identity/pages/verify.html"

    async def render(self, request: Request, renderer: TemplateRenderer) -> Response:
        form_data = await request_form_data(request)
        token = _form_value(form_data, "token")
        did_verify = await verify_user(request, token)
        context = _identity_context(
            request,
            page_title="Verify email",
            form_message="Email verification complete." if did_verify else None,
            form_error=(
                None if did_verify else "The verification token is invalid or expired."
            ),
        )
        return renderer.render_page(
            self.template_name,
            request,
            context,
            status_code=200 if did_verify else 400,
        )
