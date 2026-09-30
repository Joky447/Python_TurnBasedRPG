"""Packages the game as a Windows program with PyInstaller.

Run from the project folder:
    python tools/build_exe.py

Result: dist/SpellsxBlades/SpellsxBlades.exe (keep the whole SpellsxBlades folder together, or zip it
to share the game). The player's save.json and settings.json are created next to the .exe.

Needs PyInstaller:  pip install pyinstaller
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "SpellsxBlades"
DATA = ["character", "mobs_boss", "map", "menu_ui", "items", "sound_effects", "cache"]


def main():
    os.chdir(ROOT)
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onedir", "--windowed", "--name", NAME]
    if os.path.exists("icon.ico"):
        cmd += ["--icon", "icon.ico"]      # made by tools/make_icon.py
    for folder in DATA:
        if os.path.isdir(folder):
            cmd += ["--add-data", f"{folder}{os.pathsep}{folder}"]
    cmd.append("main.py")
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"\nDone: {os.path.join(ROOT, 'dist', NAME, NAME + '.exe')}")


if __name__ == "__main__":
    main()
