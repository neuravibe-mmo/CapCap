import os
import subprocess
import sys
from pathlib import Path


def bundle_root() -> str:
    meipass = getattr(sys, "_MEIPASS", "")
    if meipass:
        return os.path.abspath(str(meipass))
    if getattr(sys, "frozen", False):
        internal_dir = os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "_internal")
        if os.path.isdir(internal_dir):
            return internal_dir
    return str(Path(__file__).resolve().parents[1])


def workspace_root() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return str(Path(__file__).resolve().parents[1])


def join_root(*parts: str) -> str:
    return os.path.join(workspace_root(), *parts)


def asset_path(*parts: str) -> str:
    return first_existing_path(
        join_root("assets", *parts),
        os.path.join(bundle_root(), "assets", *parts),
    )


def app_path(*parts: str) -> str:
    return first_existing_path(
        join_root("app", *parts),
        os.path.join(bundle_root(), "app", *parts),
    )


def first_existing_path(*candidates: str) -> str:
    for candidate in candidates:
        path = str(candidate or "").strip()
        if path and os.path.exists(path):
            return path
    return str(candidates[0] if candidates else "")


def bin_path(*parts: str) -> str:
    import shutil

    cleaned_parts = list(parts)
    if sys.platform != "win32":
        cleaned_parts = [p[:-4] if p.lower().endswith(".exe") else p for p in cleaned_parts]

    name = cleaned_parts[-1] if cleaned_parts else ""

    candidates = [
        os.path.join(bundle_root(), "bin", *cleaned_parts),
        join_root("bin", *cleaned_parts),
        os.path.join(os.getcwd(), "bin", *cleaned_parts),
        os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "bin", *cleaned_parts),
    ]

    for candidate in candidates:
        if os.path.isfile(candidate) and (sys.platform == "win32" or os.access(candidate, os.X_OK)):
            return candidate
        if os.path.isdir(candidate) and name:
            sub_exe = os.path.join(candidate, name)
            if sys.platform == "win32":
                sub_exe_win = sub_exe + ".exe"
                if os.path.isfile(sub_exe_win):
                    return sub_exe_win
            if os.path.isfile(sub_exe) and os.access(sub_exe, os.X_OK):
                return sub_exe

    if name:
        sys_binary = shutil.which(name)
        if sys_binary:
            return sys_binary

    return first_existing_path(*candidates)


def models_path(*parts: str) -> str:
    return first_existing_path(
        join_root("models", *parts),
        os.path.join(bundle_root(), "models", *parts),
    )


def temp_path(*parts: str) -> str:
    return join_root("temp", *parts)


def output_path(*parts: str) -> str:
    return join_root("output", *parts)


def subprocess_hidden_kwargs() -> dict:
    """Return Windows flags that keep console child processes invisible.

    The GUI build has no console of its own.  Without these flags, console
    programs such as FFmpeg/FFprobe create a temporary console window every
    time they start, which causes visible flashes and adds process-launch
    overhead.  The debug console build remains unaffected.
    """
    if os.name != "nt":
        return {}
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = getattr(subprocess, "SW_HIDE", 0)
    return {
        "startupinfo": startupinfo,
        "creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0),
    }
