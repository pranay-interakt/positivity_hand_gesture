
import cv2
import numpy as np
import mediapipe as mp
import math
import sys
import time
import pyautogui

# Ensure MediaPipe is available
try:
    if not hasattr(mp, 'solutions'):
        import mediapipe.python.solutions as solutions
        mp.solutions = solutions
except ImportError:
    pass


class InteractiveProjection:
    def __init__(self):
        self.points_camera = []
        self.points_projector = []
        self.homography_matrix = None
        self.calibration_done = False
        
        # Video Configuration
        self.video_path = "DIA Event June 2023.mp4"
        self.video_cap = None
        self.video_state = "STOPPED" # STOPPED, PLAYING, PAUSED
        
        # Gesture State
        self.gesture_state = "OPEN" # OPEN, FIST
        self.last_gesture_time = 0
        self.click_history = [] # List of timestamps of recent clicks
        self.ripple_animations = [] # List of [x, y, radius, alpha]

        # Initialize MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
            model_complexity=1
        )
        self.mp_draw = mp.solutions.drawing_utils

        # Initialize Projector Screen (Simple default for now)
        self.screen_width = 1280
        self.screen_height = 720

        # Define 4 calibration points (inset)
        margin_x = int(self.screen_width * 0.1)
        margin_y = int(self.screen_height * 0.1)
        self.points_projector = np.array([
            [margin_x, margin_y],                            # Top-Left
            [self.screen_width - margin_x, margin_y],        # Top-Right
            [self.screen_width - margin_x, self.screen_height - margin_y], # Bottom-Right
            [margin_x, self.screen_height - margin_y]        # Bottom-Left
        ], dtype=np.float32)

        # Initialize Camera
        self.cap = cv2.VideoCapture(0)
        start_time = time.time()
        while not self.cap.isOpened():
             print("Trying to open camera...")
             if time.time() - start_time > 5:
                  print("Error: Could not open webcam.")
                  sys.exit(1)
             time.sleep(1)
             self.cap = cv2.VideoCapture(0)
             if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(1)

        # Create windows
        # 1. Projector Window - Normal window at default location
        cv2.namedWindow("Projector", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Projector", self.screen_width, self.screen_height)
        
        # 2. Camera Feed
        cv2.namedWindow("Camera Feed (CLICK HERE)", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Camera Feed (CLICK HERE)", 640, 480)
        cv2.moveWindow("Camera Feed (CLICK HERE)", 50, 50)
        cv2.setMouseCallback("Camera Feed (CLICK HERE)", self.mouse_callback)

    def mouse_callback(self, event, x, y, flags, param):
        if not self.calibration_done and event == cv2.EVENT_LBUTTONDOWN:
            if len(self.points_camera) < 4:
                self.points_camera.append([x, y])
                print(f"User Clicked Point {len(self.points_camera)} at ({x}, {y})")

    def calibrate(self):
        # Dark Gray background so we know it's not "dead" black
        projector_bg = np.zeros((self.screen_height, self.screen_width, 3), dtype=np.uint8)
        projector_bg[:] = (30, 30, 30) 
        
        print("\n--- MANUAL WINDOW MANAGEMENT ---")
        print("1. Drag the 'Projector' window to your wall screen (Monitor 2).")
        print("2. MAXIMIZE it manually (click the green fullscreen button on window title bar).")
        print("3. Ensure 'Camera Feed' window is visible on your laptop.")
        print("4. Proceed with clicking Red Dots.")
        
        while len(self.points_camera) < 4:
            proj_display = projector_bg.copy()
            current_idx = len(self.points_camera)
            
            try:
                _, _, w_cur, h_cur = cv2.getWindowImageRect("Projector")
                if w_cur > 0 and (w_cur != self.screen_width or h_cur != self.screen_height):
                    self.screen_width, self.screen_height = w_cur, h_cur
                    margin_x = int(self.screen_width * 0.1)
                    margin_y = int(self.screen_height * 0.1)
                    self.points_projector = np.array([
                        [margin_x, margin_y],
                        [self.screen_width - margin_x, margin_y],
                        [self.screen_width - margin_x, self.screen_height - margin_y],
                        [margin_x, self.screen_height - margin_y]
                    ], dtype=np.float32)
            except:
                pass

            for i in range(current_idx):
                pt = self.points_projector[i]
                cv2.circle(proj_display, (int(pt[0]), int(pt[1])), 20, (0, 255, 0), -1)

            pt = self.points_projector[current_idx]
            cv2.circle(proj_display, (int(pt[0]), int(pt[1])), 60, (0, 0, 255), -1)
            cv2.circle(proj_display, (int(pt[0]), int(pt[1])), 80, (0, 0, 255), 3)  
            
            text = f"CLICK Point {current_idx+1}"
            (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 2, 3)
            tx = max(50, int(pt[0]) - tw // 2)
            ty = max(100, int(pt[1]) - 100)
            cv2.putText(proj_display, text, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)

            cv2.imshow("Projector", proj_display)
            
            ret, frame = self.cap.read()
            if not ret: continue

            for i, p in enumerate(self.points_camera):
                cv2.circle(frame, (int(p[0]), int(p[1])), 5, (0, 255, 0), -1)
                cv2.putText(frame, str(i+1), (int(p[0])+10, int(p[1])), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            cv2.putText(frame, f"Click RED dot {current_idx+1}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            cv2.imshow("Camera Feed (CLICK HERE)", frame)
            
            k = cv2.waitKey(10)
            if k == 27: sys.exit(0)
        
        if len(self.points_camera) == 4:
            pts_src = np.array(self.points_camera, dtype=np.float32)
            pts_dst = self.points_projector
            self.homography_matrix, _ = cv2.findHomography(pts_src, pts_dst)
            self.calibration_done = True
            print("Calibration Complete!")

    def is_fist(self, hand_landmarks):
        # Tip is BELOW PIP (y > pip.y in screen coords) means curled
        # Note: MediaPipe Y increases downwards.
        tips = [8, 12, 16, 20]
        pips = [6, 10, 14, 18]
        curled_count = 0
        for i in range(4):
            if hand_landmarks.landmark[tips[i]].y > hand_landmarks.landmark[pips[i]].y:
                curled_count += 1
        return curled_count >= 3 # Allow loose index sometimes

    def is_open(self, hand_landmarks):
        tips = [8, 12, 16, 20]
        pips = [6, 10, 14, 18]
        extended_count = 0
        for i in range(4):
            if hand_landmarks.landmark[tips[i]].y < hand_landmarks.landmark[pips[i]].y:
                extended_count += 1
        return extended_count >= 3

    def handle_video(self, proj_display):
        if self.video_state == "PLAYING":
            ret, frame = self.video_cap.read()
            if not ret:
                # Loop video
                self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.video_cap.read()
            
            if ret:
                frame = cv2.resize(frame, (self.screen_width, self.screen_height))
                np.copyto(proj_display, frame)
        
        elif self.video_state == "PAUSED":
            # Just keep last frame? Or show "PAUSED" text overlay
            # For simplicity, if paused, we might just not update the frame or show a static capture.
            # But since we are redrawing 'proj_display' every loop, likely black/gray. 
            pass # Currently will show Gray background if paused logic isn't retaining frame.
                 # Let's handle 'PAUSED' by not reading new frame but we need last frame.
                 # Actually, simpler: If playing/paused, the video loop handles rendering.

    def toggle_video_play(self):
        if self.video_state == "STOPPED":
            print("Starting Video...")
            self.video_cap = cv2.VideoCapture(self.video_path)
            self.video_state = "PLAYING"
        elif self.video_state == "PLAYING":
            print("Pausing Video...")
            self.video_state = "PAUSED"
        elif self.video_state == "PAUSED":
            print("Resuming Video...")
            self.video_state = "PLAYING"

    def stop_video(self):
        if self.video_state != "STOPPED":
            print("Stopping Video...")
            self.video_state = "STOPPED"
            if self.video_cap:
                self.video_cap.release()
                self.video_cap = None

    def trigger_click(self, x, y):
        current_time = time.time()
        self.click_history.append(current_time)
        self.click_history = [t for t in self.click_history if current_time - t < 1.0] # Keep last 1s
        
        # Add visual ripple
        self.ripple_animations.append({'x': x, 'y': y, 'r': 10, 'alpha': 255})

        # Check for Double Click
        if len(self.click_history) >= 2:
            print("DOUBLE CLICK DETECTED!")
            # Consume clicks
            self.click_history = []
            
            # Logic: 
            # If playing -> Stop
            # If stopped -> Play
            if self.video_state in ["PLAYING", "PAUSED"]:
                self.stop_video()
            else:
                self.toggle_video_play() # Start
        else:
            print("SINGLE CLICK")
            # Logic:
            # If playing -> Toggle Pause
            if self.video_state in ["PLAYING", "PAUSED"]:
                self.toggle_video_play()
            else:
                # Normal system Click
                pyautogui.click()

    def run(self):
        print("\n--- AI MOUSE ACTIVE ---")
        print("GESTURES:")
        print("1. OPEN HAND: Move Mouse.")
        print("2. FIST -> OPEN: Back Hand facing camera, Close Fist then Open quickly = CLICK.")
        print("3. DOUBLE CLICK: Starts/Stops Video.")
        print("4. SINGLE CLICK (During Video): Pauses/Resumes.")
        
        smooth_x, smooth_y = 0, 0
        alpha = 0.4
        
        scroll_start_y = None
        
        while True:
            ret, frame = self.cap.read()
            if not ret: break
            
            try:
                _, _, w_cur, h_cur = cv2.getWindowImageRect("Projector")
                if w_cur > 0 and (w_cur != self.screen_width or h_cur != self.screen_height):
                     self.screen_width, self.screen_height = w_cur, h_cur
            except: pass

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(frame_rgb)
            
            # Base Display
            proj_display = np.zeros((self.screen_height, self.screen_width, 3), dtype=np.uint8)
            proj_display[:] = (20, 20, 20)
            
            # 1. Handle Video rendering (Background layer)
            if self.video_state == "PLAYING":
                ret_v, frame_v = self.video_cap.read()
                if not ret_v:
                    self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # Loop
                    ret_v, frame_v = self.video_cap.read()
                
                if ret_v:
                    frame_v = cv2.resize(frame_v, (self.screen_width, self.screen_height))
                    proj_display = frame_v # Overwrite background
            
            elif self.video_state == "PAUSED":
                 cv2.putText(proj_display, "PAUSED", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 5)

            # 2. Hand Tracking & UI Layer
            current_hand_state = "UNKNOWN"
            screen_point = None
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                    
                    if self.is_fist(hand_landmarks):
                        current_hand_state = "FIST"
                    elif self.is_open(hand_landmarks):
                        current_hand_state = "OPEN"
                    
                    # Track Index Tip (Open) or Wrist (Fist)
                    track_pt = hand_landmarks.landmark[8] if current_hand_state == "OPEN" else hand_landmarks.landmark[0]
                    
                    h, w, c = frame.shape
                    cx, cy = int(track_pt.x * w), int(track_pt.y * h)
                    
                    if self.homography_matrix is not None:
                        pt_cam = np.array([[[cx, cy]]], dtype=np.float32)
                        pt_proj = cv2.perspectiveTransform(pt_cam, self.homography_matrix)
                        
                        px, py = pt_proj[0][0][0], pt_proj[0][0][1]
                        px = max(0, min(px, self.screen_width))
                        py = max(0, min(py, self.screen_height))
                        
                        if smooth_x == 0: smooth_x, smooth_y = px, py
                        else:
                            smooth_x = alpha * px + (1 - alpha) * smooth_x
                            smooth_y = alpha * py + (1 - alpha) * smooth_y
                        
                        screen_point = (int(smooth_x), int(smooth_y))

            # 3. State Machine Logic
            if screen_point:
                # Detect CLICK: Transition FIST -> OPEN
                if self.gesture_state == "FIST" and current_hand_state == "OPEN":
                    # Debounce
                    if time.time() - self.last_gesture_time > 0.2:
                        self.trigger_click(screen_point[0], screen_point[1])
                        self.last_gesture_time = time.time()

                # SCROLL Mode: Hold FIST
                elif current_hand_state == "FIST":
                    if scroll_start_y is None:
                        scroll_start_y = screen_point[1]
                    else:
                        diff = screen_point[1] - scroll_start_y
                        if abs(diff) > 30: # Higher threshold to avoid jitters
                            scroll_amount = int(diff / 5)
                            pyautogui.scroll(-scroll_amount)
                            scroll_start_y = screen_point[1]
                    
                    # Scroll UI
                    cv2.circle(proj_display, screen_point, 40, (255, 100, 0), 2)
                    cv2.putText(proj_display, "SCROLL", (screen_point[0]-40, screen_point[1]-50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 100, 0), 2)

                # MOVE Mode: OPEN Hand
                elif current_hand_state == "OPEN":
                    if self.video_state == "STOPPED": # Only move system mouse when video not playing purely? Or always?
                        try: pyautogui.moveTo(screen_point[0], screen_point[1], _pause=False)
                        except: pass
                    
                    # Cursor UI
                    cv2.circle(proj_display, screen_point, 15, (255, 255, 255), -1)
                    scroll_start_y = None

            # 4. Render Animations (Ripples)
            new_ripples = []
            for r in self.ripple_animations:
                cv2.circle(proj_display, (r['x'], r['y']), r['r'], (255, 255, 255), 4) # White ring
                r['r'] += 5 # Expand
                r['alpha'] -= 10 # Fade (not used in OpenCV directly without overlay but circle width effectively thins visually if we want)
                if r['r'] < 100:
                    new_ripples.append(r)
            self.ripple_animations = new_ripples

            if current_hand_state != "UNKNOWN":
                self.gesture_state = current_hand_state

            cv2.imshow("Projector", proj_display)
            cv2.imshow("Camera Feed (CLICK HERE)", frame)
            
            k = cv2.waitKey(1)
            if k == 27: break
        
        self.cleanup()

    def cleanup(self):
        if self.cap.isOpened(): self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    app = InteractiveProjection()
    app.calibrate()
    app.run()
