# 🎯 COMMAND REFERENCE

Quick reference for starting and stopping the Positivity Boost App.

---

## 📍 Location
```
/Users/pranaydinavahi/personal_projects/vibe_coding/MiddleFinger/
```

---

## ▶️ START THE APP

### Option 1: Direct Command
```bash
cd /Users/pranaydinavahi/personal_projects/vibe_coding/MiddleFinger
python3 camera.py
```

### Option 2: Launcher Script (Recommended)
```bash
cd /Users/pranaydinavahi/personal_projects/vibe_coding/MiddleFinger
./run_camera.sh
```

### Option 3: From Anywhere
```bash
python3 ~/personal_projects/vibe_coding/MiddleFinger/camera.py
```

---

## ⏹️ STOP THE APP

### Option 1: Press Q Key
- Make sure app window is active
- Press **Q**
- App closes gracefully

### Option 2: Stop Script
```bash
cd /Users/pranaydinavahi/personal_projects/vibe_coding/MiddleFinger
./stop_camera.sh
```

### Option 3: Terminal Interrupt
- In the terminal where app is running
- Press **Ctrl+C**

### Option 4: Kill Process
```bash
pkill -f camera.py
```

---

## 🎮 APP CONTROLS

While the app is running:

| Key | Action |
|-----|--------|
| **👍 Thumbs Up** | Show surprise image (gesture) |
| **ESC** | Hide/close the image |
| **T** | Show image manually (testing) |
| **Q** | Quit the app |

---

## 📋 COMMON COMMANDS

```bash
# Navigate to project
cd /Users/pranaydinavahi/personal_projects/vibe_coding/MiddleFinger

# Start app
./run_camera.sh

# Stop app
./stop_camera.sh

# Check if running
ps aux | grep camera.py

# View logs (if running in background)
tail -f /tmp/positivity_boost.log
```

---

## 🔧 TROUBLESHOOTING

### Check if App is Running
```bash
ps aux | grep camera.py
```

### Force Stop All Instances
```bash
pkill -9 -f camera.py
```

### Check Camera Access
```bash
# macOS
system_profiler SPCameraDataType

# Linux
ls /dev/video*
```

### Reinstall Dependencies
```bash
pip3 install --upgrade opencv-python mediapipe numpy
```

### Reset Camera Permissions (macOS)
```bash
tccutil reset Camera
# Then grant permission in System Settings
```

---

## 🚀 QUICK COPY-PASTE

### Start
```bash
cd ~/personal_projects/vibe_coding/MiddleFinger && python3 camera.py
```

### Stop
```bash
pkill -f camera.py
```

### Restart
```bash
pkill -f camera.py && sleep 1 && cd ~/personal_projects/vibe_coding/MiddleFinger && python3 camera.py
```

---

## 📁 PROJECT FILES

```
MiddleFinger/
├── camera.py           # Main app
├── run_camera.sh       # Start script
├── stop_camera.sh      # Stop script
├── QUICK_START.md      # Detailed guide
├── COMMANDS.md         # This file
└── photo/              # Image folder
```

---

## ✅ CURRENT STATUS

**App Status:** RUNNING  
**Window:** "Positivity Boost"  
**Runtime:** Check with `ps aux | grep camera.py`

**To stop now:**
```bash
./stop_camera.sh
```

**Or press Q in the app window**

---

## 💡 PRO TIPS

1. **Use the launcher script** - It checks dependencies automatically
2. **Press Q to quit** - Cleanest way to exit
3. **Use stop script** - If app is stuck or you can't find the window
4. **Check running processes** - `ps aux | grep camera.py`

---

**That's it! Simple commands for easy control! 🎉**
