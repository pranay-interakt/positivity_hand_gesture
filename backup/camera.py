#!/usr/bin/env python3
"""
Positivity Boost App
Spread positivity with a simple gesture!
"""

import cv2
import numpy as np
import os
from pathlib import Path
import random

class PositivityBoostApp:
    """An app to boost your positivity!"""
    
    def __init__(self):
        # Initialize camera
        print("📹 Starting camera...")
        self.cap = cv2.VideoCapture(0)
        
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(1)
        
        if not self.cap.isOpened():
            print("❌ Camera not available!")
            exit(1)
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        print("✓ Camera ready!")
        
        # Try to load MediaPipe
        self.hands_detector = None
        try:
            import mediapipe as mp
            self.mp_hands = mp.solutions.hands
            self.mp_draw = mp.solutions.drawing_utils
            self.hands_detector = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=2,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.7
            )
            print("✓ Gesture detection ready!")
        except Exception as e:
            print(f"⚠️  Gesture detection unavailable")
        
        # Load face detection
        self.face_cascade = None
        try:
            cascade_path = cv2.data.haarcascades
            self.face_cascade = cv2.CascadeClassifier(cascade_path + 'haarcascade_frontalface_default.xml')
            print("✓ Face detection ready!")
        except:
            pass
        
        # Load the surprise image
        self.surprise_image = None
        self.load_image()
        
        # State
        self.overlay_alpha = 0.0
        self.target_alpha = 0.0
        self.fade_speed = 0.2
        self.gesture_frames = 0
        self.required_frames = 10
        self.image_shown = False
        
        # UI dimensions (1400x900 window)
        self.window_width = 1400
        self.window_height = 900
        
        # Motivational quotes
        self.quotes = [
            "Believe in yourself! 💪",
            "You are amazing! ✨",
            "Today is your day! 🌟",
            "Keep smiling! 😊",
            "You've got this! 🎯",
            "Stay positive! 🌈",
            "Dream big! 🚀",
            "Be awesome! 🌺",
            "Shine bright! ⭐",
            "You matter! 💖"
        ]
        self.current_quote = random.choice(self.quotes)
        self.quote_timer = 0
        
    def load_image(self):
        """Load the surprise image"""
        photo_dir = Path(__file__).parent / "photo"
        
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
            images = list(photo_dir.glob(ext))
            if images:
                self.surprise_image = cv2.imread(str(images[0]))
                print(f"✓ Surprise loaded!")
                return
        
        print("⚠️  No image found")
    
    def detect_thumbs_up(self, hand_landmarks, handedness):
        """Detect thumbs up gesture"""
        if not hand_landmarks:
            return False, 0.0
        
        landmarks = hand_landmarks.landmark
        
        # Thumb landmarks
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        thumb_mcp = landmarks[2]
        
        # Other fingers
        index_tip = landmarks[8]
        index_pip = landmarks[6]
        middle_tip = landmarks[12]
        middle_pip = landmarks[10]
        ring_tip = landmarks[16]
        ring_pip = landmarks[14]
        pinky_tip = landmarks[20]
        pinky_pip = landmarks[18]
        
        # Check thumb up
        thumb_up = thumb_tip.y < thumb_ip.y < thumb_mcp.y
        
        # Check fingers curled
        index_curled = index_tip.y > index_pip.y
        middle_curled = middle_tip.y > middle_pip.y
        ring_curled = ring_tip.y > ring_pip.y
        pinky_curled = pinky_tip.y > pinky_pip.y
        
        # Calculate confidence
        confidence = 0.0
        if thumb_up: confidence += 0.4
        if index_curled: confidence += 0.15
        if middle_curled: confidence += 0.15
        if ring_curled: confidence += 0.15
        if pinky_curled: confidence += 0.15
        
        return confidence >= 0.7, confidence
    
    def create_ui_frame(self, camera_frame):
        """Create the full UI with camera preview and quotes"""
        # Create blank canvas
        ui = np.ones((self.window_height, self.window_width, 3), dtype=np.uint8) * 240
        
        # Add gradient background
        for i in range(self.window_height):
            color_val = int(240 - (i / self.window_height) * 40)
            ui[i, :] = [color_val, color_val + 10, color_val + 15]
        
        # ===== HEADER =====
        header_height = 120
        cv2.rectangle(ui, (0, 0), (self.window_width, header_height), (70, 130, 180), -1)
        
        # Title
        title = "POSITIVITY BOOST"
        font = cv2.FONT_HERSHEY_DUPLEX
        title_size = cv2.getTextSize(title, font, 2.0, 3)[0]
        title_x = (self.window_width - title_size[0]) // 2
        cv2.putText(ui, title, (title_x, 70), font, 2.0, (255, 255, 255), 3)
        
        # Subtitle
        subtitle = "Send a thumbs up to brighten your day! 👍"
        subtitle_size = cv2.getTextSize(subtitle, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
        subtitle_x = (self.window_width - subtitle_size[0]) // 2
        cv2.putText(ui, subtitle, (subtitle_x, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 200), 2)
        
        # ===== CAMERA PREVIEW (LEFT SIDE) =====
        camera_x = 50
        camera_y = 160
        camera_width = 600
        camera_height = 450
        
        # Resize camera frame
        camera_resized = cv2.resize(camera_frame, (camera_width, camera_height))
        
        # Add border
        border_color = (70, 130, 180)
        border_thickness = 5
        cv2.rectangle(ui, 
                     (camera_x - border_thickness, camera_y - border_thickness),
                     (camera_x + camera_width + border_thickness, camera_y + camera_height + border_thickness),
                     border_color, border_thickness)
        
        # Place camera frame
        ui[camera_y:camera_y+camera_height, camera_x:camera_x+camera_width] = camera_resized
        
        # Camera label
        cv2.rectangle(ui, (camera_x, camera_y - 35), (camera_x + 200, camera_y - 5), (70, 130, 180), -1)
        cv2.putText(ui, "LIVE CAMERA", (camera_x + 10, camera_y - 12), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # ===== QUOTES SECTION (RIGHT SIDE) =====
        quotes_x = 700
        quotes_y = 160
        quotes_width = 650
        quotes_height = 450
        
        # Quote box background
        cv2.rectangle(ui, (quotes_x, quotes_y), (quotes_x + quotes_width, quotes_y + quotes_height), 
                     (255, 255, 255), -1)
        cv2.rectangle(ui, (quotes_x, quotes_y), (quotes_x + quotes_width, quotes_y + quotes_height), 
                     (70, 130, 180), 5)
        
        # Quote header
        cv2.rectangle(ui, (quotes_x, quotes_y), (quotes_x + quotes_width, quotes_y + 60), 
                     (70, 130, 180), -1)
        cv2.putText(ui, "DAILY INSPIRATION", (quotes_x + 20, quotes_y + 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        
        # Main quote
        quote_y = quotes_y + 150
        quote_font = cv2.FONT_HERSHEY_SIMPLEX
        quote_scale = 1.5
        quote_size = cv2.getTextSize(self.current_quote, quote_font, quote_scale, 3)[0]
        quote_x = quotes_x + (quotes_width - quote_size[0]) // 2
        cv2.putText(ui, self.current_quote, (quote_x, quote_y), 
                   quote_font, quote_scale, (70, 130, 180), 3)
        
        # Motivational messages
        messages = [
            "✨ You are capable of amazing things",
            "💪 Your potential is limitless",
            "🌟 Every day is a new opportunity",
            "🎯 Success starts with believing"
        ]
        
        msg_y = quotes_y + 250
        for msg in messages:
            cv2.putText(ui, msg, (quotes_x + 40, msg_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 100, 100), 1)
            msg_y += 40
        
        # ===== INSTRUCTIONS (BOTTOM) =====
        instructions_y = 650
        cv2.rectangle(ui, (50, instructions_y), (self.window_width - 50, instructions_y + 200), 
                     (255, 255, 255), -1)
        cv2.rectangle(ui, (50, instructions_y), (self.window_width - 50, instructions_y + 200), 
                     (70, 130, 180), 5)
        
        # Instructions header
        cv2.rectangle(ui, (50, instructions_y), (self.window_width - 50, instructions_y + 50), 
                     (70, 130, 180), -1)
        cv2.putText(ui, "HOW IT WORKS", (70, instructions_y + 35), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        
        # Steps
        steps = [
            "1. Position yourself in front of the camera",
            "2. Give a thumbs up gesture 👍",
            "3. Hold for 1 second",
            "4. Enjoy your surprise! ✨"
        ]
        
        step_y = instructions_y + 85
        for step in steps:
            cv2.putText(ui, step, (100, step_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (60, 60, 60), 2)
            step_y += 35
        
        # Controls
        cv2.putText(ui, "Press ESC to close surprise | Press Q to quit", 
                   (self.window_width - 500, self.window_height - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 1)
        
        return ui
    
    def draw_face_detection(self, frame):
        """Draw face detection overlay"""
        if self.face_cascade is None:
            return frame
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        
        for (x, y, w, h) in faces:
            # Draw box
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            # Draw corners
            corner_len = 15
            cv2.line(frame, (x, y), (x + corner_len, y), (0, 255, 0), 3)
            cv2.line(frame, (x, y), (x, y + corner_len), (0, 255, 0), 3)
            cv2.line(frame, (x + w, y), (x + w - corner_len, y), (0, 255, 0), 3)
            cv2.line(frame, (x + w, y), (x + w, y + corner_len), (0, 255, 0), 3)
            
        return frame
    
    def process_frame(self, camera_frame):
        """Process camera frame and create UI"""
        # Flip for mirror
        camera_frame = cv2.flip(camera_frame, 1)
        
        # Detect thumbs up
        thumbs_up_detected = False
        
        if self.hands_detector:
            rgb_frame = cv2.cvtColor(camera_frame, cv2.COLOR_BGR2RGB)
            results = self.hands_detector.process(rgb_frame)
            
            if results.multi_hand_landmarks and results.multi_handedness:
                for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                    is_thumbs, conf = self.detect_thumbs_up(hand_landmarks, handedness)
                    if is_thumbs:
                        thumbs_up_detected = True
                        # Draw hand landmarks on camera frame
                        self.mp_draw.draw_landmarks(camera_frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                        break
        
        # Draw face detection
        camera_frame = self.draw_face_detection(camera_frame)
        
        # Update gesture state
        if thumbs_up_detected:
            self.gesture_frames += 1
            if self.gesture_frames >= self.required_frames:
                self.target_alpha = 1.0
                self.image_shown = True
        else:
            self.gesture_frames = 0
        
        # Smooth fade
        if self.overlay_alpha < self.target_alpha:
            self.overlay_alpha = min(self.overlay_alpha + self.fade_speed, self.target_alpha)
        elif self.overlay_alpha > self.target_alpha:
            self.overlay_alpha = max(self.overlay_alpha - self.fade_speed, self.target_alpha)
        
        # Create UI
        ui_frame = self.create_ui_frame(camera_frame)
        
        # If image should be shown, overlay it on full screen
        if self.overlay_alpha > 0.01 and self.surprise_image is not None:
            # Resize surprise image to fit window
            h, w = self.surprise_image.shape[:2]
            aspect = w / h
            
            new_w = self.window_width
            new_h = int(new_w / aspect)
            
            if new_h > self.window_height:
                new_h = self.window_height
                new_w = int(new_h * aspect)
            
            surprise_resized = cv2.resize(self.surprise_image, (new_w, new_h))
            
            # Center it
            y_offset = (self.window_height - new_h) // 2
            x_offset = (self.window_width - new_w) // 2
            
            # Blend
            overlay = ui_frame.copy()
            overlay[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = surprise_resized
            ui_frame = cv2.addWeighted(ui_frame, 1 - self.overlay_alpha, overlay, self.overlay_alpha, 0)
        
        # Update quote periodically
        self.quote_timer += 1
        if self.quote_timer > 300:  # Change every 10 seconds
            self.current_quote = random.choice(self.quotes)
            self.quote_timer = 0
        
        return ui_frame
    
    def run(self):
        """Main loop"""
        print("\n" + "="*60)
        print("✨ Positivity Boost App")
        print("="*60)
        print("\n👍 Show a thumbs up to get your surprise!")
        print("Press ESC to close surprise | Press Q to quit\n")
        
        while True:
            ret, frame = self.cap.read()
            
            if not ret:
                break
            
            # Process and create UI
            ui_frame = self.process_frame(frame)
            
            # Display
            cv2.imshow('Positivity Boost', ui_frame)
            
            # Keyboard input
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q') or key == ord('Q'):
                break
            elif key == 27:  # ESC key
                # Hide image
                self.target_alpha = 0.0
                self.image_shown = False
            elif key == ord('t') or key == ord('T'):
                # Manual trigger (for testing)
                self.target_alpha = 1.0
                self.image_shown = True
        
        # Cleanup
        self.cap.release()
        cv2.destroyAllWindows()
        if self.hands_detector:
            self.hands_detector.close()
        print("\n👋 Thanks for spreading positivity!\n")

def main():
    """Entry point"""
    try:
        app = PositivityBoostApp()
        app.run()
    except KeyboardInterrupt:
        print("\n\n👋 Bye!\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
