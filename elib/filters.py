from __future__ import annotations

from markupsafe import Markup
from flask import Flask

from .utils import markdown_to_html_safe


def register_filters(app: Flask) -> None:


    @app.template_filter("markdown")
    def _markdown_filter(text: str) -> Markup:
        html = markdown_to_html_safe(text or "")
        return Markup(html)
