from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from fastapi import FastAPI

def custom_swagger_ui_html(*, openapi_url: str, title: str, swagger_js_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js", swagger_css_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css", swagger_favicon_url: str = "/static/logo.png", oauth2_redirect_url: str = None, init_oauth: dict = None, swagger_ui_parameters: dict = None) -> HTMLResponse:
    html = get_swagger_ui_html(
        openapi_url=openapi_url,
        title=title,
        swagger_js_url=swagger_js_url,
        swagger_css_url=swagger_css_url,
        swagger_favicon_url=swagger_favicon_url,
        oauth2_redirect_url=oauth2_redirect_url,
        init_oauth=init_oauth,
        swagger_ui_parameters=swagger_ui_parameters
    )
    # Inject custom logo and styles
    custom_logo = '<img src="/static/logo.png" alt="Political Campaign Logo" class="custom-logo" style="max-width: 100px; margin: 10px;">'
    custom_styles = """
    <style>
        .custom-logo { max-width: 100px; margin: 10px; }
        .swagger-ui .topbar { background-color: #1a3c34; }
        .swagger-ui .topbar a { color: #ffffff; }
    </style>
    """
    html_content = html.body.decode()
    html_content = html_content.replace('</head>', custom_styles + '</head>')
    html_content = html_content.replace('<div id="swagger-ui"></div>', custom_logo + '<div id="swagger-ui"></div>')
    return HTMLResponse(content=html_content)

# Update FastAPI app to use custom Swagger UI
def configure_custom_swagger(app: FastAPI):
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui():
        return custom_swagger_ui_html(
            openapi_url=app.openapi_url,
            title="Political Campaign API - Swagger UI",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_favicon_url="/static/logo.png"
        )

    @app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
    async def swagger_ui_redirect():
        from fastapi.openapi.docs import get_swagger_ui_oauth2_redirect_html
        return get_swagger_ui_oauth2_redirect_html()