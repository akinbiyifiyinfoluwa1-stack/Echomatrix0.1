from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os

PORT = int(os.getenv("PORT", "8080"))

class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
