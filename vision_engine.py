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
        self.last_click_time = 0
        self.debug_mode = False
        
        # Load existing lock if any
        self.load_lock()

    def load_lock(self):
        if os.path.exists('center_lock.npy'):
            try:
                self.target_center = tuple(np.load('center_lock.npy').tolist())
                print(f"🔒 Stored Target Loaded: {self.target_center}")
            except:
                pass

    def find_button_auto(self, frame):
        """Finds the brightest circular spot (the projection)."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        # Look for VERY bright spots (projector hotspots)
        _, thresh = cv2.threshold(gray, 230, 255, cv2.THRESH_BINARY)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            c = max(contours, key=cv2.contourArea)
            M = cv2.moments(c)
            if M["m00"] > 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                return (cX, cY)
        return None

    def set_target_mouse(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.target_center = (x, y)
            self.auto_locked = False
            np.save('center_lock.npy', np.array(self.target_center))
            print(f"📍 TARGET MANUALLY SET: ({x}, {y})")

    def run(self):
        print("Vision Engine Started. Waiting for connections...")
        cv2.namedWindow('Vision Tool')
        cv2.setMouseCallback('Vision Tool', self.set_target_mouse)
        
        while True:
            ret, frame = self.cap.read()
            if not ret: break

            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            
            # --- AUTO-SEEK ---
            if self.target_center is None:
                auto_pos = self.find_button_auto(frame)
                if auto_pos:
                    self.target_center = auto_pos
                    self.auto_locked = True
                    print(f"✨ AUTO-SEEK FOUND TARGET: {auto_pos}")

            # --- HAND TRACKING ---
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Check if all 5 fingers are open
                    fingers_open = []
                    
                    # Wrist
                    wrist = hand_landmarks.landmark[0]
                    
                    # Helper for distance to wrist
                    def dist_to_wrist(lm_idx):
                        lm = hand_landmarks.landmark[lm_idx]
                        return (lm.x - wrist.x)**2 + (lm.y - wrist.y)**2

                    # Thumb: Tip (4) vs IP (3) - slightly different logic often used but dist check works ok
                    # Often for thumb, we check if it is away from the hand center, but let's stick to wrist dist
                    thumbs_up = dist_to_wrist(4) > dist_to_wrist(3) + 0.002 # small buffer
                    fingers_open.append(thumbs_up)

                    # Other 4 fingers: Tip vs PIP (6, 10, 14, 18)
                    for tip, pip in [(8, 6), (12, 10), (16, 14), (20, 18)]:
                         fingers_open.append(dist_to_wrist(tip) > dist_to_wrist(pip))

                    is_five_fingers = all(fingers_open)

                    # Use Middle Finger MCP (9) or Centroid as interaction point for "Whole Hand"
                    # Landmark 9 is stable
                    center_lm = hand_landmarks.landmark[9] 
                    cx, cy = int(center_lm.x * w), int(center_lm.y * h)
                    
                    # Visual feedback
                    color = (0, 255, 255) if is_five_fingers else (0, 0, 255)
                    cv2.circle(frame, (cx, cy), 20, color, -1)
                    
                    if is_five_fingers:
                        cv2.putText(frame, "HAND OPEN", (cx, cy-40), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

                    if self.target_center and is_five_fingers:
                        tx, ty = self.target_center
                        dist = np.sqrt((cx - tx)**2 + (cy - ty)**2)
                        
                        # Large hit zone: 150 pixels for wall interaction
                        if dist < 150: 
                            cv2.circle(frame, (tx, ty), 150, (0, 255, 0), 5)
                            cv2.putText(frame, "HIT!", (cx, cy-70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
                            
                            if time.time() - self.last_click_time > 2.0:
                                print(f"🎯 TRIGGER (Dist: {dist:.1f})")
                                sio.emit('click', {'x': 0.5, 'y': 0.5})
                                self.last_click_time = time.time()
                        else:
                            cv2.putText(frame, f"Dist: {int(dist)}", (cx+20, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                    elif not is_five_fingers:
                         cv2.putText(frame, "OPEN HAND NEEDED", (cx, cy-40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)


            # --- UI HUD ---
            if self.target_center:
                tx, ty = self.target_center
                color = (255, 200, 0) if self.auto_locked else (255, 0, 0)
                cv2.circle(frame, (tx, ty), 150, color, 3)
                cv2.putText(frame, "ACTIVE ZONE", (tx-80, ty-160), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            cv2.putText(frame, "1. PROJECT IMAGE ON WALL", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, "2. CLICK WINDOW TO LOCK SPOT", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, "3. USE OPEN HAND TO TRIGGER", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            cv2.imshow('Vision Tool', frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'): break
            elif key == ord('l'): 
                self.target_center = None
                print("🗑️ Target Reset")

        self.cap.release()
        cv2.destroyAllWindows()

@sio.event
def connect(sid, environ):
    print("🌐 Browser Connected")

if __name__ == "__main__":
    engine = VisionEngine()
    eventlet.spawn(engine.run)
    eventlet.wsgi.server(eventlet.listen(('', 5001)), app)
