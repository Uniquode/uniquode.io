from fastapi import Request
from wybra.template import render_page


async def home(request: Request):
    return render_page(
        request,
        "public/pages/home.html",
    )
