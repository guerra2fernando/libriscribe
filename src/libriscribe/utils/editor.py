import os
import shlex
import subprocess
import sys


def open_file_in_editor(filename: str) -> bool:
    editor = os.environ.get("EDITOR", "").strip()
    if editor:
        subprocess.run([*shlex.split(editor), filename], check=False)
        return True

    if sys.platform.startswith("win"):
        os.startfile(filename)  # type: ignore[attr-defined]
        return True

    if sys.platform == "darwin":
        subprocess.run(["open", filename], check=False)
        return True

    subprocess.run(["xdg-open", filename], check=False)
    return True
