"""The `rising` command."""

import argparse
import os
import sys
import time
import zoneinfo
from pathlib import Path

from rising import exercise, grade, store
from rising.client import ApiError, Client

DEFAULT_URL = "https://learn.rising.sh"
# The XP a passing exercise claims. The site caps it per event and per day.
XP_PER_EXERCISE = 10
SIGN_IN = "Ejecuta `rising login` para iniciar sesión."


def signed_in() -> Client:
    saved = store.load_credentials()
    if not saved:
        raise ApiError(0, "signed_out", SIGN_IN)
    return Client(str(saved["url"]), str(saved["token"]))


def login(args: argparse.Namespace) -> int:
    client = Client(args.url or os.environ.get("RISING_URL", DEFAULT_URL))
    codes = client.request("POST", "/auth/device/code")
    print(f"Abre esta dirección en tu navegador:\n\n    {codes['verificationUriComplete']}\n")
    print(f"Inicia sesión si hace falta y comprueba que el código sea {codes['userCode']}.")
    print("Esperando la aprobación...")
    interval = codes["interval"]
    deadline = time.monotonic() + codes["expiresIn"]
    while time.monotonic() < deadline:
        time.sleep(interval)
        try:
            grant = client.request(
                "POST", "/auth/device/token", {"deviceCode": codes["deviceCode"]}
            )
        except ApiError as e:
            if e.reason == "authorization_pending":
                continue
            if e.reason == "slow_down":
                interval = max(interval, e.retry_after)
                continue
            if e.reason == "access_denied":
                raise ApiError(
                    e.status, e.reason, "Rechazaste el acceso desde el navegador."
                ) from None
            raise
        store.save_credentials(client.url, grant["token"], grant["expiresAt"])
        print("Sesión iniciada.")
        return 0
    raise ApiError(0, "expired_code", "El código venció. Ejecuta `rising login` otra vez.")


def logout(_: argparse.Namespace) -> int:
    saved = store.load_credentials()
    if not saved:
        print("No había una sesión iniciada.")
        return 0
    # The token is deleted here only once the site has revoked it.
    signed_in().request("POST", "/auth/logout")
    store.delete_credentials()
    print("Sesión cerrada.")
    return 0


def pull(args: argparse.Namespace) -> int:
    if not exercise.ID.fullmatch(args.exercise):
        raise ApiError(
            0, "bad_id", "El ejercicio se escribe lección/ejercicio, como p1-quickstart/ghz."
        )
    saved = store.load_credentials()
    client = Client(str(saved["url"]) if saved else os.environ.get("RISING_URL", DEFAULT_URL))
    block = exercise.fetch(client, args.exercise)
    code = exercise.write(args.exercise, block, args.force)
    print(
        f"Escribí {code} y {exercise.STATEMENT}. Lee el enunciado, edita {code} y ejecuta `rising test`."
    )
    return 0


def graded() -> tuple[str, dict[str, object]]:
    here = store.load_workspace()
    if not here:
        raise ApiError(
            0, "no_exercise", "Aquí no hay un ejercicio. Ejecuta `rising pull lección/ejercicio`."
        )
    name, file = here
    try:
        code = Path(file.name).read_text(encoding="utf-8")
    except OSError:
        raise ApiError(0, "no_file", f"No se encontró {file.name}.") from None
    result = grade.run(name, code)
    grade.show(result)
    return name, result


def test(_: argparse.Namespace) -> int:
    return 0 if graded()[1]["passed"] else 1


def local_zone() -> str | None:
    """The IANA name of this machine's time zone, if it can be read."""
    name = os.environ.get("TZ", "").lstrip(":")
    if not name:
        try:
            name = os.readlink("/etc/localtime").partition("zoneinfo/")[2]
        except OSError:
            return None
    try:
        zoneinfo.ZoneInfo(name)
    except zoneinfo.ZoneInfoNotFoundError, ValueError:
        return None
    return name


def submit(_: argparse.Namespace) -> int:
    client = signed_in()
    name, result = graded()
    if not result["passed"]:
        return 1
    award = {"source": "cli", "ref": name.replace("/", ":"), "amount": XP_PER_EXERCISE}
    if zone := local_zone():
        award["tz"] = zone
    reply = client.request("POST", "/api/xp", award)
    if reply["granted"]:
        print(f"+{reply['granted']} XP. Hoy llevas {reply['total']} de {reply['cap']}.")
    elif reply["reason"] == "ref_today":
        print("Ya ganaste XP por este ejercicio hoy. Vuelve mañana por más.")
    else:
        print(f"Llegaste al tope de {reply['cap']} XP de hoy. Vuelve mañana.")
    return 0


def status(_: argparse.Namespace) -> int:
    client = signed_in()
    streak = client.request("GET", "/api/streak")
    xp = client.request("GET", "/api/xp")
    board = client.request("GET", "/api/board")
    days = lambda n: f"{n} día" if n == 1 else f"{n} días"  # noqa: E731
    print(f"Racha: {days(streak['current'])} (la mejor: {days(streak['longest'])})")
    print("Hoy ya ganaste XP." if streak["today"] else "Hoy todavía no ganas XP.")
    print(f"XP de hoy: {xp['total']} de {xp['cap']}")
    print(f"\nTablero de la semana del {board['weekStart']}:")
    for entry in board["entries"]:
        who = "tú" if entry["you"] else f"amigo {entry['id']}"
        print(f"  {entry['rank']}. {who:<10} {entry['xp']} XP")
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="rising", description="Ejercicios de Rising en tu terminal."
    )
    commands = root.add_subparsers(dest="command", required=True)
    one = commands.add_parser("login", help="inicia sesión con el navegador")
    one.add_argument("--url", help=f"el sitio (por defecto {DEFAULT_URL})")
    one.set_defaults(run=login)
    commands.add_parser("logout", help="cierra la sesión y revoca el token").set_defaults(
        run=logout
    )
    one = commands.add_parser("pull", help="escribe un ejercicio en esta carpeta")
    one.add_argument("exercise", help="lección/ejercicio, como p1-quickstart/ghz")
    one.add_argument("--force", action="store_true", help="reemplaza lo que ya existe")
    one.set_defaults(run=pull)
    commands.add_parser("test", help="comprueba tu código").set_defaults(run=test)
    commands.add_parser("submit", help="comprueba tu código y registra el XP").set_defaults(
        run=submit
    )
    commands.add_parser("status", help="tu racha, tu XP y el tablero").set_defaults(run=status)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    # `login` waits for minutes: a pipe must see its URL and code at once.
    sys.stdout.reconfigure(line_buffering=True)
    try:
        return int(args.run(args))
    except ApiError as e:
        if e.reason == "token_invalid":
            print(f"error: {e} {SIGN_IN}", file=sys.stderr)
        else:
            print(f"error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
