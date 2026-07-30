<h1 align="center"> ⌨️ Entered Characters Counting Cube (PyQt5)</h1>
<p align="center">
  <img width="119" height="120" alt="Animation" src="https://github.com/user-attachments/assets/000dbb83-1cc5-42d0-aeb1-e48a83aa418b" />
</p>

<p align="center">
  A compact interactive desktop widget that tracks keystrokes, calculates typing speed (CPM/WPM), and displays session uptime, all accompanied by procedural visual effects.
</p>

<p align="center">
  <a href="README.md">Русский</a> | <strong>Read in English</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/PyQt5-5.15+-green.svg" alt="PyQt5">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg" alt="Platform">
  <img src="https://img.shields.io/badge/License-MIT-brightgreen.svg" alt="License">
</p>

---

## ✨ Key Features

* **📊 Three Display Modes:** Switch between metrics with a single left-click on the cube.
* **🌐 Bilingual Interface:** Support for Russian and English languages with dynamic switching of text labels and menu options.
* **🔥 Dynamic Heat System:** The faster you type, the quicker the neon border changes its color, and more particles (sparks) are generated inside.
* **🎨 Procedural Visual Effects:**
  * **Shake Effect:** A subtle text jitter triggered when typing.
  * **Spark Particles:** Particles burst from the center on keystrokes, fading out naturally while being contained inside the widget borders.
  * **Ripple Effect:** Circular waves radiating inside the cube upon mouse clicks (when button masher mode is active).
* **🔒 Layout Controls:** Lock the widget position, pause counting, or toggle key filters directly from the context menu.
* **🔲 Minimalist Design:** Frameless translucent window with a subtle border breathing animation.

---

## ⚡ Operating & Display Modes

You can cycle through the display modes by left-clicking the cube:

| Mode | Information Displayed | Features |
| :--- | :--- | :--- |
| **Counter** | Total number of keystrokes | Accompanied by digit shaking and spark bursts on input. |
| **Time** | Start time and elapsed session duration | Time format automatically adapts to the chosen language. |
| **Speed** | Typing speed in CPM and WPM | Calculated in real-time using a 60-second sliding window. |

<p align="center">
  <img width="233" height="209" alt="Animation4" src="https://github.com/user-attachments/assets/3896894e-10bc-44a0-9bea-95ff54031da5" />
</p>

---

## ⚙️ Input Filtering

The program records **only individual physical key presses** (holding down keys and OS autorepeat are completely ignored in all modes).

By default, the widget operates in **Smart Counting Mode**:
* System modifier keys (`Ctrl`, `Alt`, `Win`) are ignored.
* Navigation and command keys (`Enter`, `Backspace`, `Tab`, arrows, `Page Up/Down`, etc.) are ignored.
* The Spacebar is counted only when pressed without modifiers.

In **Button Masher Mode** (can be enabled via the context menu):
* All individual key presses and hotkey combinations are counted.
* Mouse clicks are also counted and produce a circular ripple effect.

---

## ⌨️ Widget Controls

| Action | Result |
| :--- | :--- |
| **Left Click (LMB)** | Switch display mode (Counter ➡️ Time ➡️ Speed) |
| **Hold LMB & Drag** | Drag the cube across the screen (if unlocked) |
| **Right Click (RMB)** | Open settings context menu |

### Settings Menu (RMB):
* **Count all keys and combinations** — activates Button Masher mode.
* **Lock / Unlock** — prevents accidental dragging of the widget.
* **Pause / Resume Counting** — temporarily pauses activity tracking.
* **Reset Counter** — resets keystroke statistics and heat level.
* **Language \ Язык** — toggles the interface language (Русский / English).
* **Exit** — closes the application.

<p align="center">
  <img width="604" height="398" alt="Animation2" src="https://github.com/user-attachments/assets/0eb6f3c4-4002-4226-ba04-f51452f11b1c" />
</p>

---

## 📥 Requirements & Installation

### Requirements
This script requires Python 3.8 or higher. Dependencies can be installed using:

```bash
pip install PyQt5 pynput
```
