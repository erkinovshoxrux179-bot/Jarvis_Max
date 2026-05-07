import json
import subprocess
import sys
import time
from pathlib import Path

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE    = 0.06
    _PYAUTOGUI = True
except ImportError:
    _PYAUTOGUI = False

try:
    import pyperclip
    _PYPERCLIP = True
except ImportError:
    _PYPERCLIP = False

def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

def _get_os() -> str:
    try:
        cfg = json.loads(
            (_base_dir() / "config" / "api_keys.json").read_text(encoding="utf-8")
        )
        return cfg.get("os_system", "windows").lower()
    except Exception:
        return "windows"


def _require_pyautogui():
    if not _PYAUTOGUI:
        raise RuntimeError("PyAutoGUI not installed. Run: pip install pyautogui")


def _paste_text(text: str) -> None:
    _require_pyautogui()

    os_name = _get_os()
    paste_hotkey = ("command", "v") if os_name == "mac" else ("ctrl", "v")

    if _PYPERCLIP:
        pyperclip.copy(text)
        time.sleep(0.15)
        pyautogui.hotkey(*paste_hotkey)
        time.sleep(0.1)
    else:
        pyautogui.write(text, interval=0.03)


def _clear_and_paste(text: str) -> None:
    _require_pyautogui()
    os_name = _get_os()
    select_all = ("command", "a") if os_name == "mac" else ("ctrl", "a")
    pyautogui.hotkey(*select_all)
    time.sleep(0.1)
    pyautogui.press("delete")
    time.sleep(0.1)
    _paste_text(text)

def _open_app(app_name: str) -> bool:
    _require_pyautogui()
    os_name = _get_os()

    try:
        if os_name == "windows":
            pyautogui.press("win")
            time.sleep(0.5)
            _paste_text(app_name)
            time.sleep(0.6)
            pyautogui.press("enter")
            time.sleep(2.5)
            return True

        elif os_name == "mac":
            result = subprocess.run(
                ["open", "-a", app_name],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0:
                result = subprocess.run(
                    ["open", "-a", f"{app_name}.app"],
                    capture_output=True, text=True, timeout=10,
                )
            time.sleep(2.5)
            return result.returncode == 0

        else: 
            launched = False
            for launcher in [
                ["gtk-launch", app_name.lower()],
                [app_name.lower()],
            ]:
                try:
                    subprocess.Popen(
                        launcher,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    launched = True
                    break
                except FileNotFoundError:
                    continue
            time.sleep(2.5)
            return launched

    except Exception as e:
        print(f"[SendMessage] ⚠️ Could not open {app_name}: {e}")
        return False


def _open_browser_url(url: str) -> bool:
    import webbrowser
    try:
        webbrowser.open(url)
        time.sleep(4.0) 
        return True
    except Exception as e:
        print(f"[SendMessage] ⚠️ Could not open browser: {e}")
        return False

def _search_in_app(query: str) -> None:
    _require_pyautogui()
    os_name = _get_os()
    search_hotkey = ("command", "f") if os_name == "mac" else ("ctrl", "f")

    pyautogui.hotkey(*search_hotkey)
    time.sleep(0.5)
    _clear_and_paste(query)
    time.sleep(1.0)

def _desktop_send(app_name: str, receiver: str, message: str) -> str:
    if not _open_app(app_name):
        return f"Could not open {app_name}."

    time.sleep(1.0)
    _search_in_app(receiver)
    pyautogui.press("enter")
    time.sleep(0.8)

    _paste_text(message)
    time.sleep(0.2)
    pyautogui.press("enter")
    time.sleep(0.3)
    return f"Message sent to {receiver} via {app_name}."

def _send_whatsapp(receiver: str, message: str) -> str:
    return _desktop_send("WhatsApp", receiver, message)

def _send_telegram(receiver: str, message: str) -> str:
    return _desktop_send("Telegram", receiver, message)

def _send_signal(receiver: str, message: str) -> str:
    return _desktop_send("Signal", receiver, message)


def _send_discord(receiver: str, message: str) -> str:
    return _desktop_send("Discord", receiver, message)


def _send_instagram(receiver: str, message: str) -> str:
    _require_pyautogui()

    if not _open_browser_url("https://www.instagram.com/direct/new/"):
        return "Could not open Instagram in browser."

    _paste_text(receiver)
    time.sleep(1.5)

    pyautogui.press("down")
    time.sleep(0.3)
    pyautogui.press("enter")   
    time.sleep(0.4)

    for _ in range(4):
        pyautogui.press("tab")
        time.sleep(0.15)
    pyautogui.press("enter")
    time.sleep(2.0)

    _paste_text(message)
    time.sleep(0.2)
    pyautogui.press("enter")
    time.sleep(0.3)

    return f"Message sent to {receiver} via Instagram."


def _send_messenger(receiver: str, message: str) -> str:
    _require_pyautogui()

    if not _open_browser_url("https://www.messenger.com/"):
        return "Could not open Messenger in browser."


    _search_in_app(receiver)
    time.sleep(0.5)
    pyautogui.press("down")
    time.sleep(0.3)
    pyautogui.press("enter")
    time.sleep(1.0)

    _paste_text(message)
    time.sleep(0.2)
    pyautogui.press("enter")
    time.sleep(0.3)

    return f"Message sent to {receiver} via Messenger."

def _send_whatsapp_web(receiver: str, message: str, browser: str | None = None) -> str:
    """
    Best-effort WhatsApp Web sender via Playwright controller.
    Requires the user to be logged into WhatsApp Web already.
    """
    from actions.browser_control import browser_control

    browser_control({"action": "go_to", "browser": browser or "chrome", "url": "https://web.whatsapp.com/"})
    time.sleep(2.5)

    # Try to focus search and find chat
    browser_control({"action": "smart_click", "description": "Search"})
    time.sleep(0.5)
    browser_control({"action": "smart_type", "description": "Search", "text": receiver})
    time.sleep(1.0)
    # click the chat by visible text
    browser_control({"action": "click", "text": receiver})
    time.sleep(0.8)
    # type message into focused box
    browser_control({"action": "type", "text": message, "clear_first": False})
    browser_control({"action": "press", "key": "Enter"})
    return f"Attempted WhatsApp Web send to {receiver}. If you were logged in, it should be delivered."


def _send_telegram_web(receiver: str, message: str, browser: str | None = None) -> str:
    """
    Best-effort Telegram Web sender via Playwright controller.
    Requires the user to be logged into Telegram Web already.
    """
    from actions.browser_control import browser_control

    browser_control({"action": "go_to", "browser": browser or "chrome", "url": "https://web.telegram.org/k/"})
    time.sleep(3.0)

    browser_control({"action": "smart_click", "description": "Search"})
    time.sleep(0.4)
    browser_control({"action": "smart_type", "description": "Search", "text": receiver})
    time.sleep(1.0)
    browser_control({"action": "click", "text": receiver})
    time.sleep(0.8)
    browser_control({"action": "type", "text": message, "clear_first": False})
    browser_control({"action": "press", "key": "Enter"})
    return f"Attempted Telegram Web send to {receiver}. If you were logged in, it should be delivered."


def _send_telegram_uia(receiver: str, message: str) -> str:
    """
    Telegram Desktop (Windows) best-effort send using UIA focus + key sequences.
    This avoids coordinate clicking and usually works if Telegram is already installed.
    """
    from actions.windows_automation import windows_automation

    # Focus Telegram window (if not found, try opening)
    r = windows_automation({"action": "focus", "window_title": "Telegram", "timeout": 6})
    if "no matching" in r.lower():
        try:
            from actions.open_app import open_app
            open_app({"app_name": "Telegram"})
            time.sleep(2.2)
        except Exception:
            pass
        r = windows_automation({"action": "focus", "window_title": "Telegram", "timeout": 8})
    # Open search (Telegram supports Ctrl+K to search chats)
    windows_automation({"action": "keys", "window_title": "Telegram", "keys": "^k"})
    time.sleep(0.2)
    windows_automation({"action": "type", "window_title": "Telegram", "text": receiver, "clear_first": True})
    time.sleep(0.6)
    windows_automation({"action": "keys", "window_title": "Telegram", "keys": "{ENTER}"})
    time.sleep(0.6)
    windows_automation({"action": "type", "window_title": "Telegram", "text": message, "clear_first": False})
    windows_automation({"action": "keys", "window_title": "Telegram", "keys": "{ENTER}"})
    return f"{r}\nMessage sent to {receiver} via Telegram (UIA)."


def _send_whatsapp_uia(receiver: str, message: str) -> str:
    """
    WhatsApp Desktop (Windows) best-effort send using UIA focus + key sequences.
    WhatsApp desktop shortcuts vary by version; Ctrl+F often focuses chat search.
    """
    from actions.windows_automation import windows_automation

    r = windows_automation({"action": "focus", "window_title": "WhatsApp", "timeout": 6})
    if "no matching" in r.lower():
        try:
            from actions.open_app import open_app
            open_app({"app_name": "WhatsApp"})
            time.sleep(2.2)
        except Exception:
            pass
        r = windows_automation({"action": "focus", "window_title": "WhatsApp", "timeout": 8})
    windows_automation({"action": "keys", "window_title": "WhatsApp", "keys": "^f"})
    time.sleep(0.2)
    windows_automation({"action": "type", "window_title": "WhatsApp", "text": receiver, "clear_first": True})
    time.sleep(0.7)
    windows_automation({"action": "keys", "window_title": "WhatsApp", "keys": "{ENTER}"})
    time.sleep(0.7)
    windows_automation({"action": "type", "window_title": "WhatsApp", "text": message, "clear_first": False})
    windows_automation({"action": "keys", "window_title": "WhatsApp", "keys": "{ENTER}"})
    return f"{r}\nMessage sent to {receiver} via WhatsApp (UIA)."

_PLATFORM_MAP = [
    ({"whatsapp", "wp", "wapp"},              _send_whatsapp),
    ({"telegram", "tg"},                      _send_telegram),
    ({"instagram", "ig", "insta"},            _send_instagram),
    ({"signal"},                               _send_signal),
    ({"discord"},                              _send_discord),
    ({"messenger", "facebook", "fb"},         _send_messenger),
]


def _resolve_platform(platform_str: str):
    key = platform_str.lower().strip()
    for keywords, handler in _PLATFORM_MAP:
        if any(k in key for k in keywords):
            return handler
    return lambda r, m: _desktop_send(platform_str.strip().title(), r, m)


def send_message(
    parameters: dict,
    response=None,
    player=None,
    session_memory=None,
) -> str:
    params       = parameters or {}
    receiver     = params.get("receiver", "").strip()
    message_text = params.get("message_text", "").strip()
    platform     = params.get("platform", "whatsapp").strip()
    mode         = (params.get("mode") or params.get("strategy") or "").strip().lower()  # "desktop" | "web" | "uia" | ""
    browser      = (params.get("browser") or "").strip().lower() or None

    if not receiver:
        return "Please specify a recipient."
    if not message_text:
        return "Please specify the message content."

    preview = message_text[:50] + ("…" if len(message_text) > 50 else "")
    print(f"[SendMessage] 📨 {platform} → {receiver}: {preview}")
    if player:
        player.write_log(f"[msg] {platform} → {receiver}")

    try:
        pkey = platform.lower().strip()

        # Explicit web mode
        if mode == "web":
            if "whatsapp" in pkey or pkey in ("wp", "wapp"):
                result = _send_whatsapp_web(receiver, message_text, browser=browser)
            elif "telegram" in pkey or pkey in ("tg",):
                result = _send_telegram_web(receiver, message_text, browser=browser)
            else:
                result = "Web mode is currently supported for WhatsApp/Telegram only."

        # Explicit UIA mode
        elif mode == "uia":
            if "telegram" in pkey or pkey in ("tg",):
                result = _send_telegram_uia(receiver, message_text)
            elif "whatsapp" in pkey or pkey in ("wp", "wapp"):
                result = _send_whatsapp_uia(receiver, message_text)
            else:
                result = "UIA mode is currently supported for Telegram/WhatsApp only."

        else:
            # AUTO MODE: prefer UIA on Windows (desktop apps), then Web, then PyAutoGUI legacy
            if "telegram" in pkey or pkey in ("tg",):
                try:
                    result = _send_telegram_uia(receiver, message_text)
                    return result
                except Exception:
                    try:
                        result = _send_telegram_web(receiver, message_text, browser=browser)
                        return result
                    except Exception:
                        pass
            if "whatsapp" in pkey or pkey in ("wp", "wapp"):
                try:
                    result = _send_whatsapp_uia(receiver, message_text)
                    return result
                except Exception:
                    try:
                        result = _send_whatsapp_web(receiver, message_text, browser=browser)
                        return result
                    except Exception:
                        pass

            if not _PYAUTOGUI:
                # If desktop automation is unavailable, still try web for WA/TG as fallback
                if "whatsapp" in pkey or pkey in ("wp", "wapp"):
                    result = _send_whatsapp_web(receiver, message_text, browser=browser)
                elif "telegram" in pkey or pkey in ("tg",):
                    result = _send_telegram_web(receiver, message_text, browser=browser)
                else:
                    return "PyAutoGUI is not installed — cannot control the desktop."
            handler = _resolve_platform(platform)
            result  = handler(receiver, message_text)
    except Exception as e:
        result = f"Could not send message: {e}"

    print(f"[SendMessage] {'✅' if 'sent' in result.lower() else '❌'} {result}")
    if player:
        player.write_log(f"[msg] {result}")

    return result