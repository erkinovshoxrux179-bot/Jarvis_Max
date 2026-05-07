from __future__ import annotations

import platform
import time
from dataclasses import dataclass
from typing import Any


_OS = platform.system()


@dataclass
class _Target:
    title: str | None = None
    process: str | None = None
    timeout: float = 8.0


def _require_windows() -> None:
    if _OS != "Windows":
        raise RuntimeError(f"windows_automation is only supported on Windows (current: {_OS}).")


def _require_pywinauto():
    try:
        from pywinauto import Desktop  # noqa: F401
        from pywinauto.application import Application  # noqa: F401
        from pywinauto.keyboard import send_keys  # noqa: F401
    except Exception as e:
        raise RuntimeError(
            "pywinauto is required for windows_automation. "
            "Install with: pip install pywinauto"
        ) from e


def _desktop():
    _require_pywinauto()
    from pywinauto import Desktop

    return Desktop(backend="uia")


def _find_window(target: _Target):
    _require_windows()
    d = _desktop()

    # Fast path: title substring match
    if target.title:
        for w in d.windows():
            try:
                t = w.window_text() or ""
                if target.title.lower() in t.lower():
                    return w
            except Exception:
                continue

    # Fallback: process name match (e.g., "notepad.exe", "chrome.exe")
    if target.process:
        for w in d.windows():
            try:
                p = (w.element_info.process_name or "").lower()
                if p == target.process.lower():
                    return w
            except Exception:
                continue

    return None


def _wait_for_window(target: _Target):
    deadline = time.time() + max(0.5, float(target.timeout or 8.0))
    last = None
    while time.time() < deadline:
        last = _find_window(target)
        if last is not None:
            return last
        time.sleep(0.2)
    return last


def _as_target(params: dict) -> _Target:
    return _Target(
        title=(params.get("window_title") or params.get("title") or "").strip() or None,
        process=(params.get("process") or params.get("process_name") or "").strip() or None,
        timeout=float(params.get("timeout", 8.0) or 8.0),
    )


def list_windows(limit: int = 25) -> list[dict[str, Any]]:
    _require_windows()
    d = _desktop()
    out: list[dict[str, Any]] = []
    for w in d.windows():
        try:
            title = (w.window_text() or "").strip()
            if not title:
                continue
            info = w.element_info
            out.append(
                {
                    "title": title[:200],
                    "process_name": (info.process_name or "")[:80],
                    "handle": int(getattr(info, "handle", 0) or 0),
                    "class_name": (info.class_name or "")[:80],
                }
            )
        except Exception:
            continue
        if len(out) >= limit:
            break
    return out


def focus_window(params: dict) -> str:
    _require_windows()
    tgt = _as_target(params)
    w = _wait_for_window(tgt)
    if w is None:
        return "No matching window found."
    try:
        w.set_focus()
    except Exception:
        try:
            w.set_focus()
        except Exception as e:
            return f"Could not focus window: {e}"
    return f"Focused: {(w.window_text() or '').strip()[:120]}"


def window_action(params: dict, action: str) -> str:
    _require_windows()
    tgt = _as_target(params)
    w = _wait_for_window(tgt)
    if w is None:
        return "No matching window found."
    try:
        if action == "close":
            w.close()
            return "Window closed."
        if action == "minimize":
            w.minimize()
            return "Window minimized."
        if action == "maximize":
            w.maximize()
            return "Window maximized."
        if action == "restore":
            w.restore()
            return "Window restored."
        return f"Unknown window action: {action}"
    except Exception as e:
        return f"Window action failed ({action}): {e}"


def click_control(params: dict) -> str:
    _require_windows()
    tgt = _as_target(params)
    w = _wait_for_window(tgt)
    if w is None:
        return "No matching window found."

    control_text = (params.get("control_text") or params.get("name") or "").strip()
    auto_id = (params.get("automation_id") or params.get("auto_id") or "").strip()
    control_type = (params.get("control_type") or "").strip() or None

    try:
        w.set_focus()
    except Exception:
        pass

    try:
        if auto_id:
            c = w.child_window(auto_id=auto_id, control_type=control_type)
        elif control_text:
            c = w.child_window(title=control_text, control_type=control_type)
        else:
            return "Provide control_text or automation_id."
        c.wait("exists ready", timeout=max(1, int(tgt.timeout)))
        c.click_input()
        return "Clicked control."
    except Exception as e:
        return f"Click failed: {e}"


def type_into_control(params: dict) -> str:
    _require_windows()
    _require_pywinauto()
    from pywinauto.keyboard import send_keys

    tgt = _as_target(params)
    w = _wait_for_window(tgt)
    if w is None:
        return "No matching window found."

    text = str(params.get("text") or "")
    clear_first = bool(params.get("clear_first", True))

    control_text = (params.get("control_text") or params.get("name") or "").strip()
    auto_id = (params.get("automation_id") or params.get("auto_id") or "").strip()
    control_type = (params.get("control_type") or "Edit").strip() or "Edit"

    try:
        w.set_focus()
    except Exception:
        pass

    try:
        if auto_id:
            c = w.child_window(auto_id=auto_id, control_type=control_type)
        elif control_text:
            c = w.child_window(title=control_text, control_type=control_type)
        else:
            # If no explicit control, type into currently focused element in this window.
            send_keys(text, with_spaces=True, pause=0.01)
            return "Typed (focused element)."

        c.wait("exists ready", timeout=max(1, int(tgt.timeout)))
        c.set_focus()
        if clear_first:
            try:
                c.type_keys("^a{DEL}", set_foreground=False)
            except Exception:
                send_keys("^a{DEL}", pause=0.01)
        try:
            c.type_keys(text, with_spaces=True, set_foreground=False)
        except Exception:
            send_keys(text, with_spaces=True, pause=0.01)
        return "Typed into control."
    except Exception as e:
        return f"Type failed: {e}"


def dump_controls(params: dict) -> str:
    """Returns a short tree of controls to help the model learn selectors."""
    _require_windows()
    tgt = _as_target(params)
    w = _wait_for_window(tgt)
    if w is None:
        return "No matching window found."
    try:
        # Pywinauto prints a tree; capture minimal text representation.
        descendants = w.descendants()[:80]
        lines: list[str] = []
        for el in descendants:
            try:
                info = el.element_info
                title = (el.window_text() or "").strip()
                if not title and not info.automation_id:
                    continue
                lines.append(
                    f"- {info.control_type}  title='{title[:60]}'  auto_id='{(info.automation_id or '')[:60]}'"
                )
            except Exception:
                continue
        return "Controls:\n" + ("\n".join(lines) if lines else "(none)")
    except Exception as e:
        return f"Could not dump controls: {e}"


def send_keys_action(params: dict) -> str:
    _require_windows()
    _require_pywinauto()
    from pywinauto.keyboard import send_keys

    tgt = _as_target(params)
    w = _wait_for_window(tgt)
    if w is None:
        return "No matching window found."
    keys = str(params.get("keys") or params.get("key_sequence") or "").strip()
    if not keys:
        return "No keys provided."
    try:
        try:
            w.set_focus()
        except Exception:
            pass
        send_keys(keys, pause=0.01)
        return f"Sent keys: {keys}"
    except Exception as e:
        return f"send_keys failed: {e}"


def windows_automation(parameters: dict = None, response=None, player=None, session_memory=None) -> str:
    """
    Windows UI automation via UIA (pywinauto).

    parameters:
      action: list_windows | focus | close | minimize | maximize | restore | click | type | keys | dump_controls
      window_title: substring to match window title (recommended)
      process: process name match (optional)
      timeout: seconds (optional, default 8)

      click/type/keys extras:
        control_text: exact control title/name
        automation_id: UIA automation id
        control_type: e.g. Button, Edit, ListItem (optional)
        text: for type
        clear_first: bool (type)
        keys: key sequence for 'keys' action (pywinauto send_keys syntax, e.g. '^k', '{ENTER}')
    """
    params = parameters or {}
    action = (params.get("action") or "").lower().strip()
    confirmed = str(params.get("confirmed", "")).lower() in ("yes", "true", "1", "confirm")
    if player:
        player.write_log(f"[win_auto] {action or 'unknown'}")

    try:
        if action in ("list_windows", "list"):
            limit = int(params.get("limit", 25))
            wins = list_windows(limit=limit)
            if not wins:
                return "No windows found."
            # return compact text for model
            lines = ["Open windows:"]
            for w in wins:
                lines.append(f"- {w['title']}  ({w['process_name']})")
            return "\n".join(lines)

        if action in ("focus", "activate"):
            return focus_window(params)

        if action in ("close", "minimize", "maximize", "restore"):
            if action == "close" and not confirmed:
                return "This will close a window. Confirm by calling again with confirmed=yes."
            return window_action(params, action)

        if action in ("click", "click_control"):
            return click_control(params)

        if action in ("type", "type_control", "set_text"):
            return type_into_control(params)

        if action in ("keys", "send_keys"):
            return send_keys_action(params)

        if action in ("dump_controls", "inspect"):
            return dump_controls(params)

        return f"Unknown action: '{action}'"
    except Exception as e:
        return f"windows_automation failed: {e}"

