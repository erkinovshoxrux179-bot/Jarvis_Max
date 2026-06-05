"""
windows_max_control.py - Comprehensive Windows system control module.

Provides advanced Windows management capabilities including services, registry,
notifications, clipboard, virtual desktops, startup programs, environment variables,
firewall, Windows Defender, taskbar, context menu, and system information.
"""

from __future__ import annotations

import os
import platform
import subprocess
import json
from typing import Any

_OS = platform.system()


def _require_windows() -> None:
    if _OS != "Windows":
        raise RuntimeError(
            f"windows_max_control is only supported on Windows (current: {_OS})."
        )


def _run_powershell(command: str, timeout: float = 30.0) -> str:
    """Run a PowerShell command and return output."""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0 and result.stderr:
            return f"Error: {result.stderr.strip()}"
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "Error: Command timed out."
    except Exception as e:
        return f"Error running PowerShell: {e}"


def _run_cmd(command: str, timeout: float = 30.0) -> str:
    """Run a CMD command and return output."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=True,
        )
        if result.returncode != 0 and result.stderr:
            return f"Error: {result.stderr.strip()}"
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "Error: Command timed out."
    except Exception as e:
        return f"Error running command: {e}"


# ═══════════════════════════════════════════
# SERVICE MANAGEMENT
# ═══════════════════════════════════════════

def manage_services(params: dict, player=None) -> str:
    """List, start, stop, or restart Windows services."""
    _require_windows()
    sub_action = (params.get("sub_action") or "list").lower().strip()
    service_name = (params.get("service_name") or "").strip()

    if sub_action == "list":
        query = params.get("filter", "")
        cmd = "Get-Service"
        if query:
            cmd += f" | Where-Object {{$_.DisplayName -like '*{query}*' -or $_.Name -like '*{query}*'}}"
        cmd += " | Select-Object -First 50 Name, DisplayName, Status | Format-Table -AutoSize"
        return _run_powershell(cmd)

    if not service_name:
        return "Error: service_name is required for start/stop/restart."

    if sub_action == "start":
        return _run_powershell(f"Start-Service -Name '{service_name}' -PassThru | Format-Table Name, Status")
    elif sub_action == "stop":
        return _run_powershell(f"Stop-Service -Name '{service_name}' -Force -PassThru | Format-Table Name, Status")
    elif sub_action == "restart":
        return _run_powershell(f"Restart-Service -Name '{service_name}' -Force -PassThru | Format-Table Name, Status")
    elif sub_action == "status":
        return _run_powershell(f"Get-Service -Name '{service_name}' | Format-List Name, DisplayName, Status, StartType")
    else:
        return f"Unknown sub_action for services: '{sub_action}'. Use list/start/stop/restart/status."


# ═══════════════════════════════════════════
# REGISTRY MANAGEMENT
# ═══════════════════════════════════════════

def manage_registry(params: dict, player=None) -> str:
    """Read, write, or delete Windows registry keys/values."""
    _require_windows()
    import winreg

    sub_action = (params.get("sub_action") or "read").lower().strip()
    key_path = (params.get("key_path") or "").strip()
    value_name = (params.get("value_name") or "").strip()
    value_data = params.get("value_data")
    value_type = (params.get("value_type") or "REG_SZ").upper().strip()

    if not key_path:
        return "Error: key_path is required (e.g., 'HKCU\\\\Software\\\\MyApp')."

    # Parse hive and subkey
    hive_map = {
        "HKCU": winreg.HKEY_CURRENT_USER,
        "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
        "HKLM": winreg.HKEY_LOCAL_MACHINE,
        "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
        "HKCR": winreg.HKEY_CLASSES_ROOT,
        "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
    }

    parts = key_path.split("\\", 1)
    if len(parts) < 2:
        return "Error: key_path must include hive and subkey (e.g., 'HKCU\\\\Software\\\\MyApp')."

    hive_name = parts[0].upper()
    subkey = parts[1]

    hive = hive_map.get(hive_name)
    if hive is None:
        return f"Error: Unknown registry hive '{hive_name}'. Use HKCU, HKLM, or HKCR."

    type_map = {
        "REG_SZ": winreg.REG_SZ,
        "REG_DWORD": winreg.REG_DWORD,
        "REG_EXPAND_SZ": winreg.REG_EXPAND_SZ,
        "REG_MULTI_SZ": winreg.REG_MULTI_SZ,
    }

    try:
        if sub_action == "read":
            key = winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ)
            if value_name:
                data, reg_type = winreg.QueryValueEx(key, value_name)
                winreg.CloseKey(key)
                return f"{value_name} = {data} (type: {reg_type})"
            else:
                # List all values in the key
                values = []
                i = 0
                while True:
                    try:
                        name, data, reg_type = winreg.EnumValue(key, i)
                        values.append(f"  {name} = {data}")
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(key)
                if values:
                    return "Values:\n" + "\n".join(values)
                return "No values found in this key."

        elif sub_action == "write":
            if not value_name:
                return "Error: value_name is required for write."
            if value_data is None:
                return "Error: value_data is required for write."
            reg_type = type_map.get(value_type, winreg.REG_SZ)
            if reg_type == winreg.REG_DWORD:
                value_data = int(value_data)
            key = winreg.CreateKeyEx(hive, subkey, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, value_name, 0, reg_type, value_data)
            winreg.CloseKey(key)
            return f"Registry value '{value_name}' set successfully."

        elif sub_action == "delete":
            if value_name:
                key = winreg.OpenKey(hive, subkey, 0, winreg.KEY_WRITE)
                winreg.DeleteValue(key, value_name)
                winreg.CloseKey(key)
                return f"Registry value '{value_name}' deleted."
            else:
                winreg.DeleteKey(hive, subkey)
                return f"Registry key '{key_path}' deleted."

        else:
            return f"Unknown sub_action for registry: '{sub_action}'. Use read/write/delete."

    except FileNotFoundError:
        return f"Registry key or value not found: {key_path}"
    except PermissionError:
        return "Error: Permission denied. May need administrator privileges."
    except Exception as e:
        return f"Registry error: {e}"


# ═══════════════════════════════════════════
# NOTIFICATIONS
# ═══════════════════════════════════════════

def send_notification(params: dict, player=None) -> str:
    """Send a Windows toast notification."""
    _require_windows()
    title = params.get("title", "JARVIS")
    message = params.get("message", "")
    timeout = int(params.get("timeout", 10))

    if not message:
        return "Error: message is required for notification."

    try:
        from plyer import notification
        notification.notify(
            title=title,
            message=message,
            timeout=timeout,
            app_name="JARVIS",
        )
        return f"Notification sent: '{title}' - '{message}'"
    except ImportError:
        return "Error: plyer is not installed. Install with: pip install plyer"
    except Exception as e:
        return f"Notification error: {e}"


# ═══════════════════════════════════════════
# CLIPBOARD
# ═══════════════════════════════════════════

def manage_clipboard(params: dict, player=None) -> str:
    """Get or set clipboard content."""
    _require_windows()
    sub_action = (params.get("sub_action") or "get").lower().strip()

    try:
        import pyperclip

        if sub_action == "get":
            content = pyperclip.paste()
            if not content:
                return "Clipboard is empty."
            # Truncate for safety
            if len(content) > 2000:
                return f"Clipboard content (truncated):\n{content[:2000]}..."
            return f"Clipboard content:\n{content}"

        elif sub_action == "set":
            text = str(params.get("text", ""))
            if not text:
                return "Error: text is required for clipboard set."
            pyperclip.copy(text)
            return "Text copied to clipboard."

        elif sub_action == "clear":
            pyperclip.copy("")
            return "Clipboard cleared."

        else:
            return f"Unknown sub_action for clipboard: '{sub_action}'. Use get/set/clear."

    except ImportError:
        return "Error: pyperclip is not installed. Install with: pip install pyperclip"
    except Exception as e:
        return f"Clipboard error: {e}"


# ═══════════════════════════════════════════
# VIRTUAL DESKTOPS
# ═══════════════════════════════════════════

def manage_virtual_desktop(params: dict, player=None) -> str:
    """Create, switch, or close virtual desktops."""
    _require_windows()
    sub_action = (params.get("sub_action") or "list").lower().strip()

    if sub_action == "create":
        # Use keyboard shortcut Win+Ctrl+D
        try:
            import pyautogui
            pyautogui.hotkey("win", "ctrl", "d")
            return "New virtual desktop created."
        except Exception as e:
            return f"Error creating virtual desktop: {e}"

    elif sub_action == "switch_left":
        try:
            import pyautogui
            pyautogui.hotkey("win", "ctrl", "left")
            return "Switched to left virtual desktop."
        except Exception as e:
            return f"Error switching desktop: {e}"

    elif sub_action == "switch_right":
        try:
            import pyautogui
            pyautogui.hotkey("win", "ctrl", "right")
            return "Switched to right virtual desktop."
        except Exception as e:
            return f"Error switching desktop: {e}"

    elif sub_action == "close":
        try:
            import pyautogui
            pyautogui.hotkey("win", "ctrl", "F4")
            return "Current virtual desktop closed."
        except Exception as e:
            return f"Error closing virtual desktop: {e}"

    elif sub_action == "list":
        # PowerShell to get virtual desktop count
        cmd = (
            "try { "
            "[void][System.Reflection.Assembly]::LoadWithPartialName('System.Runtime.InteropServices'); "
            "$desktops = (Get-Process | Where-Object {$_.MainWindowTitle}).Count; "
            "Write-Output \"Virtual desktops are active. Use Task View (Win+Tab) to see all.\""
            " } catch { Write-Output 'Could not enumerate virtual desktops.' }"
        )
        return _run_powershell(cmd)

    else:
        return f"Unknown sub_action for virtual_desktop: '{sub_action}'. Use create/switch_left/switch_right/close/list."


# ═══════════════════════════════════════════
# STARTUP PROGRAMS
# ═══════════════════════════════════════════

def manage_startup(params: dict, player=None) -> str:
    """List, add, or remove startup programs."""
    _require_windows()
    import winreg

    sub_action = (params.get("sub_action") or "list").lower().strip()
    startup_key = r"Software\Microsoft\Windows\CurrentVersion\Run"

    try:
        if sub_action == "list":
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, startup_key, 0, winreg.KEY_READ)
            programs = []
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    programs.append(f"  {name}: {value}")
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
            if programs:
                return "Startup programs:\n" + "\n".join(programs)
            return "No startup programs found."

        elif sub_action == "add":
            name = (params.get("name") or "").strip()
            path = (params.get("path") or "").strip()
            if not name or not path:
                return "Error: 'name' and 'path' are required to add a startup program."
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, startup_key, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, path)
            winreg.CloseKey(key)
            return f"Added '{name}' to startup programs."

        elif sub_action == "remove":
            name = (params.get("name") or "").strip()
            if not name:
                return "Error: 'name' is required to remove a startup program."
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, startup_key, 0, winreg.KEY_WRITE)
            winreg.DeleteValue(key, name)
            winreg.CloseKey(key)
            return f"Removed '{name}' from startup programs."

        else:
            return f"Unknown sub_action for startup: '{sub_action}'. Use list/add/remove."

    except FileNotFoundError:
        return "Startup registry key or value not found."
    except PermissionError:
        return "Error: Permission denied."
    except Exception as e:
        return f"Startup management error: {e}"


# ═══════════════════════════════════════════
# ENVIRONMENT VARIABLES
# ═══════════════════════════════════════════

def manage_env_vars(params: dict, player=None) -> str:
    """Get, set, or delete environment variables."""
    _require_windows()
    sub_action = (params.get("sub_action") or "get").lower().strip()
    var_name = (params.get("name") or params.get("variable") or "").strip()

    if sub_action == "list":
        # List all user environment variables
        cmd = "[System.Environment]::GetEnvironmentVariables('User') | Format-Table -AutoSize"
        return _run_powershell(cmd)

    if not var_name:
        return "Error: 'name' (variable name) is required."

    if sub_action == "get":
        value = os.environ.get(var_name)
        if value is None:
            return f"Environment variable '{var_name}' is not set."
        return f"{var_name} = {value}"

    elif sub_action == "set":
        value = str(params.get("value", ""))
        if not value:
            return "Error: 'value' is required for set."
        # Set for current process
        os.environ[var_name] = value
        # Persist with setx
        result = _run_cmd(f'setx {var_name} "{value}"')
        return f"Environment variable '{var_name}' set to '{value}'. {result}"

    elif sub_action == "delete":
        cmd = f"[System.Environment]::SetEnvironmentVariable('{var_name}', $null, 'User')"
        result = _run_powershell(cmd)
        if var_name in os.environ:
            del os.environ[var_name]
        return f"Environment variable '{var_name}' deleted. {result}"

    else:
        return f"Unknown sub_action for env_vars: '{sub_action}'. Use get/set/delete/list."


# ═══════════════════════════════════════════
# INSTALLED APPLICATIONS
# ═══════════════════════════════════════════

def list_installed_apps(params: dict, player=None) -> str:
    """List installed applications from the registry."""
    _require_windows()
    filter_text = (params.get("filter") or params.get("search") or "").lower().strip()

    cmd = (
        "Get-ItemProperty "
        "'HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*', "
        "'HKLM:\\Software\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*' "
        "| Where-Object { $_.DisplayName -ne $null } "
    )
    if filter_text:
        cmd += f"| Where-Object {{ $_.DisplayName -like '*{filter_text}*' }} "
    cmd += "| Select-Object -First 50 DisplayName, DisplayVersion, Publisher | Sort-Object DisplayName | Format-Table -AutoSize"

    return _run_powershell(cmd)


# ═══════════════════════════════════════════
# WINDOWS UPDATE
# ═══════════════════════════════════════════

def windows_update_status(params: dict, player=None) -> str:
    """Check Windows Update status."""
    _require_windows()
    sub_action = (params.get("sub_action") or "status").lower().strip()

    if sub_action == "status":
        cmd = (
            "$Session = New-Object -ComObject Microsoft.Update.Session; "
            "$Searcher = $Session.CreateUpdateSearcher(); "
            "try { "
            "$Results = $Searcher.Search('IsInstalled=0'); "
            "if ($Results.Updates.Count -eq 0) { "
            "Write-Output 'System is up to date. No pending updates.' "
            "} else { "
            "Write-Output \"$($Results.Updates.Count) updates available:\"; "
            "$Results.Updates | Select-Object -First 20 Title | Format-Table -AutoSize "
            "} "
            "} catch { Write-Output \"Could not check updates: $_\" }"
        )
        return _run_powershell(cmd, timeout=60.0)

    elif sub_action == "history":
        cmd = (
            "Get-HotFix | Sort-Object InstalledOn -Descending | "
            "Select-Object -First 20 HotFixID, Description, InstalledOn | Format-Table -AutoSize"
        )
        return _run_powershell(cmd)

    else:
        return f"Unknown sub_action for windows_update: '{sub_action}'. Use status/history."


# ═══════════════════════════════════════════
# FIREWALL MANAGEMENT
# ═══════════════════════════════════════════

def manage_firewall(params: dict, player=None) -> str:
    """Manage Windows Firewall settings."""
    _require_windows()
    sub_action = (params.get("sub_action") or "status").lower().strip()

    if sub_action == "status":
        return _run_cmd("netsh advfirewall show allprofiles state")

    elif sub_action == "enable":
        profile = params.get("profile", "allprofiles")
        return _run_cmd(f"netsh advfirewall set {profile} state on")

    elif sub_action == "disable":
        profile = params.get("profile", "allprofiles")
        return _run_cmd(f"netsh advfirewall set {profile} state off")

    elif sub_action == "add_rule":
        rule_name = (params.get("rule_name") or "").strip()
        direction = (params.get("direction") or "in").lower()
        action = (params.get("rule_action") or "allow").lower()
        protocol = (params.get("protocol") or "tcp").lower()
        port = (params.get("port") or "").strip()

        if not rule_name:
            return "Error: rule_name is required."
        if not port:
            return "Error: port is required."

        cmd = (
            f'netsh advfirewall firewall add rule name="{rule_name}" '
            f'dir={direction} action={action} protocol={protocol} localport={port}'
        )
        return _run_cmd(cmd)

    elif sub_action == "remove_rule":
        rule_name = (params.get("rule_name") or "").strip()
        if not rule_name:
            return "Error: rule_name is required."
        return _run_cmd(f'netsh advfirewall firewall delete rule name="{rule_name}"')

    elif sub_action == "list_rules":
        filter_text = params.get("filter", "")
        cmd = "netsh advfirewall firewall show rule name=all"
        if filter_text:
            cmd += f' | findstr /i "{filter_text}"'
        return _run_cmd(cmd)

    else:
        return f"Unknown sub_action for firewall: '{sub_action}'. Use status/enable/disable/add_rule/remove_rule/list_rules."


# ═══════════════════════════════════════════
# WINDOWS DEFENDER
# ═══════════════════════════════════════════

def manage_defender(params: dict, player=None) -> str:
    """Manage Windows Defender settings and scans."""
    _require_windows()
    sub_action = (params.get("sub_action") or "status").lower().strip()

    if sub_action == "status":
        cmd = "Get-MpComputerStatus | Select-Object AntivirusEnabled, RealTimeProtectionEnabled, AntivirusSignatureLastUpdated, QuickScanEndTime | Format-List"
        return _run_powershell(cmd)

    elif sub_action == "quick_scan":
        cmd = "Start-MpScan -ScanType QuickScan; Write-Output 'Quick scan started.'"
        return _run_powershell(cmd, timeout=120.0)

    elif sub_action == "full_scan":
        cmd = "Start-MpScan -ScanType FullScan; Write-Output 'Full scan started (this may take a while).'"
        return _run_powershell(cmd, timeout=120.0)

    elif sub_action == "update_signatures":
        cmd = "Update-MpSignature; Write-Output 'Defender signatures updated.'"
        return _run_powershell(cmd, timeout=60.0)

    elif sub_action == "toggle_realtime":
        enable = str(params.get("enable", "true")).lower() in ("true", "1", "yes")
        val = "$true" if enable else "$false"
        cmd = f"Set-MpPreference -DisableRealtimeMonitoring (-not {val}); Write-Output 'Real-time protection toggled.'"
        return _run_powershell(cmd)

    elif sub_action == "threats":
        cmd = "Get-MpThreatDetection | Select-Object -First 10 ThreatID, ProcessName, DomainUser, ActionSuccess | Format-Table -AutoSize"
        return _run_powershell(cmd)

    else:
        return f"Unknown sub_action for defender: '{sub_action}'. Use status/quick_scan/full_scan/update_signatures/toggle_realtime/threats."


# ═══════════════════════════════════════════
# TASKBAR MANAGEMENT
# ═══════════════════════════════════════════

def manage_taskbar(params: dict, player=None) -> str:
    """Manage taskbar settings."""
    _require_windows()
    sub_action = (params.get("sub_action") or "settings").lower().strip()

    taskbar_reg = r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"

    if sub_action == "hide":
        cmd = f'reg add "{taskbar_reg}" /v TaskbarAutoHideInTabletMode /t REG_DWORD /d 1 /f'
        _run_cmd(cmd)
        cmd2 = f'reg add "{taskbar_reg}" /v EnableAutoTray /t REG_DWORD /d 1 /f'
        _run_cmd(cmd2)
        return "Taskbar auto-hide enabled. Changes may require explorer restart."

    elif sub_action == "show":
        cmd = f'reg add "{taskbar_reg}" /v TaskbarAutoHideInTabletMode /t REG_DWORD /d 0 /f'
        _run_cmd(cmd)
        return "Taskbar auto-hide disabled."

    elif sub_action == "small_icons":
        enable = str(params.get("enable", "true")).lower() in ("true", "1", "yes")
        val = 1 if enable else 0
        cmd = f'reg add "{taskbar_reg}" /v TaskbarSmallIcons /t REG_DWORD /d {val} /f'
        _run_cmd(cmd)
        return f"Taskbar small icons {'enabled' if enable else 'disabled'}. Restart explorer to apply."

    elif sub_action == "settings":
        cmd = "Get-ItemProperty 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced' | Select-Object TaskbarSmallIcons, ShowTaskViewButton, TaskbarGlomLevel | Format-List"
        return _run_powershell(cmd)

    elif sub_action == "restart_explorer":
        _run_cmd("taskkill /f /im explorer.exe")
        _run_cmd("start explorer.exe")
        return "Explorer restarted. Taskbar refreshed."

    else:
        return f"Unknown sub_action for taskbar: '{sub_action}'. Use hide/show/small_icons/settings/restart_explorer."


# ═══════════════════════════════════════════
# CONTEXT MENU
# ═══════════════════════════════════════════

def manage_context_menu(params: dict, player=None) -> str:
    """Add or remove context menu entries."""
    _require_windows()
    import winreg

    sub_action = (params.get("sub_action") or "list").lower().strip()
    menu_name = (params.get("name") or "").strip()

    if sub_action == "add":
        if not menu_name:
            return "Error: 'name' is required for context menu entry."
        command = (params.get("command") or "").strip()
        if not command:
            return "Error: 'command' is required (the executable/command to run)."
        icon = (params.get("icon") or "").strip()

        # Add to background context menu (right-click desktop/folder background)
        base_key = r"Directory\Background\shell"
        try:
            key = winreg.CreateKeyEx(
                winreg.HKEY_CLASSES_ROOT,
                f"{base_key}\\{menu_name}",
                0,
                winreg.KEY_WRITE,
            )
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, menu_name)
            if icon:
                winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, icon)
            winreg.CloseKey(key)

            cmd_key = winreg.CreateKeyEx(
                winreg.HKEY_CLASSES_ROOT,
                f"{base_key}\\{menu_name}\\command",
                0,
                winreg.KEY_WRITE,
            )
            winreg.SetValueEx(cmd_key, "", 0, winreg.REG_SZ, command)
            winreg.CloseKey(cmd_key)
            return f"Context menu entry '{menu_name}' added."
        except PermissionError:
            return "Error: Administrator privileges required to modify context menu."
        except Exception as e:
            return f"Context menu error: {e}"

    elif sub_action == "remove":
        if not menu_name:
            return "Error: 'name' is required."
        cmd = f'reg delete "HKCR\\Directory\\Background\\shell\\{menu_name}" /f'
        result = _run_cmd(cmd)
        return f"Context menu entry '{menu_name}' removed. {result}"

    elif sub_action == "list":
        cmd = 'reg query "HKCR\\Directory\\Background\\shell" /s'
        output = _run_cmd(cmd)
        if not output or "Error" in output:
            return "Could not list context menu entries or none found."
        # Truncate if too long
        if len(output) > 3000:
            output = output[:3000] + "\n... (truncated)"
        return f"Context menu entries:\n{output}"

    else:
        return f"Unknown sub_action for context_menu: '{sub_action}'. Use add/remove/list."


# ═══════════════════════════════════════════
# SYSTEM INFORMATION
# ═══════════════════════════════════════════

def system_info(params: dict, player=None) -> str:
    """Get comprehensive system information."""
    _require_windows()
    sub_action = (params.get("sub_action") or "summary").lower().strip()

    if sub_action == "summary":
        cmd = (
            "$os = Get-CimInstance Win32_OperatingSystem; "
            "$cpu = Get-CimInstance Win32_Processor; "
            "$mem = Get-CimInstance Win32_PhysicalMemory | Measure-Object Capacity -Sum; "
            "$disk = Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3'; "
            "Write-Output \"OS: $($os.Caption) $($os.Version)\"; "
            "Write-Output \"Computer: $($os.CSName)\"; "
            "Write-Output \"CPU: $($cpu.Name)\"; "
            "Write-Output \"RAM: $([math]::Round($mem.Sum / 1GB, 2)) GB\"; "
            "Write-Output \"Uptime: $((Get-Date) - $os.LastBootUpTime)\"; "
            "foreach ($d in $disk) { "
            "Write-Output \"Disk $($d.DeviceID): $([math]::Round($d.FreeSpace/1GB,1))GB free / $([math]::Round($d.Size/1GB,1))GB total\" }"
        )
        return _run_powershell(cmd)

    elif sub_action == "cpu":
        cmd = "Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed, LoadPercentage | Format-List"
        return _run_powershell(cmd)

    elif sub_action == "memory":
        cmd = (
            "$os = Get-CimInstance Win32_OperatingSystem; "
            "Write-Output \"Total: $([math]::Round($os.TotalVisibleMemorySize/1MB, 2)) GB\"; "
            "Write-Output \"Free: $([math]::Round($os.FreePhysicalMemory/1MB, 2)) GB\"; "
            "Write-Output \"Used: $([math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory)/1MB, 2)) GB\""
        )
        return _run_powershell(cmd)

    elif sub_action == "disk":
        cmd = "Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' | Select-Object DeviceID, @{N='SizeGB';E={[math]::Round($_.Size/1GB,1)}}, @{N='FreeGB';E={[math]::Round($_.FreeSpace/1GB,1)}} | Format-Table -AutoSize"
        return _run_powershell(cmd)

    elif sub_action == "network":
        cmd = "Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike '*Loopback*' } | Select-Object InterfaceAlias, IPAddress | Format-Table -AutoSize"
        return _run_powershell(cmd)

    elif sub_action == "processes":
        count = int(params.get("count", 15))
        cmd = f"Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First {count} Name, @{{N='MemMB';E={{[math]::Round($_.WorkingSet64/1MB,1)}}}}, CPU | Format-Table -AutoSize"
        return _run_powershell(cmd)

    else:
        return f"Unknown sub_action for system_info: '{sub_action}'. Use summary/cpu/memory/disk/network/processes."


# ═══════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════

def windows_max_control(parameters: dict = None, response=None, player=None, session_memory=None) -> str:
    """
    Comprehensive Windows system control.

    parameters:
      action: services | registry | notification | clipboard | virtual_desktop |
              startup | env_vars | installed_apps | windows_update | firewall |
              defender | taskbar | context_menu | system_info
      sub_action: depends on action (e.g., list/start/stop for services)
      ... additional params depend on action/sub_action
    """
    params = parameters or {}
    action = (params.get("action") or "").lower().strip()

    if player:
        player.write_log(f"[win_max_ctrl] {action or 'unknown'}")

    try:
        if action in ("services", "service", "manage_services"):
            return manage_services(params, player)

        elif action in ("registry", "reg", "manage_registry"):
            return manage_registry(params, player)

        elif action in ("notification", "notify", "send_notification"):
            return send_notification(params, player)

        elif action in ("clipboard", "manage_clipboard"):
            return manage_clipboard(params, player)

        elif action in ("virtual_desktop", "desktop", "manage_virtual_desktop"):
            return manage_virtual_desktop(params, player)

        elif action in ("startup", "startup_programs", "manage_startup"):
            return manage_startup(params, player)

        elif action in ("env_vars", "environment", "manage_env_vars"):
            return manage_env_vars(params, player)

        elif action in ("installed_apps", "apps", "list_installed_apps"):
            return list_installed_apps(params, player)

        elif action in ("windows_update", "update", "windows_update_status"):
            return windows_update_status(params, player)

        elif action in ("firewall", "manage_firewall"):
            return manage_firewall(params, player)

        elif action in ("defender", "manage_defender"):
            return manage_defender(params, player)

        elif action in ("taskbar", "manage_taskbar"):
            return manage_taskbar(params, player)

        elif action in ("context_menu", "manage_context_menu"):
            return manage_context_menu(params, player)

        elif action in ("system_info", "sysinfo", "info"):
            return system_info(params, player)

        else:
            return (
                f"Unknown action: '{action}'. Available actions: "
                "services, registry, notification, clipboard, virtual_desktop, "
                "startup, env_vars, installed_apps, windows_update, firewall, "
                "defender, taskbar, context_menu, system_info"
            )

    except RuntimeError as e:
        return str(e)
    except Exception as e:
        return f"windows_max_control error: {e}"
