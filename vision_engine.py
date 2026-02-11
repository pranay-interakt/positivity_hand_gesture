import cv2
import mediapipe as mp
import numpy as np
import socketio
import eventlet
import eventlet.wsgi
from flask import Flask
import time
import os

# Initialize Socket.IO server
sio = socketio.Server(cors_allowed_origins='*')
app = Flask(__name__)
app.wsgi_app = socketio.WSGIApp(sio, app.wsgi_app)

# Mediapipe constants
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

class VisionEngine:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        
        self.target_center = None
        self.auto_locked = False
        self.last_scan_time = 0
        self.last_click_time = 0
        
        # Cyan color range for button detection
        self.lower_cyan = np.array([85, 100, 100])
        self.upper_cyan = np.array([105, 255, 255])

        # Load existing lock if any
        self.load_lock()

    def load_lock(self):
        if os.path.exists('center_lock.npy'):
            try:
                self.target_center = tuple(np.load('center_lock.npy').tolist())
                print(f"🔒 Target Lock Loaded: {self.target_center}")
            except:
                pass

    def find_button(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower_cyan, self.upper_cyan)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)
        
        contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            c = max(contours, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            if 20 < radius < 300:
                return (int(x), int(y)), int(radius)
        return None, None

    def run(self):
        print("Vision Engine Started. Waiting for connections...")
        while True:
            ret, frame = self.cap.read()
            if not ret: break

            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)

            # --- AUTO-SCAN ---
            if self.target_center is None or (time.time() - self.last_scan_time > 3.0):
                self.last_scan_time = time.time()
                center, radius = self.find_button(frame)
                if center:
                    self.target_center = center
                    self.auto_locked = True
                    print(f"✅ AUTO-DETECTED BUTTON AT {center}")

            # --- HAND TRACKING ---
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    index_tip = hand_landmarks.landmark[8]
                    cx, cy = int(index_tip.x * w), int(index_tip.y * h)
                    
                    # Draw visual markers
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    cv2.circle(frame, (cx, cy), 10, (0, 255, 255), -1)

                    # --- PROXIMITY TRIGGER ---
                    if self.target_center:
                        tx, ty = self.target_center
                        dist = np.sqrt((cx - tx)**2 + (cy - ty)**2)
                        
                        if dist < 90: # In range
                            cv2.circle(frame, (int(tx), int(ty)), 90, (0, 255, 0), 5)
                            cv2.putText(frame, "TRIGGER!", (cx, cy-30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
                            
                            if time.time() - self.last_click_time > 2.0:
                                print(f"🎯 BUTTON HIT! Dist: {dist:.1f}")
                                sio.emit('click', {'x': 0.5, 'y': 0.5})
                                self.last_click_time = time.time()
                        else:
                            cv2.putText(frame, f"Dist: {int(dist)}", (cx+20, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            # --- UI FEEDBACK ---
            if self.target_center:
                tx, ty = self.target_center
                color = (255, 255, 0) if self.auto_locked else (255, 0, 0)
                cv2.circle(frame, (int(tx), int(ty)), 90, color, 2)
                cv2.putText(frame, "TARGET", (int(tx)-40, int(ty)-100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            cv2.putText(frame, "Auto-Scanning... Press 'L' to Manual Lock", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow('Vision Engine', frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'): break
            elif key == ord('l'): # Manual Lock override
                # Find current index finger if possible
                if results.multi_hand_landmarks:
                    hand_landmarks = results.multi_hand_landmarks[0]
                    index_tip = hand_landmarks.landmark[8]
                    self.target_center = (int(index_tip.x * w), int(index_tip.y * h))
                    self.auto_locked = False
                    np.save('center_lock.npy', np.array(self.target_center))
                    print(f"🔒 MANUALLY LOCKED AT {self.target_center}")

        self.cap.release()
        cv2.destroyAllWindows()

@sio.event
def connect(sid, environ):
    print("Client connected:", sid)

if __name__ == "__main__":
    engine = VisionEngine()
    eventlet.spawn(engine.run)
    eventlet.wsgi.server(eventlet.listen(('', 5001)), app)
