from fastapi import Request
from wybra.web.context import TemplateContext, add_to_context


def get_context(_request: Request, context: TemplateContext) -> TemplateContext:
    return context.with_values(
        page_title="uniquode",
    )


add_to_context(get_context)
