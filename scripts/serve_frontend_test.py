"""Serve the static Pages export under its real base path for browser tests."""

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from packages.core.io import ROOT


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "web/out"), **kwargs)

    def do_GET(self):
        if self.path.startswith("/mlspend/"):
            self.path = self.path[len("/mlspend") :]
        super().do_GET()

    def do_HEAD(self):
        self.send_error(405, "The verification server deliberately refuses HEAD")


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 4173), Handler).serve_forever()
