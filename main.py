import base64
import os
import shutil
import subprocess
import tempfile
import pathlib
import atexit

def have(cmd): return shutil.which(cmd) is not None

def run(cmd, **kw):
    return subprocess.run(cmd, check=True, text=True, capture_output=True, **kw)

def _capture_png(tmp_png: str):
    wayland = bool(os.environ.get("WAYLAND_DISPLAY"))
    if wayland:
        if have("grim") and have("slurp"):
            geom = run(["slurp", "-f", "%x,%y %wx%h"]).stdout.strip()
            run(["grim", "-g", geom, tmp_png])
            return
        if have("spectacle"):
            run(["spectacle", "-r", "-b", "-n", "-o", tmp_png]); return
        if have("gnome-screenshot"):
            run(["gnome-screenshot", "-a", "-f", tmp_png]); return
        raise RuntimeError("Install grim+slurp or spectacle or gnome-screenshot.")
    # X11
    if have("maim"): run(["maim", "-s", tmp_png]); return
    if have("scrot"): run(["scrot", "-s", tmp_png]); return
    if have("import"): run(["import", tmp_png]); return
    raise RuntimeError("Install maim or scrot or ImageMagick 'import'.")

def capture_selection_b64(copy_to_clipboard: bool=False) -> str:
    fd, tmp = tempfile.mkstemp(suffix=".png"); os.close(fd)
    atexit.register(lambda: os.path.exists(tmp) and os.remove(tmp))
    _capture_png(tmp)
    b64 = base64.b64encode(pathlib.Path(tmp).read_bytes()).decode("ascii")
    if copy_to_clipboard:
        if os.environ.get("WAYLAND_DISPLAY") and have("wl-copy"):
            p = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE, text=True); p.communicate(b64)
        elif have("xclip"):
            p = subprocess.Popen(["xclip","-selection","clipboard"], stdin=subprocess.PIPE, text=True); p.communicate(b64)
    return b64

# --- example usage ---
if __name__ == "__main__":
    img_b64 = capture_selection_b64()
    print(f"got {len(img_b64)} base64 chars")
    print(img_b64)
