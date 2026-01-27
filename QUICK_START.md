# 🚀 QUICK START GUIDE

## Starting the App

### Method 1: Simple Command (Recommended)
```bash
cd /Users/pranaydinavahi/personal_projects/vibe_coding/MiddleFinger
python3 camera.py
```

### Method 2: Using the Launcher Script
```bash
cd /Users/pranaydinavahi/personal_projects/vibe_coding/MiddleFinger
./run_camera.sh
```

### Method 3: From Anywhere
```bash
python3 /Users/pranaydinavahi/personal_projects/vibe_coding/MiddleFinger/camera.py
```

---

## Stopping the App

### Method 1: Press 'Q' Key
- While the app window is active
- Press the **Q** key
- App will close gracefully

### Method 2: Close Window
- Click the **X** button on the window
- Or press **Cmd+W** (macOS)

### Method 3: Terminal Interrupt
- In the terminal where it's running
- Press **Ctrl+C**
- App will stop immediately

---

## Quick Commands Cheat Sheet

```bash
# Navigate to project
cd /Users/pranaydinavahi/personal_projects/vibe_coding/MiddleFinger

# Start app
python3 camera.py

# Stop app (in terminal)
Ctrl+C

# Or press Q in the app window
```

---

## App Controls (While Running)

| Key | Action |
|-----|--------|
| **Thumbs Up 👍** | Show surprise image |
| **ESC** | Hide/close image |
| **T** | Show image (manual/testing) |
| **Q** | Quit app |

---

## Troubleshooting

### App Won't Start
```bash
# Check if camera is available
ls /dev/video*

# Check if Python is installed
python3 --version

# Reinstall dependencies
pip3 install opencv-python mediapipe numpy
```

### App Already Running
```bash
# Find the process
ps aux | grep camera.py

# Kill it
pkill -f camera.py

# Or find and kill by PID
ps aux | grep camera.py
kill <PID>
```

### Camera Permission Denied
```bash
# macOS: Reset camera permissions
tccutil reset Camera

# Then grant permission in:
# System Settings → Privacy & Security → Camera
```

---

## One-Line Commands

```bash
# Start (from anywhere)
python3 ~/personal_projects/vibe_coding/MiddleFinger/camera.py

# Stop all instances
pkill -f camera.py

# Check if running
ps aux | grep camera.py
```

---

## Auto-Start on Login (Optional)

### macOS:
1. Open **Automator**
2. Create new **Application**
3. Add "Run Shell Script"
4. Paste:
   ```bash
   cd /Users/pranaydinavahi/personal_projects/vibe_coding/MiddleFinger
   python3 camera.py
   ```
5. Save as "PositivityBoost.app"
6. Add to **Login Items** in System Settings

### Linux:
Add to `~/.bashrc` or create a systemd service

---

## Current Status

✅ **App is currently RUNNING**  
- Running for: 2m23s
- Window: "Positivity Boost"
- To stop: Press Q or Ctrl+C

---

## Quick Reference

**Start:** `python3 camera.py`  
**Stop:** Press `Q` or `Ctrl+C`  
**Location:** `/Users/pranaydinavahi/personal_projects/vibe_coding/MiddleFinger/`
