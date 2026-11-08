# Chest Counter

A small, standalone Windows overlay for manually counting Fortnite chests.
Open a chest, tap **²**, and your session, daily, and all-time totals
increase by one. Holding the key counts once, rather than repeating.

## Start on Windows

1. Install **Python 3.10 or newer** from [python.org](https://www.python.org/downloads/windows/).
   Include Tcl/Tk (the default desktop installation does) and the Python launcher.
   Select **Add python.exe to PATH** in the installer.
2. Download this repository and double-click **Launch Chest Counter.bat**.
   Or run `py -3 main.py` from the repository folder.
3. Set Fortnite's display mode to **Windowed Fullscreen**, so Windows can display
   the separate overlay above it. Drag the overlay's header to position it.
4. Choose **Compact overlay** for just the session number followed by a real
   Fortnite chest image, with a transparent background on Windows. Press
   **Ctrl+Shift+L** to let mouse clicks pass through; press it again to unlock.
   **Ctrl+Shift+M** returns to the full controls. Right-clicking the compact
   overlay also returns to the controls when it is unlocked.

No `pip install`, account, API key, or administrator permissions are required.
This source download does require Python; it is not a prebuilt `.exe`.

The startup file checks that Python actually runs and includes Tk before opening
the app. It tries the Python launcher, PATH, other supported launcher versions,
and standard installation folders. Keep its console window open while using the
overlay; startup errors remain visible there.

### If Python Launcher says "Unable to create process"

This means the launcher points to a Python executable that was moved or deleted
(for example, a missing `Documents\python2\pythonw.exe`). Download the current ZIP
and extract it again: the updated startup file skips broken interpreter entries.
If it reports that no working Python was found, install or repair Python 3.10+
using the official installer above, with **Tcl/Tk** and **Add python.exe to PATH**
enabled. Then run **Launch Chest Counter.bat** again. Your saved chest counts are
kept separately from the app folder.

## Controls

| Action | Control |
| --- | --- |
| Count one chest | **²**, or **Add chest** |
| Correct a mistake | **Undo** (up to the last 100 additions in this session) |
| Pause or resume counting | **Ctrl+Shift+P**, or **Pause** |
| Switch full / compact view | **Ctrl+Shift+M**, or the view buttons |
| Toggle mouse click-through | **Ctrl+Shift+L** (Windows) |
| Close, including while locked | **Ctrl+Shift+Q**, or **×** in the full view |
| Reset this session, keep overall totals | **New session**, then confirm |
| Change the session goal | **Edit** beside the goal |

The all-time total, current session, daily total, best session, goal, and undo
history are saved locally after every change. A session resumes after closing
the app; **New session** starts another one. The daily counter follows your PC's
local calendar date. View mode, position, click-through, and pause are reset on
launch, so you always start with visible, unlocked controls.

## Separate from the game

The app never opens Fortnite's process or files, reads game memory, injects code,
uses game hooks, automates chest opening, or sends input to Fortnite. It only
queries Windows for the state of the ² key and its own shortcut keys, and
changes styles on its own window. It makes no network requests.

Counting is entirely manual. **²** works **regardless of which app is in
focus**; pause counting when you are not tracking chests. It is not swallowed or
remapped, so any existing ² binding in Fortnite still works. On French AZERTY
keyboards this is the key just left of `1`; on layouts without an unmodified ²
character the app uses that same physical key. Left Arrow no longer counts. Very short
taps between the 16 ms polling samples can be missed. An exclusive fullscreen
game can cover an ordinary desktop overlay; use Windowed Fullscreen.
Restart the app after changing your Windows keyboard layout so the count key
is resolved again.

## Your save file

On Windows: `%LOCALAPPDATA%\ChestCounter\state.json`.
Back up this file to keep or transfer your counts. Writes are atomic. If saving
fails, the app pauses and rolls back the unsaved change. If existing data cannot
be read, it reports the problem without replacing the file. A second Windows
instance using the same save file is rejected to prevent conflicting writes.

For a separate practice counter, run:

```powershell
py -3 main.py --data-file "C:\Users\YOUR_NAME\Documents\practice-counts.json"
```

## Development and verification

Python's standard library and Tk are the only runtime requirements.

```sh
python3 main.py
python3 -m unittest discover -v
```

On Linux/macOS the UI can be previewed and controlled with its buttons, but
background counting and click-through require Windows. Linux saves default to
`$XDG_DATA_HOME/chest-counter/state.json` or `~/.local/share/chest-counter/state.json`.

Tests without a desktop run the counter/storage suite and mark GUI tests skipped.
For the complete suite, use an available desktop display (or a headless X server),
for example `DISPLAY=:99 python3 -m unittest discover -v`.

Validated in this Linux cloud environment: **27 passing tests**, including real
Tk button interactions, keyboard-edge polling through a simulated OS adapter,
pause, compact layout, undo, session resets, daily rollover, persistence, and
write-failure recovery, the minimal number-and-image compact view, and simulated
Windows keyboard layouts for the ² key. Expanded and compact windows were also rendered and
visually inspected. The actual Windows APIs, launcher, click-through behavior,
and display over Fortnite still need a Windows machine for end-to-end validation.

The bundled Fortnite chest image and its source are documented in
[`assets/README.md`](assets/README.md). It is loaded locally; the app does not
download images or connect to Fortnite while running.
