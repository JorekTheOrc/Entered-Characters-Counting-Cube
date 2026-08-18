<h1 align="center"> ⌨️ Entered Characters Counting Cube (PyQt5)</h1>
<p align="center">
  <img width="119" height="120" alt="Animation" src="https://github.com/user-attachments/assets/000dbb83-1cc5-42d0-aeb1-e48a83aa418b" />
</p>

<p align="center">
  A compact and interactive desktop widget that tracks keystrokes and mouse clicks, calculates typing speed (CPM/WPM), logs detailed session statistics, and responds with procedural visual effects.
</p>

<p align="center">
  <a href="README.md">Русский</a> | <strong>English</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/PyQt5-5.15+-green.svg" alt="PyQt5">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg" alt="Platform">
  <img src="https://img.shields.io/badge/License-MIT-brightgreen.svg" alt="License">
</p>

---

## ✨ Key Features

* **📊 Three Display Modes:** Switch between Counter, Elapsed Time, and Typing Speed with a single left click.
* **🔥 Dynamic Heat System:** Typing faster dynamically accelerates the neon border color cycle and generates extra glowing spark particles inside the widget.
* **🎨 Procedural Visual Effects:**
  * **Text Shake:** Subtle shaking feedback on every keystroke.
  * **Sparks (Particles):** Dynamic particles radiating from the center and dissolving within the rounded border boundaries.
  * **Ripples:** Expanding wave animations triggered on mouse clicks.
* **📥 Detailed Session Logging:** Automatically writes session statistics (launch time, exit time, uptime, keystroke count, and mouse click count) to `stats_log.txt` located in the system `AppData` directory.
* **💾 Automatic Settings Persistence:** Remembers widget position, interface language, and lock status across application restarts via `QSettings`.
* **🌐 Multilingual UI:** Seamlessly switch between Russian and English via the context menu.
* **🔔 System Tray Integration:** Minimize the widget to the tray using the middle mouse button (scroll wheel) or via the context menu.
* **🔲 Minimalist Design:** Frameless translucent window with a smooth "breathing" border effect.

---

## ⚡ Display Modes

Switch the displayed information by left-clicking the cube:

| Mode | Information Displayed | Details |
| :--- | :--- | :--- |
| **Counter** | Total actions during the session | Accompanied by text shake and spark particle bursts. |
| **Time** | Start time and total session duration | Display format: `HH:MM:SS`. |
| **Speed** | Typing speed in CPM and WPM | Calculated in real-time over a sliding 60-second window. |
<p align="center">
  <img width="233" height="209" alt="Animation4" src="https://github.com/user-attachments/assets/3896894e-10bc-44a0-9bea-95ff54031da5" />
</p>

---

## ⚙️ Input Filtering

By default, the application runs in **smart character count mode**:
* Ignores modifier keys (`Ctrl`, `Alt`, `Win`).
* Ignores navigation and functional keys (`Enter`, `Backspace`, `Tab`, arrow keys, `Page Up/Down`, etc.).
* Spaces are counted only when pressed without modifier keys.

When **"Count mouse clicks"** is enabled:
* Mouse clicks are tracked alongside keystrokes and trigger circular ripple effects.
* Keystrokes and mouse clicks are tracked separately in the session log.

---

## ⌨️ Controls

| Action | Result |
| :--- | :--- |
| **Left Click** | Toggle display mode (Counter ➡️ Time ➡️ Speed) |
| **Left Click + Drag** | Move the cube across the screen (when unlocked) |
| **Middle Click (Wheel)** | Minimize to tray / Restore from tray |
| **Right Click** | Open settings context menu |

### Context Menu (Right Click):
* **Count mouse clicks** — Toggle mouse click tracking.
* **Lock / Unlock** — Prevent accidental dragging.
* **Pause / Resume Counting** — Temporarily pause input tracking.
* **Reset Counter** — Reset current counts and heat meter to zero.
* **Hide to tray** — Minimize widget to system notification area.
* **Open Stats Log** — Open `stats_log.txt` in your default text editor.
* **Language \ Язык** — Switch interface language (Русский / English).
* **Exit** — Save session logs and exit the application.
<p align="center">
  <img width="604" height="398" alt="Animation2" src="https://github.com/user-attachments/assets/0eb6f3c4-4002-4226-ba04-f51452f11b1c" />
</p>

---

## 🚀 Running the Application

### Option 1. Standalone Executable (Windows)
1. Download `KeyboardCube.exe` from the [Releases](https://github.com/JorekTheOrc/Entered-Characters-Counting-Cube/releases) page (or grab it from the repository root).
2. Run the `.exe` by double-clicking.

---

### Option 2. Running from Source (Cross-platform)

#### 1. Prerequisites
Ensure **Python 3.8+** is installed on your system.

#### 2. Clone the Repository
```bash
git clone https://github.com/JorekTheOrc/Entered-Characters-Counting-Cube.git
cd Entered-Characters-Counting-Cube
```

#### 3. Install Dependencies
```bash
py -m pip install PyQt5 pynput
```
*(or `python -m pip install PyQt5 pynput`)*

#### 4. Run the Script
```bash
py char_counter.py
```
*(or `python char_counter.py`)*

---

## 🛠️ Building an Executable with PyInstaller

To bundle the project into a single standalone `.exe` file:

1. Install PyInstaller:
   ```cmd
   py -m pip install pyinstaller
   ```
2. Build using the provided `.spec` file:
   ```cmd
   py -m PyInstaller KeyboardCube.spec
   ```
   *(or directly: `py -m PyInstaller --noconsole --onefile --name "KeyboardCube" char_counter.py`)*

The generated binary will be located in **`dist/KeyboardCube.exe`**.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
