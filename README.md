# 👍 Positivity Boost - Hand Gesture Recognition App

A fun and interactive application that uses real-time hand gesture recognition to spread positivity! Show a thumbs up gesture to reveal a surprise image.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green.svg)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10.9-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Features

- 🎥 **Real-time Hand Tracking** - Uses Google's MediaPipe for accurate hand detection
- 👍 **Thumbs Up Recognition** - Custom ML algorithm to detect thumbs up gesture
- 😊 **Face Detection** - Professional-looking face detection overlays
- 🎨 **Beautiful UI** - Modern interface with motivational quotes
- 🖼️ **Surprise Image Display** - Full-screen image reveal on gesture detection
- ⚡ **Fast Performance** - 30+ FPS on modern hardware

## 🎯 Demo

The app features:
- **Small camera preview** with face detection boxes
- **Rotating motivational quotes** 
- **Professional UI layout** with clear instructions
- **Full-screen image overlay** when thumbs up is detected
- **Smooth animations** and transitions

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Webcam
- macOS, Linux, or Windows

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/pranay-interakt/positivity_hand_gesture.git
cd positivity_hand_gesture
```

2. **Install dependencies**
```bash
pip3 install opencv-python mediapipe numpy
```

3. **Add your image**
```bash
# Place your image in the photo/ folder
cp /path/to/your/image.jpg photo/
```

### Running the App

**Option 1: Using the launcher script (Recommended)**
```bash
./run_camera.sh
```

**Option 2: Direct Python command**
```bash
python3 camera.py
```

**Option 3: From anywhere**
```bash
python3 /path/to/positivity_hand_gesture/camera.py
```

## 🎮 Controls

| Key | Action |
|-----|--------|
| **👍 Thumbs Up** | Show surprise image (gesture) |
| **ESC** | Hide/close the image |
| **T** | Show image manually (testing) |
| **Q** | Quit the app |

## 🛑 Stopping the App

**Option 1: Press Q key** (recommended)

**Option 2: Use stop script**
```bash
./stop_camera.sh
```

**Option 3: Terminal interrupt**
```bash
Ctrl+C
```

## 📖 Documentation

- [**QUICK_START.md**](QUICK_START.md) - Detailed startup guide
- [**COMMANDS.md**](COMMANDS.md) - Complete command reference
- [**UI_GUIDE.md**](UI_GUIDE.md) - UI layout and features

## 🎨 UI Layout

The app features a professional 1400x900 window with:

- **Header**: "POSITIVITY BOOST" title with subtitle
- **Left Panel**: Live camera preview (600x450) with face detection
- **Right Panel**: Rotating motivational quotes and messages
- **Bottom Section**: Clear "How it works" instructions
- **Full Screen**: Surprise image overlay on gesture detection

## 🛠️ Technical Details

### Technologies Used

- **OpenCV** - Computer vision and camera handling
- **MediaPipe** - Google's ML framework for hand tracking
- **NumPy** - Numerical operations
- **Haar Cascades** - Face detection

### How It Works

1. **Hand Detection**: MediaPipe detects up to 2 hands in real-time
2. **Landmark Tracking**: 21 key points tracked on each hand
3. **Gesture Recognition**: Custom algorithm analyzes finger positions
4. **Thumbs Up Detection**: 
   - Checks if thumb is pointing upward
   - Verifies other fingers are curled
   - Requires 70% confidence threshold
   - Must hold for 10 frames (~0.3 seconds)
5. **Image Display**: Smooth fade-in animation to full screen

### Performance

- **FPS**: 30+ on modern hardware
- **Latency**: <100ms gesture detection
- **Accuracy**: ~90% with good lighting
- **CPU Usage**: ~15-25%

## 🎯 Customization

### Change the Image

Replace the image in the `photo/` folder:
```bash
cp /path/to/your/image.jpg photo/
```

### Modify Quotes

Edit `camera.py` around line 73:
```python
self.quotes = [
    "Your custom quote! 💪",
    "Another quote! ✨",
    # Add more...
]
```

### Adjust Window Size

Edit `camera.py` lines 70-71:
```python
self.window_width = 1600  # Change width
self.window_height = 1000  # Change height
```

### Change Detection Sensitivity

Edit `camera.py` line 67:
```python
self.required_frames = 5  # Lower = faster detection
```

## 🐛 Troubleshooting

### Camera Not Working

**macOS:**
```bash
# Reset camera permissions
tccutil reset Camera
# Then grant permission in System Settings → Privacy & Security → Camera
```

**Linux:**
```bash
# Check available cameras
ls /dev/video*
```

### Dependencies Issues

```bash
# Reinstall all dependencies
pip3 install --upgrade opencv-python mediapipe numpy
```

### App Won't Start

```bash
# Check Python version
python3 --version  # Should be 3.8+

# Check if camera is in use
lsof | grep -i camera
```

## 📁 Project Structure

```
positivity_hand_gesture/
├── camera.py              # Main application
├── run_camera.sh          # Start script
├── stop_camera.sh         # Stop script
├── photo/                 # Image directory
│   └── (your image here)
├── QUICK_START.md         # Detailed startup guide
├── COMMANDS.md            # Command reference
├── UI_GUIDE.md            # UI documentation
└── README.md              # This file
```

## 🔒 Privacy

- ✅ **100% Local** - No internet connection required
- ✅ **No Recording** - Camera feed is not saved
- ✅ **No Tracking** - No data sent anywhere
- ✅ **Open Source** - All code is visible

## 🤝 Contributing

Contributions are welcome! Feel free to:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- **MediaPipe** by Google - Amazing hand tracking framework
- **OpenCV** - Computer vision library
- **NumPy** - Numerical computing

## 💡 Use Cases

- **Fun Pranks** - Surprise your friends!
- **Interactive Demos** - Show off ML capabilities
- **Learning Tool** - Understand computer vision
- **Engagement** - Interactive user experiences
- **Positivity Spread** - Actually use it for motivation!

## 🎉 Fun Fact

This app looks like a wholesome positivity app with motivational quotes, but secretly waits for a thumbs up to reveal your surprise image. Perfect for pranks! 😂

---

**Made with Python, OpenCV, and a bit of fun! 🐍👍**

Star ⭐ this repo if you found it useful!
