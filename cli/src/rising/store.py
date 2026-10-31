"""What `rising` keeps on disk: the login in the user's config directory and, beside the
learner's code, the exercise that folder holds."""

import json
import os
from pathlib import Path

import platformdirs

WORKSPACE = ".rising.json"


def credentials_path() -> Path:
    return platformdirs.user_config_path("rising") / "credentials.json"


def save_credentials(url: str, token: str, expires_at: int) -> None:
    path = credentials_path()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Create the temporary file private so no other user can read the token.
    partial = path.with_suffix(".tmp")
    fd = os.open(partial, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as file:
        json.dump({"url": url, "token": token, "expiresAt": expires_at}, file)
    partial.replace(path)


def load_credentials() -> dict[str, object] | None:
    try:
        data = json.loads(credentials_path().read_text())
    except OSError, ValueError:
        return None
    if (
        isinstance(data, dict)
        and isinstance(data.get("url"), str)
        and isinstance(data.get("token"), str)
    ):
        return data
    return None


def delete_credentials() -> None:
    credentials_path().unlink(missing_ok=True)


def save_workspace(exercise: str, file: str) -> None:
    Path(WORKSPACE).write_text(json.dumps({"exercise": exercise, "file": file}) + "\n")


def load_workspace() -> tuple[str, Path] | None:
    try:
        data = json.loads(Path(WORKSPACE).read_text())
        return data["exercise"], Path(data["file"])
    except OSError, ValueError, KeyError, TypeError:
        return None
