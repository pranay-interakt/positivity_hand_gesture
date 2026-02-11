import cv2
import mediapipe as mp
import numpy as np
import socketio
import eventlet
import eventlet.wsgi
from flask import Flask
import time
import json
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
        
        # Calibration state
        self.calibration_points = [] # Points in camera coordinates
        self.homography = None
        self.is_calibrating = False
        self.calibration_step = 0
        self.target_points = np.float32([
            [0, 0],       # Top Left
            [1920, 0],    # Top Right
            [1920, 1080], # Bottom Right
            [0, 1080]     # Bottom Left
        ])
        
        # Smoothing
        self.prev_x, self.prev_y = 0, 0
        self.smoothing = 0.7
        
        # Dwell detection
        self.dwell_timer = 0
        self.dwell_pos = None
        self.dwell_threshold = 0.4 # seconds
        self.dwell_radius = 0.03 # normalized distance
        self.last_click_time = 0
        
        # Load calibration if exists
        self.load_calibration()

    def save_calibration(self):
        if self.homography is not None:
            np.save('calibration.npy', self.homography)
            print("Calibration saved.")

    def load_calibration(self):
        if os.path.exists('calibration.npy'):
            self.homography = np.load('calibration.npy')
            print("Calibration loaded.")

    def run(self):
        print("Vision Engine Started. Waiting for connections...")
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            # Flip for mirror effect and easier interaction
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            
            # Convert to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)

            finger_pos = None

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Index finger tip is index 8
                    index_tip = hand_landmarks.landmark[8]
                    thumb_tip = hand_landmarks.landmark[4]
                    
                    cx, cy = int(index_tip.x * w), int(index_tip.y * h)
                    finger_pos = (cx, cy)
                    
                    # Calculate distance for tap detection (pinch)
                    dist = np.sqrt((index_tip.x - thumb_tip.x)**2 + (index_tip.y - thumb_tip.y)**2)
                    
                    # Draw landmarks on camera view
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    
                    color = (0, 255, 0) # Green for hover
                    click_triggered = False
                    current_time = time.time()
                    norm_x, norm_y = cx/w, cy/h

                    # --- PINCH CHECK ---
                    if dist < 0.08: # Threshold for pinching
                        color = (0, 0, 255) # Red for pinch click
                        if not hasattr(self, 'pinch_active') or not self.pinch_active:
                            if current_time - self.last_click_time > 0.5: # Debounce
                                print(f"✨ PINCH CLICK (dist: {dist:.4f})")
                                click_triggered = True
                                self.pinch_active = True
                    else:
                        self.pinch_active = False

                    # --- DWELL CHECK ---
                    if self.dwell_pos is None:
                        self.dwell_pos = (norm_x, norm_y)
                        self.dwell_timer = current_time
                    else:
                        d_dist = np.sqrt((norm_x - self.dwell_pos[0])**2 + (norm_y - self.dwell_pos[1])**2)
                        
                        if d_dist > self.dwell_radius:
                            # Moved outside radius, reset
                            self.dwell_pos = (norm_x, norm_y)
                            self.dwell_timer = current_time
                        elif current_time - self.dwell_timer > self.dwell_threshold:
                            # Dwell triggered!
                            if current_time - self.last_click_time > 1.0: # Longer debounce for dwell
                                print(f"✨ DWELL CLICK (held for {self.dwell_threshold}s)")
                                click_triggered = True
                                color = (255, 0, 255) # Magenta for dwell click
                                cv2.circle(frame, (cx, cy), 40, color, 2)
                                self.dwell_timer = current_time # Reset timer to allow re-trigger after move
                    
                    # --- EMIT CLICK ---
                    if click_triggered:
                        self.last_click_time = current_time
                        # Map to projected coordinates if calibrated
                        emit_x, emit_y = cx/w, cy/h
                        if self.homography is not None:
                            p = np.float32([[[cx, cy]]])
                            trans = cv2.perspectiveTransform(p, self.homography)
                            emit_x, emit_y = trans[0][0][0]/1920.0, trans[0][0][1]/1080.0
                        
                        sio.emit('click', {'x': emit_x, 'y': emit_y})

                    cv2.circle(frame, (cx, cy), 15, color, -1)

            # Handle Calibration
            if self.is_calibrating and finger_pos:
                # In a real setup, we'd wait for a "click" or a "hold"
                # For now, let's just listen for a keyboard trigger to lock the point
                pass

            # Map coordinates and Broadcast
            if finger_pos:
                if self.homography is not None:
                    point = np.float32([[[finger_pos[0], finger_pos[1]]]])
                    transformed = cv2.perspectiveTransform(point, self.homography)
                    tx, ty = transformed[0][0]
                    tx = tx / 1920.0
                    ty = ty / 1080.0
                else:
                    # Raw normalized coordinates for testing without projector
                    tx, ty = finger_pos[0] / w, finger_pos[1] / h
                
                # Apply smoothing
                smooth_x = self.prev_x * self.smoothing + tx * (1 - self.smoothing)
                smooth_y = self.prev_y * self.smoothing + ty * (1 - self.smoothing)
                
                self.prev_x, self.prev_y = smooth_x, smooth_y
                sio.emit('touch', {'x': smooth_x, 'y': smooth_y})

            # Show camera feed (only for debugging/setup)
            cv2.putText(frame, "Calibration Step: " + str(self.calibration_step) if self.is_calibrating else "Running", 
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
            cv2.imshow('Vision Engine', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('c'):
                print("Starting Calibration...")
                self.is_calibrating = True
                self.calibration_points = []
                self.calibration_step = 0
                sio.emit('calibration_start')
            elif key == ord(' ') and self.is_calibrating and finger_pos:
                # Capture current finger pos as calibration point
                self.calibration_points.append(finger_pos)
                print(f"Captured point {self.calibration_step + 1}: {finger_pos}")
                self.calibration_step += 1
                sio.emit('calibration_next', {'step': self.calibration_step})
                
                if self.calibration_step == 4:
                    # Calculate homography
                    src_pts = np.float32(self.calibration_points)
                    self.homography, _ = cv2.findHomography(src_pts, self.target_points)
                    self.save_calibration()
                    self.is_calibrating = False
                    print("Calibration Complete!")
                    sio.emit('calibration_end')

        self.cap.release()
        cv2.destroyAllWindows()

@sio.event
def connect(sid, environ):
    print("Client connected:", sid)

if __name__ == "__main__":
    engine = VisionEngine()
    # Start the Socket.IO server in a separate thread
    eventlet.spawn(engine.run)
    eventlet.wsgi.server(eventlet.listen(('', 5001)), app)
