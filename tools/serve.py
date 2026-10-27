"""Serves site/ and grades the code exercises on this machine.

    uv run python tools/serve.py [port]

It is `python -m http.server` plus `POST /run`, which the exercise editor calls with
{"exercise": id, "code": text, "mode": "run"|"check"} and gets the result of qgcheck.grade.
It listens only on 127.0.0.1 and runs the code in a process of your user, with no further isolation:
it is for practising on your machine, not for exposing to a network.
The `error` texts of the replies are in Spanish: the editor shows them to the learner.
"""

import io
import json
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from qgcheck import grade  # noqa: E402
from qgcheck.runner import MAX_CODE  # noqa: E402

PORT = 8810


class Handler(SimpleHTTPRequestHandler):
    def reply(self, status: int, body: dict[str, Any]) -> None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        if self.path != "/run":
            return self.reply(404, {"error": "No existe."})
        # Another website could send the POST from the learner's browser: application/json forces
        # a preflight request that this server does not answer, and Host prevents DNS rebinding.
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0]
        if (
            host not in ("localhost", "127.0.0.1")
            or self.headers.get("Content-Type") != "application/json"
        ):
            return self.reply(403, {"error": "Petición no permitida."})
        size = int(self.headers.get("Content-Length") or 0)
        if size > 2 * MAX_CODE:
            return self.reply(413, {"error": "El código es demasiado largo."})
        try:
            req = json.loads(self.rfile.read(size))
            result = grade(req["exercise"], req["code"], req.get("mode", "check"))
        except (ValueError, KeyError, TypeError) as exc:
            return self.reply(400, {"error": f"Petición inválida: {exc}"})
        self.reply(200, result)


def main() -> None:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    server = ThreadingHTTPServer(
        ("127.0.0.1", port), partial(Handler, directory=str(ROOT / "site"))
    )
    print(f"Course at http://localhost:{port}/")
    server.serve_forever()


if __name__ == "__main__":
    main()
