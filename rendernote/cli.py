"""The rendernote command.

  rendernote SCORE.ly [-o OUT.html] [--files]   build the page next to the score
  rendernote serve SCORE.ly [--port N]          serve it on your Wi-Fi, rebuilding on save
"""
import argparse, glob, http.server, os, re, socket, sys, threading, time

from .build import build


def wifi_address():
    """This computer's address on the local network (no traffic is sent)."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(("192.0.2.1", 9))
            return s.getsockname()[0]
        except OSError:
            return "127.0.0.1"


def watched(score):
    folder = os.path.dirname(os.path.abspath(score))
    return {p: os.path.getmtime(p) for p in glob.glob(os.path.join(folder, "*.ly")) + glob.glob(os.path.join(folder, "*.ily"))}


def serve(score, port):
    page = build(score)
    print(f"Built {page}")
    state = {"page": page}

    def rebuild_loop():
        seen = watched(score)
        while True:
            time.sleep(0.5)
            now = watched(score)
            if now != seen:
                seen = now
                try:
                    state["page"] = build(score)
                    print(time.strftime("%H:%M:%S"), "rebuilt", flush=True)
                except SystemExit as e:
                    print(e, flush=True)

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.startswith("/__build"):
                m = re.search(rb'"build":"([^"]*)"', open(state["page"], "rb").read())
                body, kind = (m.group(1) if m else b""), "text/plain"
            else:
                body, kind = open(state["page"], "rb").read(), "text/html; charset=utf-8"
            self.send_response(200)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    threading.Thread(target=rebuild_loop, daemon=True).start()
    server = http.server.ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"Open http://{wifi_address()}:{server.server_port}/ on any device on this Wi-Fi "
          f"(or http://localhost:{server.server_port}/ here). Ctrl-C to stop.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "serve":
        p = argparse.ArgumentParser(prog="rendernote serve")
        p.add_argument("score")
        p.add_argument("--port", type=int, default=8000)
        a = p.parse_args(argv[1:])
        serve(a.score, a.port)
        return
    p = argparse.ArgumentParser(prog="rendernote", description="Turn a LilyPond score into one playable HTML file.")
    p.add_argument("score")
    p.add_argument("-o", "--out", help="where to write the page (default: <Title>.html next to the score)")
    p.add_argument("--files", action="store_true", help="also write the PDFs and MIDI next to the page")
    a = p.parse_args(argv)
    print("Wrote", build(a.score, a.out, a.files))
