from http.server import SimpleHTTPRequestHandler, HTTPServer

class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

PORT = 8000  # Change if needed
server = HTTPServer(("0.0.0.0", PORT), NoCacheHandler)
print(f"Serving at http://127.0.0.1:{PORT}")
server.serve_forever()
