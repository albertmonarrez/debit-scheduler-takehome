from werkzeug.wrappers import Request
from werkzeug.exceptions import HTTPException, NotFound
from urls import url_patterns


class App:

    def __init__(self):
        self.url_map = url_patterns

    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            if callable(endpoint):
                return endpoint(request, **values)
            return getattr(self, f"on_{endpoint}")(request, **values)
        except NotFound as error:
            return self.error_404(error)
        except HTTPException as e:
            return e

    def error_404(self, exc):
        """Doesn't do anything useful yet other than re-raise
        the 404."""
        raise exc

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)


def create_app():
    application = App()
    return application


if __name__ == '__main__':
    from werkzeug.serving import run_simple

    app = create_app()
    run_simple('0.0.0.0', 5000, app, use_debugger=True, use_reloader=True)
