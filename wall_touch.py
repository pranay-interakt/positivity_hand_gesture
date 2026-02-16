
import cv2
import numpy as np
import mediapipe as mp
import time
import pyautogui
import math
import sys

# Constants
CLICK_THRESHOLD = 0.3 # Faster click
MOVE_THRESHOLD = 10   
CALIBRATION_FILE = "calibration.npy"


class WallTouch:
    def __init__(self):
        self.points_camera = []
        self.points_projector = []
        self.homography_matrix = None
        self.calibration_done = False
        
        # Interaction Logic
        self.click_cooldown = 0
        self.press_start_time = None
        self.press_pos = None
        self.current_tracker_id = None 
        
        self.app_state = "BLANK" 
        self.video_path = "DIA Event June 2023.mp4"
        self.video_cap = None
        self.ripple_animations = []

        # Initialize MediaPipe Hands: Very Low Confidence for Range (0.5), High Model (1)
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5, 
            min_tracking_confidence=0.5,
            model_complexity=1
        )
        self.mp_draw = mp.solutions.drawing_utils

        # Initialize Projector Screen
        self.screen_width = 1280
        self.screen_height = 720

        # Define 4 calibration points (inset)
        margin_x = int(self.screen_width * 0.1)
        margin_y = int(self.screen_height * 0.1)
        self.points_projector = np.array([
            [margin_x, margin_y],                            
            [self.screen_width - margin_x, margin_y],        
            [self.screen_width - margin_x, self.screen_height - margin_y], 
            [margin_x, self.screen_height - margin_y]        
        ], dtype=np.float32)

        # Initialize Camera
        self.cap = cv2.VideoCapture(0)
        start_time = time.time()
        while not self.cap.isOpened():
             if time.time() - start_time > 5:
                  sys.exit(1)
             time.sleep(1)
             self.cap = cv2.VideoCapture(0)
             if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(1)

        # Create Windows
        cv2.namedWindow("Projector", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Projector", self.screen_width, self.screen_height)
        
        cv2.namedWindow("Camera Feed (CLICK HERE)", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Camera Feed (CLICK HERE)", 640, 480)
        cv2.moveWindow("Camera Feed (CLICK HERE)", 50, 50)
        cv2.setMouseCallback("Camera Feed (CLICK HERE)", self.mouse_callback)


    def is_pointing(self, hand_landmarks, img_w, img_h):
        # Improved Pointing Detection: Relative Distance Check
        # Index Finger: Tip should be FURTHER from wrist than PIP (Knuckle)
        # Other Fingers: Tip should be CLOSER/NEAR (curled) relative to their PIP
        
        wrist = hand_landmarks.landmark[0]
        wx, wy = wrist.x * img_w, wrist.y * img_h
        
        def get_dist(lm_idx):
             lm = hand_landmarks.landmark[lm_idx]
             return math.hypot(lm.x * img_w - wx, lm.y * img_h - wy)

        # Index Finger (8=Tip, 6=PIP)
        # Lenient: Just needs to be extended somewhat
        index_extended = get_dist(8) > get_dist(6) * 1.2 
        
        # Middle (12=Tip, 10=PIP)
        # Lenient: Just needs to not be fully extended
        middle_curled = get_dist(12) < get_dist(10) * 1.3
        
        # Ring (16=Tip, 14=PIP)
        ring_curled = get_dist(16) < get_dist(14) * 1.3
        
        # Pinky (20=Tip, 18=PIP)
        pinky_curled = get_dist(20) < get_dist(18) * 1.3
        
        # Thumb is ignored (can be open or closed) to allow casual pointing
        
        return index_extended and (middle_curled and ring_curled and pinky_curled)

    def toggle_video(self):
        if self.app_state == "BLANK":
            print("Action: START VIDEO")
            self.video_cap = cv2.VideoCapture(self.video_path)
            self.app_state = "PLAYING"
        else:
            print("Action: STOP VIDEO")
            if self.video_cap:
                self.video_cap.release()
                self.video_cap = None
            self.app_state = "BLANK"

    def check_hover_press(self, screen_point, is_pointing_active):
        if self.click_cooldown > 0:
            self.click_cooldown -= 1
            return False

        if screen_point is None or not is_pointing_active:
            self.press_start_time = None
            return False
            
        current_time = time.time()
        if self.press_pos is None:
            self.press_pos = screen_point
            self.press_start_time = current_time
            return False

        dist = math.hypot(screen_point[0] - self.press_pos[0], screen_point[1] - self.press_pos[1])
        if dist < MOVE_THRESHOLD: # Holding Still
            if self.press_start_time is None:
                 self.press_start_time = current_time
                 return 0.0
            duration = current_time - self.press_start_time
            return min(1.0, duration / CLICK_THRESHOLD)
        else:
            self.press_pos = screen_point
            self.press_start_time = current_time
            return False

    def mouse_callback(self, event, x, y, flags, param):
        if not self.calibration_done and event == cv2.EVENT_LBUTTONDOWN:
            if len(self.points_camera) < 4:
                self.points_camera.append([x, y])
                print(f"User Clicked Point {len(self.points_camera)} at ({x}, {y})")

    def calibrate(self):
        projector_bg = np.zeros((self.screen_height, self.screen_width, 3), dtype=np.uint8)
        projector_bg[:] = (30, 30, 30) 
        
        print("\n--- MANUAL CALIBRATION ---")
        print("1. Find Red Dots on Projector.")
        print("2. Click them on Laptop Screen.")
        
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
            except: pass

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

    def run(self):
        print("\n--- WALL TOUCH SIMULATION ---")
        print("1. Calibration first.")
        print("2. RAISE Hand and POINT to control.")
        print("3. HOLD STILL (0.6s) to Click.")
        
        smooth_x, smooth_y = 0, 0
        alpha = 0.3 # Slightly faster smoothing
        
        while True:
            ret, frame = self.cap.read()
            if not ret: break
            
            h_cam, w_cam, _ = frame.shape
            
            # Handle Window Resize
            try:
                _, _, w_cur, h_cur = cv2.getWindowImageRect("Projector")
                if w_cur > 0 and (w_cur != self.screen_width or h_cur != self.screen_height):
                     self.screen_width, self.screen_height = w_cur, h_cur
            except: pass

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(frame_rgb)
            
            # 1. Background Rendering
            proj_display = np.zeros((self.screen_height, self.screen_width, 3), dtype=np.uint8)
            
            if self.app_state == "PLAYING" and self.video_cap:
                ret_v, frame_v = self.video_cap.read()
                if not ret_v:
                    self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret_v, frame_v = self.video_cap.read()
                
                if ret_v:
                    # Maintain Aspect Ratio Fit
                    vh, vw = frame_v.shape[:2]
                    target_w_box = int(self.screen_width * 0.8)
                    target_h_box = int(self.screen_height * 0.8)
                    
                    scale = min(target_w_box / vw, target_h_box / vh)
                    new_w = int(vw * scale)
                    new_h = int(vh * scale)
                    
                    frame_v = cv2.resize(frame_v, (new_w, new_h))
                    
                    x_offset = (self.screen_width - new_w) // 2
                    y_offset = (self.screen_height - new_h) // 2
                    
                    proj_display[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = frame_v
            else:
                proj_display[:] = (20, 20, 20)

            # 2. Hand Tracking Logic
            screen_point = None
            active_hand_idx = -1
            is_strict_pointing = False
            
            if results.multi_hand_landmarks:
                # Find best hand: Start with None
                best_hand_idx = -1
                highest_y = 1.0 # In MediaPipe, 0 is top. MIN y is highest.

                for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                    self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                    
                    # Check gesture with robust method
                    if self.is_pointing(hand_landmarks, w_cam, h_cam):
                         wrist_y = hand_landmarks.landmark[0].y
                         if wrist_y < highest_y:
                             highest_y = wrist_y
                             best_hand_idx = idx
                             
                if best_hand_idx != -1:
                    active_hand_idx = best_hand_idx
                    is_strict_pointing = True
                
                # If pointing not found, just tracking cursor but NO CLICK allowed
                elif len(results.multi_hand_landmarks) > 0:
                     active_hand_idx = 0
                     is_strict_pointing = False 

                if active_hand_idx != -1:
                    hand_landmarks = results.multi_hand_landmarks[active_hand_idx]
                    index_tip = hand_landmarks.landmark[8]
                    
                    cx, cy = int(index_tip.x * w_cam), int(index_tip.y * h_cam)
                    
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

            # 3. Interaction Logic
            if screen_point:
                # Move Cursor
                try: pyautogui.moveTo(screen_point[0], screen_point[1], _pause=False)
                except: pass

                # Check Press only if STRICTLY POINTING
                press_progress = self.check_hover_press(screen_point, is_strict_pointing)
                
                # Render Cursor
                color = (0, 255, 0)
                if press_progress > 0:
                    radius = int(30 * press_progress)
                    cv2.circle(proj_display, screen_point, 30, (100, 100, 100), 2)
                    cv2.circle(proj_display, screen_point, radius, color, -1)
                else: 
                    # Smaller cursor if just moving
                    cursor_color = (0, 255, 255) if is_strict_pointing else (100, 100, 100)
                    cv2.circle(proj_display, screen_point, 15, cursor_color, -1)
                    if not is_strict_pointing:
                         cv2.putText(proj_display, "POINT TO CLICK", (screen_point[0]+20, screen_point[1]), 
                                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)

                if press_progress >= 1.0:
                    # CLICK TRIGGERED
                    self.toggle_video()
                    self.ripple_animations.append({'x': screen_point[0], 'y': screen_point[1], 'r': 10, 'alpha': 255})
                    self.press_start_time = time.time()
                    self.click_cooldown = 20 # Slower repeat

            # 4. Render Ripples
            new_ripples = []
            for r in self.ripple_animations:
                # White Expanding Ring
                cv2.circle(proj_display, (r['x'], r['y']), r['r'], (255, 255, 255), 4)  
                r['r'] += 8
                if r['r'] < 150:
                    new_ripples.append(r)
            self.ripple_animations = new_ripples

            cv2.imshow("Projector", proj_display)
            cv2.imshow("Camera Feed (CLICK HERE)", frame)
            
            k = cv2.waitKey(1)
            if k == 27: break
        
        self.cleanup()

    def cleanup(self):
        if self.cap.isOpened(): self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    app = WallTouch()
    app.calibrate()
    app.run()
