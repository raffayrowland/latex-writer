#!/usr/bin/env python3
import sys
from copy_latex.core import capture_selection_b64, copy_clipboard
from copy_latex.transcribe import getLatex

def main():
    args = sys.argv[1:]
    cmd = args[0] if args else "screenshot"

    if cmd == "screenshot":
        b64 = capture_selection_b64()

    else:
        print("usage: copy_latex screenshot")
        sys.exit(2)

    latex = getLatex(b64)
    print(latex)
    copy_clipboard(latex)
