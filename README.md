# Interactive Globe System

A touch-free video kiosk controlled by hand gestures. A webcam watches the visitor. Showing a hand or swiping it left or right moves the show forward through a sequence of videos. Everything runs offline in a web browser on one Windows PC.

---

## How it works (visitor experience)

```
 ┌──────────────────────────────┐
 │ 1. Start screen              │  Background_Video.mp4 loops
 │    "Show your hand on Globe" │  ← visitor holds an open hand in the center (~0.8 s)
 └──────────────┬───────────────┘
                ▼
 2. Intro_and_Instruction_Video1.mp4 plays
                ▼
 3. "Move your hand left to right"   ← visitor swipes left → right
                ▼
 4. Video11.mp4 plays
                ▼
 5. LEFT ARROW key is pressed automatically, then a 5-second pause
                ▼
 6. Intro_and_Instruction_Video2.mp4 plays
                ▼
 7. "Move your hand right to left"   ← visitor swipes right → left
                ▼
 8. Video22.mp4 plays
                ▼
 9. RIGHT ARROW key is pressed automatically, then a 5-second pause
                ▼
    back to step 1
```

- Left and right are from the **visitor's point of view** (standing in front of the camera).
- If nobody swipes for 60 seconds on an instruction screen, the system goes back to the start screen.
- Only the **detection zone** is analysed. The camera image is cut down to the zone before hand detection, so a hand outside it is never detected at all (people walking past, for example). Only **one hand** is tracked at a time. You set the zone yourself with the setup page (see below).
- At the start screen, a fist does not start the show. Only an **open hand** in the zone does.

---

## Requirements

| Item | Notes |
|---|---|
| Windows 10 / 11 PC | The automatic arrow-key presses use Windows |
| Python 3.8 or newer | Must be available as `python` in the command line. For the ESP32 light, also install **pyserial**: `python -m pip install pyserial` |
| Google Chrome (recommended) or Microsoft Edge | |
| Webcam | Any USB or built-in camera. Place it so it faces the visitor. |
| ESP32 (optional) | Connected by USB; switches a light through a relay (see *ESP32 light*) |

No internet connection is needed. The hand-tracking files are included in the folder.

---

## How to run

### Step 1: Set the detection zone (first time, or after moving the camera)
Double-click **`setup.bat`**. A window opens with the live camera and a box drawn on it.

- **Move** the zone by dragging the box.
- **Resize** it by dragging the round handles on the corners and edges.
- With the keyboard: **Arrow keys** move it and **Shift + Arrow keys** resize it.
- **Test it:** hold your hand up. The box turns **green** when your hand is inside the zone.
- Click **Save Zone**. The zone is saved to `zone.json` and is used by the main system from then on.
- **Save & Run System ▶** saves and switches straight to the main system in the same window.
- **Reset** puts the zone back to the default (click Save afterwards to keep it).

You only need to do this again if the camera is moved or you want a different area. Then close the setup window and continue with Step 2.

### Step 2: Run the system

#### Option A: Kiosk mode (for the exhibit)
Double-click **`start.bat`**.

- It starts the local server (a minimized window called **"Globe Server"**). Leave it running.
- It opens Chrome **fullscreen in kiosk mode**, with camera access and video sound allowed automatically.

**To stop:** press **Alt+F4** to close the browser, then close the "Globe Server" window.

> If a "Globe Server" window is still open from the setup step, that's fine. The system uses the server that's already running.

#### Option B: Normal browser window (for testing)
Open a terminal in this folder and run:

```
python server.py
```

The browser opens `http://localhost:8000/index.html`. To open the setup page this way instead, run `python server.py setup.html`.

1. Click **Allow** when it asks to use the camera.
2. Click once on the page so videos can play with sound.
3. Press **F** for fullscreen.

**To stop:** press **Ctrl+C** in the terminal.

> ⚠️ **Do not open `index.html` by double-clicking it.** The camera and the automatic arrow keys only work when the page is opened through the server (`start.bat` or `python server.py`).

---

## Keyboard shortcuts

| Key | Action |
|---|---|
| **D** | Show or hide the **debug view**: a camera preview with the detected hand points, the saved detection zone (turns green when the hand is accepted), the swipe path (pink line) and the current step |
| **Space** | Pretend the current gesture happened (show hand or swipe). Useful for testing without a camera |
| **H** | Go back to the start screen |
| **F** | Toggle fullscreen |

---

## Folder structure

```
Interactive_Glob_System/
├── setup.bat            Opens the detection zone setup page
├── start.bat            Starts the main system in kiosk mode
├── server.py            Local web server; saves the zone and presses the real Windows arrow keys
├── setup.html           Detection zone setup page
├── index.html           The main app: screens, gesture detection, video flow, settings
├── server.log           What the server did: key presses, ESP32 messages, errors (created automatically)
├── zone.json            The saved detection zone (created when you click Save in setup)
├── README.md            This file
├── BG/
│   └── bg_image.png     Shown while the background video loads
├── Videos/
│   ├── Background_Video.mp4               Loops on the start screen
│   ├── Intro_and_Instruction_Video1.mp4   Plays after the hand is shown
│   ├── Video11.mp4                        Plays after the left → right swipe
│   ├── Intro_and_Instruction_Video2.mp4   Plays after the 5-second pause
│   └── Video22.mp4                        Plays after the right → left swipe
├── lib/                 Hand-tracking engine (Google MediaPipe), stored locally
└── models/
    └── hand_landmarker.task   Hand-tracking model
```

### Replacing videos or the background
Replace a file in `Videos/` or `BG/` with a new one **using exactly the same file name**, then reload the page (**F5**, or restart `start.bat`). Videos should be **.mp4 (H.264)** files.

---

## Settings

All settings are in **`index.html`**, in the `CONFIG` block near the top of the `<script>` section. Open it in any text editor, change a value, save, and reload the page.

| Setting | Default | Meaning |
|---|---|---|
| `zone` | `x0: 0.25, x1: 0.75, y0: 0.15, y1: 0.85` | Default detection zone, used only when no zone has been saved. **Use `setup.bat` instead of editing this** |
| `holdMs` | `800` | How long (in milliseconds) the hand must be held in the center to start |
| `requireOpenPalm` | `true` | `true` = only an open hand starts the show; `false` = any hand |
| `releaseMs` | `500` | The hand must leave for this long before it can trigger again |
| `edgeMargin` | `0.08` | The tracker looks this far (8% of the camera image) past the zone edge, so a hand crossing the edge isn't lost. Only a palm whose center is inside the zone counts |
| `swipeDistance` | `0.35` | How far the hand must move for a swipe (0.35 = about a third of the zone's width) |
| `swipeTimeMs` | `1200` | The swipe must be done within this time |
| `swipeGapMs` | `400` | A swipe still counts if the hand is lost for up to this long (blurry fast movement) |
| `mirror` | `true` | If swipe directions come out reversed, change to `false` |
| `waitAfterVideoMs` | `5000` | Pause after Video1 / Video2 (5000 = 5 seconds) |
| `sendOsKeys` | `true` | `true` = also press the real Windows Left/Right arrow key; `false` = only inside the page |
| `promptTimeoutMs` | `60000` | Go back to the start if nobody swipes for this long (0 = never) |
| `texts` | | All on-screen messages |

---

## About the automatic arrow keys

After Video1 ends the system presses **Left Arrow**. After Video2 ends it presses **Right Arrow**. The key is sent in two ways:

1. **Inside the web page**, for anything in the page that listens for arrow keys.
2. **As a real Windows key press**: the page asks `server.py` to press the key through the Windows API.

A real key press goes to whichever window is **focused** at that moment. In kiosk mode that is the browser itself. If the arrow keys are meant to control a different program, that program must be the focused window.

---

## ESP32 light

When the system presses an arrow key, `server.py` also sends the same command as text over USB serial (115200 baud) to the ESP32:

| Moment | Sent to ESP32 |
|---|---|
| Video1 ends | `LEFT` (the ESP32 switches the light **on for 5 seconds**) |
| Video2 ends | `RIGHT` (the current ESP32 code ignores it; available if you want to use it later) |

- The ESP32 is **found automatically** when the server starts (boards with CH340/CH9102, CP210x, FTDI or Espressif USB chips). The "Globe Server" window shows `ESP32: connected on COM3`, for example.
- To choose a port yourself, set it before starting: `set ESP32_PORT=COM3` (or `off` to disable the ESP32). You can put this line in `start.bat` before `start "Globe Server" ...`.
- If the ESP32 is unplugged and plugged back in, the server reconnects at the next command.
- **Close the Arduino IDE Serial Monitor** while the system runs. Only one program can use the COM port at a time.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Red message: *"Camera not available"* | Close other apps using the webcam (Zoom, Teams, Camera app), check the camera is plugged in, then reload (**F5**) |
| Page says *"can't connect"* | The server is not running. Start `start.bat` or `python server.py` again |
| `python` is not recognized | Install Python from python.org and tick **"Add Python to PATH"** during setup |
| Videos play without sound | Click once on the page, or use `start.bat` (it allows sound automatically) |
| Hand is not detected | Press **D** to see what the camera sees. Improve lighting, move closer, keep the hand open and in the center |
| Swipes go the wrong way | Set `mirror: false` in the settings |
| Swipes are too hard / too easy to trigger | Lower / raise `swipeDistance`, or raise / lower `swipeTimeMs`. During a swipe prompt, a glowing dot on the arrow follows the hand: if the dot doesn't appear, the hand isn't being detected (check light and the zone) |
| Show starts by accident | Raise `holdMs`, or make the zone smaller with `setup.bat` |
| Hand is never accepted | Run `setup.bat` and check that the box turns green when your hand is where visitors will stand |
| Zone changes are not used | Click **Save Zone** in the setup page, then reload the main system (**F5**) |
| Arrow keys don't reach another program | That program must be the focused window (see *About the automatic arrow keys*) |
| ESP32 light doesn't turn on / arrow key not pressed | Open **`server.log`** in the project folder. After Video1 ends it should show `key press: left -> sent`, `ESP32: sent LEFT` and the ESP32's reply. If nothing appears, close all "Globe Server" windows and start `start.bat` again (it always starts a fresh server). It should also say `ESP32: connected on COMx`. Close the Arduino Serial Monitor, check the USB cable, and restart the server. If it says *pyserial not installed*, run `python -m pip install pyserial` |
| Error after the server window was closed | Port 8000 may still be in use. Restart the PC or close the other program using port 8000 |

---

## Technical notes

- **Gesture detection:** [Google MediaPipe Hand Landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker) runs in the browser. It finds 21 points on the hand in each camera frame.
  - *Detection zone:* the zone is stored in `zone.json` as fractions (0–1) of the camera image, as seen in the mirrored preview. Each camera frame is cropped to the zone plus a small margin (`edgeMargin`) before it goes to the hand tracker, so hands away from the zone are never seen, and a hand counts only if its palm center is inside the zone.
  - *Performance:* hand tracking only runs while the system waits for a gesture (start screen and swipe prompts). It pauses while videos play, so playback stays smooth.
  - *Show hand:* the palm center must be inside the zone, at least 3 of 4 fingers must be straight, and the hand must stay there for `holdMs`.
  - *Swipe:* inside the zone, the palm center must travel `swipeDistance` × the zone's width sideways within `swipeTimeMs`, mostly sideways rather than up/down. Short tracking dropouts (up to `swipeGapMs`) don't cancel the swipe.
- **Why a local server is needed:** browsers only allow camera access on `http://localhost` or `https`, not on files opened directly from disk. The server also handles the real Windows key presses (`POST /key?k=left` or `right`) and saves the zone (`POST /zone`).
- **Kiosk flags used by `start.bat`:** `--kiosk` (fullscreen, no browser UI), `--autoplay-policy=no-user-gesture-required` (videos play with sound without a click), `--use-fake-ui-for-media-stream` (camera allowed without a prompt).
