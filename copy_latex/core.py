import base64
import os
import shutil
import subprocess
import tempfile
import pathlib
import atexit
from copy_latex.transcribe import getLatex
from dotenv import load_dotenv

load_dotenv()

def have(cmd): return shutil.which(cmd) is not None

def run(cmd, **kw):
    return subprocess.run(cmd, check=True, text=True, capture_output=True, **kw)

def notify(summary: str, body: str | None = None):
    if have("notify-send"):
        try:
            args = ["notify-send", "--app-name=copy_latex", summary]
            if body: args.append(body)
            subprocess.run(args, check=True)
        except Exception:
            pass  # best-effort


def copy_clipboard(text: str) -> bool:
    copy_clipboard.last_error = None
    TIMEOUT = float(os.environ.get("CLIP_TIMEOUT", "2.0"))
    wayland = bool(os.environ.get("WAYLAND_DISPLAY"))

    if wayland:
        if have("wl-copy"):
            try:
                r = subprocess.run(["wl-copy"], input=text, text=True,
                                   capture_output=True, timeout=TIMEOUT)
                if r.returncode == 0: return True
                copy_clipboard.last_error = f"wl-copy exited {r.returncode}: {(r.stderr or '').strip() or 'no stderr'}"
            except subprocess.TimeoutExpired:
                copy_clipboard.last_error = f"wl-copy timed out after {TIMEOUT}s"
            except Exception as e:
                copy_clipboard.last_error = f"wl-copy error: {e}"
        else:
            copy_clipboard.last_error = "Wayland detected but wl-copy not installed"
        # last resort
        try:
            import pyperclip
            pyperclip.copy(text); return True
        except Exception as e:
            copy_clipboard.last_error = copy_clipboard.last_error or f"pyperclip error: {e}"
            return False

    # X11 path
    for cmd in (["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]):
        if not have(cmd[0]): continue
        try:
            r = subprocess.run(cmd, input=text, text=True,
                               capture_output=True, timeout=TIMEOUT)
            if r.returncode == 0: return True
            copy_clipboard.last_error = f"{cmd[0]} exited {r.returncode}: {(r.stderr or '').strip() or 'no stderr'}"
        except subprocess.TimeoutExpired:
            copy_clipboard.last_error = f"{cmd[0]} timed out after {TIMEOUT}s"
        except Exception as e:
            copy_clipboard.last_error = f"{cmd[0]} error: {e}"

    try:
        import pyperclip
        pyperclip.copy(text); return True
    except Exception as e:
        copy_clipboard.last_error = f"pyperclip error: {e}"
        return False


def _capture_png(tmp_png: str):
    wayland = bool(os.environ.get("WAYLAND_DISPLAY"))
    if wayland:
        if have("grim") and have("slurp"):
            geom = run(["slurp", "-f", "%x,%y %wx%h"]).stdout.strip()
            run(["grim", "-g", geom, tmp_png])
            return
        raise RuntimeError("Install grim+slurp")
    if have("maim"):
        run(["maim", "-s", tmp_png]); return
    raise RuntimeError("Install maim or scrot or ImageMagick 'import'.")

def capture_selection_b64(copy_to_clipboard: bool=False) -> str:
    fd, tmp = tempfile.mkstemp(suffix=".png"); os.close(fd)
    atexit.register(lambda: os.path.exists(tmp) and os.remove(tmp))
    _capture_png(tmp)
    b64 = base64.b64encode(pathlib.Path(tmp).read_bytes()).decode("ascii")
    if copy_to_clipboard:
        if os.environ.get("WAYLAND_DISPLAY") and have("wl-copy"):
            p = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE, text=True); p.communicate(b64)
    return b64

if __name__ == "__main__":
    import sys
    img_b64 = capture_selection_b64()
    print(f"got {len(img_b64)} base64 chars")
    print(img_b64)
    latex = getLatex(img_b64)
    print(latex)
    ok = copy_clipboard(latex)

    if ok:
        notify("LaTeX copied to clipboard")
    else:
        err = getattr(copy_clipboard, "last_error", "unknown error")
        notify("Failed to copy LaTeX", err)
        print(f"copy failed: {err}", file=sys.stderr)

