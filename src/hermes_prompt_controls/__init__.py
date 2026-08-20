"""Hermes Prompt Controls plugin."""

from __future__ import annotations

import json
import logging
import os
import shlex
import tempfile
import threading
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_CONFIG_WARNING = "Prompt controls configuration is invalid; request left unchanged."
_SHAPE_WARNING = "Prompt controls request shape is unsupported; request left unchanged."
_USAGE = (
    "Usage: /prompt-controls list | "
    "set global <files...> | set platform <name> <files...> | "
    "set model <name> <files...> | clear global | "
    "clear platform <name> | clear model <name>"
)
_WRITE_LOCK = threading.Lock()


class _ConfigurationError(ValueError):
    pass


class _ShapeError(ValueError):
    pass


def _plugin_home() -> Path:
    hermes_home = Path(os.environ.get("HERMES_HOME") or Path.home() / ".hermes")
    return hermes_home / "prompt-controls"


def _default_config() -> dict[str, Any]:
    return {"global": [], "platforms": {}, "models": {}}


def _validate_directive_name(name: Any) -> str:
    if (
        not isinstance(name, str)
        or not name
        or "/" in name
        or "\\" in name
        or Path(name).name != name
        or Path(name).suffix.lower() != ".md"
    ):
        raise _ConfigurationError
    return name


def _validate_directive_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        raise _ConfigurationError
    return [_validate_directive_name(name) for name in value]


def _validate_mapping(value: Any) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        raise _ConfigurationError
    validated: dict[str, list[str]] = {}
    for key, names in value.items():
        if not isinstance(key, str) or not key:
            raise _ConfigurationError
        validated[key] = _validate_directive_list(names)
    return validated


def _read_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _ConfigurationError from exc
    if not isinstance(value, dict):
        raise _ConfigurationError
    return value


def _load_config(root: Path) -> dict[str, Any]:
    value = _read_json(root / "config.json", _default_config())
    if set(value) - {"global", "platforms", "models"}:
        raise _ConfigurationError
    return {
        "global": _validate_directive_list(value.get("global", [])),
        "platforms": _validate_mapping(value.get("platforms", {})),
        "models": _validate_mapping(value.get("models", {})),
    }


def _load_session_state(root: Path) -> dict[str, list[str]]:
    value = _read_json(root / "session-state.json", {"sessions": {}})
    if set(value) - {"sessions"}:
        raise _ConfigurationError
    return _validate_mapping(value.get("sessions", {}))


def _active_directive_names(
    config: dict[str, Any],
    sessions: dict[str, list[str]],
    *,
    model: str,
    platform: str,
    session_id: str,
) -> list[str]:
    layers = [config["global"]]
    if platform:
        layers.append(config["platforms"].get(platform, []))
    layers.append(config["models"].get(model, []))
    if session_id:
        layers.append(sessions.get(session_id, []))

    names: list[str] = []
    for layer in layers:
        for name in layer:
            if name not in names:
                names.append(name)
    return names


def _read_directives(root: Path, names: list[str]) -> str:
    # HERMES_HOME is operator-owned. Link checks prevent accidental escapes, not
    # replacement races from another process that can already rewrite this config.
    directory = root / "directives"
    if directory.is_symlink() or not directory.is_dir():
        raise _ConfigurationError
    resolved_directory = directory.resolve()

    contents: list[str] = []
    for name in names:
        path = directory / name
        if path.is_symlink() or not path.is_file():
            raise _ConfigurationError
        try:
            path.resolve().relative_to(resolved_directory)
            descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
            with os.fdopen(descriptor, encoding="utf-8") as directive_file:
                content = directive_file.read().strip()
        except (OSError, UnicodeError, ValueError) as exc:
            raise _ConfigurationError from exc
        if not content:
            raise _ConfigurationError
        contents.append(content)
    return "\n\n".join(contents)


def _prepend_system(request: dict[str, Any], directive: str) -> dict[str, Any] | None:
    messages = request.get("messages")
    if not isinstance(messages, list):
        raise _ShapeError

    system_index = None
    for index, message in enumerate(messages):
        if not isinstance(message, dict):
            raise _ShapeError
        if message.get("role") == "system":
            if not isinstance(message.get("content"), str):
                raise _ShapeError
            system_index = index
            break

    rewritten = deepcopy(request)
    if system_index is None:
        rewritten["messages"].insert(0, {"role": "system", "content": directive})
        return rewritten

    existing = messages[system_index]["content"]
    if existing == directive or existing.startswith(f"{directive}\n\n"):
        return None
    rewritten["messages"][system_index]["content"] = f"{directive}\n\n{existing}"
    return rewritten


def _llm_request(**context: Any):
    request = context.get("request")
    if context.get("api_mode") != "chat_completions":
        logger.warning(_SHAPE_WARNING)
        return None
    if not isinstance(request, dict) or not isinstance(request.get("model"), str):
        logger.warning(_SHAPE_WARNING)
        return None

    try:
        root = _plugin_home()
        config = _load_config(root)
        sessions = _load_session_state(root)
        names = _active_directive_names(
            config,
            sessions,
            model=request["model"],
            platform=context.get("platform")
            if isinstance(context.get("platform"), str)
            else "",
            session_id=(
                context.get("session_id")
                if isinstance(context.get("session_id"), str)
                else ""
            ),
        )
        if not names:
            return None
        directive = _read_directives(root, names)
        rewritten = _prepend_system(request, directive)
    except _ShapeError:
        logger.warning(_SHAPE_WARNING)
        return None
    except Exception:
        logger.warning(_CONFIG_WARNING)
        return None

    if rewritten is None:
        return None
    return {"request": rewritten, "source": "prompt-controls"}


def _available_directives(root: Path) -> list[str]:
    directory = root / "directives"
    if directory.is_symlink():
        raise _ConfigurationError
    if not directory.is_dir():
        return []
    return sorted(
        path.name
        for path in directory.iterdir()
        if not path.is_symlink() and path.is_file() and path.suffix.lower() == ".md"
    )


@contextmanager
def _locked_config(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    lock_path = root / ".config.lock"
    with _WRITE_LOCK, open(lock_path, "a+b") as lock_file:
        if os.name == "nt":
            import msvcrt

            if lock_file.seek(0, os.SEEK_END) == 0:
                lock_file.write(b"\0")
                lock_file.flush()
            lock_file.seek(0)
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            yield
        finally:
            lock_file.seek(0)
            if os.name == "nt":
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock_file, fcntl.LOCK_UN)


def _atomic_write_config(root: Path, config: dict[str, Any]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=root,
            prefix=".config.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            json.dump(config, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, root / "config.json")
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _set_selection(
    config: dict[str, Any], scope: str, key: str, names: list[str]
) -> None:
    if scope == "global":
        config["global"] = names
    elif scope == "platform":
        config["platforms"][key] = names
    elif scope == "model":
        config["models"][key] = names
    else:
        raise _ConfigurationError


def _clear_selection(config: dict[str, Any], scope: str, key: str) -> None:
    if scope == "global":
        config["global"] = []
    elif scope == "platform":
        config["platforms"].pop(key, None)
    elif scope == "model":
        config["models"].pop(key, None)
    else:
        raise _ConfigurationError


def _command(raw_args: str) -> str:
    try:
        arguments = shlex.split(raw_args)
    except ValueError:
        return _USAGE

    root = _plugin_home()
    if arguments == ["list"]:
        try:
            names = _available_directives(root)
        except (OSError, _ConfigurationError):
            return "Prompt controls configuration is invalid; no changes were made."
        return "Available directives:\n" + ("\n".join(names) if names else "(none)")

    if not arguments or arguments[0] not in {"set", "clear"}:
        return _USAGE

    action = arguments[0]
    scope = arguments[1] if len(arguments) > 1 else ""
    if scope == "global":
        key = ""
        names = arguments[2:]
    elif scope in {"platform", "model"} and len(arguments) > 2:
        key = arguments[2]
        names = arguments[3:]
    else:
        return _USAGE

    if action == "set" and not names:
        return _USAGE
    if action == "clear" and names:
        return _USAGE

    try:
        if scope != "global" and not key:
            raise _ConfigurationError
        with _locked_config(root):
            config = _load_config(root)
            if action == "set":
                validated_names = _validate_directive_list(names)
                _read_directives(root, validated_names)
                _set_selection(config, scope, key, validated_names)
                result = "Selection updated."
            else:
                _clear_selection(config, scope, key)
                result = "Selection cleared."
            _atomic_write_config(root, config)
        return result
    except Exception:
        return "Prompt controls configuration is invalid; no changes were made."


def register(ctx):
    ctx.register_middleware("llm_request", _llm_request)
    ctx.register_command(
        "prompt-controls",
        handler=_command,
        description="List and select prompt directive files",
        args_hint="<list|set|clear>",
    )
