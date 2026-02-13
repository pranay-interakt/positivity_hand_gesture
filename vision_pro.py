
import cv2
import numpy as np
import pyautogui
# from pynput.mouse import Button, Controller # Not really needed if we use pyautogui for easier clicking
import mediapipe as mp
import time
import math

# Using PyAutoGUI for simpler mouse control (already in requirements.txt if we add it)
# pip install pyautogui

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# Global Vars for Calibration
calibration_points = []
calibrating = True
warp_matrix = None
screen_width, screen_height = pyautogui.size()
# Maintain Aspect Ratio for Warped Image (Standard 16:9 for clean processing)
WARP_W, WARP_H = 1280, 720 

def mouse_callback(event, x, y, flags, param):
    global calibration_points
    if event == cv2.EVENT_LBUTTONDOWN and calibrating:
        if len(calibration_points) < 4:
            calibration_points.append((x, y))
            print(f"📍 Calibration Point {len(calibration_points)}: ({x}, {y})")

def get_perspective_transform(src_pts):
    # Destination points: Top-Left, Top-Right, Bottom-Right, Bottom-Left
    dst_pts = np.float32([
        [0, 0],
        [WARP_W, 0],
        [WARP_W, WARP_H],
        [0, WARP_H]
    ])
    return cv2.getPerspectiveTransform(src_pts, dst_pts)

def main():
    global calibrating, warp_matrix, calibration_points
    
    cap = cv2.VideoCapture(0)
    
    cv2.namedWindow('CLICK HERE - CAMERA FEED')
    cv2.setMouseCallback('CLICK HERE - CAMERA FEED', mouse_callback)

    print("--- INSTRUCTIONS ---")
    print("1. SETUP: Look at your COMPUTER SCREEN. Use your MOUSE to click the 4 corners of the PROJECTION in the 'CLICK HERE - CAMERA FEED' window.")
    print("   Order: TOP-LEFT -> TOP-RIGHT -> BOTTOM-RIGHT -> BOTTOM-LEFT")
    print("2. TRACKING: Once 4 points are set, walk to the wall.")
    print("   Use your OPEN HAND to touch the wall and trigger the video.")
    print("3. Press 'R' to reset calibration.")
    print("4. Press 'Q' to quit.")
    
    # Intentional Interaction State
    dwell_counter = 0
    last_stable_pos = (0, 0)
    STABILITY_THRESHOLD = 30 # px
    DWELL_REQUIRED = 5 # frames
    SIZE_THRESHOLD = 0.12 # relative size (dist 0-9)
    last_click_time = 0
    COOLDOWN = 1.5 # seconds between toggles

    while True:
        ret, frame = cap.read()
        if not ret: break

        display_frame = frame.copy()

        if calibrating:
            # ... (Calibration UI logic)
            prompts = [
                "STEP 1: Click TOP-LEFT of Projection",
                "STEP 2: Click TOP-RIGHT of Projection",
                "STEP 3: Click BOTTOM-RIGHT of Projection",
                "STEP 4: Click BOTTOM-LEFT of Projection"
            ]
            current_prompt = prompts[len(calibration_points)] if len(calibration_points) < 4 else "CALIBRATING..."
            
            cv2.rectangle(display_frame, (0, 0), (640, 80), (0, 0, 0), -1)
            cv2.putText(display_frame, "SETUP: CLICK HERE ON CORNERS", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(display_frame, current_prompt, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            for i, ptr in enumerate(calibration_points):
                cv2.circle(display_frame, ptr, 8, (0, 0, 255), -1)
                cv2.circle(display_frame, ptr, 4, (255, 255, 255), -1)
                if i > 0:
                    cv2.line(display_frame, calibration_points[i-1], ptr, (0, 255, 0), 2)
            
            if len(calibration_points) == 4:
                cv2.line(display_frame, calibration_points[3], calibration_points[0], (0, 255, 0), 2)
                src_pts = np.float32(calibration_points)
                try:
                    warp_matrix = get_perspective_transform(src_pts)
                    calibrating = False
                    print("✅ Calibration Complete! Switching to Tracking Mode.")
                except Exception as e:
                    print(f"❌ Calibration Failed: {e}")
                    calibration_points = []
        else:
            # --- TRACKING MODE ---
            if warp_matrix is not None:
                warped = cv2.warpPerspective(frame, warp_matrix, (WARP_W, WARP_H))
                rgb_warped = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)
                results = hands.process(rgb_warped)
                
                h, w, _ = warped.shape
                hand_detected = False

                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        # 1. Check for 5 Fingers Open
                        wrist = hand_landmarks.landmark[0]
                        mcp = hand_landmarks.landmark[9]
                        
                        # Calculate relative size (Distance 0 to 9)
                        hand_size = math.hypot(wrist.x - mcp.x, wrist.y - mcp.y)
                        
                        fingers_open = []
                        for tip_idx, pip_idx in [(8,6), (12,10), (16,14), (20,18)]:
                            tip = hand_landmarks.landmark[tip_idx]
                            pip = hand_landmarks.landmark[pip_idx]
                            fingers_open.append(math.hypot(tip.x - wrist.x, tip.y - wrist.y) > 
                                              math.hypot(pip.x - wrist.x, pip.y - wrist.y))
                        
                        is_open_hand = all(fingers_open)
                        cx, cy = int(mcp.x * w), int(mcp.y * h)
                        
                        # 2. Touch Detection (Size + Dwell)
                        if is_open_hand and hand_size > SIZE_THRESHOLD:
                            hand_detected = True
                            dist_to_last = math.hypot(cx - last_stable_pos[0], cy - last_stable_pos[1])
                            
                            if dist_to_last < STABILITY_THRESHOLD:
                                dwell_counter += 1
                                # Visual progress bar for "Pressing"
                                progress = min(dwell_counter / DWELL_REQUIRED, 1.0)
                                cv2.circle(warped, (cx, cy), int(20 + 30*progress), (0, 255, 255), 3)
                            else:
                                dwell_counter = 0
                                last_stable_pos = (cx, cy)
                            
                            if dwell_counter >= DWELL_REQUIRED:
                                if time.time() - last_click_time > COOLDOWN:
                                    screen_x = int((cx / WARP_W) * screen_width)
                                    screen_y = int((cy / WARP_H) * screen_height)
                                    print(f"🎯 INTENTIONAL TOUCH! Position: ({screen_x}, {screen_y}) | Size: {hand_size:.2f}")
                                    pyautogui.click(screen_x, screen_y)
                                    last_click_time = time.time()
                                    dwell_counter = 0 # reset after trigger
                                
                            cv2.circle(warped, (cx, cy), 20, (0, 255, 0), -1)
                            cv2.putText(warped, "NEAR WALL (STAY STEADY)", (cx-50, cy-50), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                        else:
                            dwell_counter = 0
                            cv2.circle(warped, (cx, cy), 10, (0, 0, 255), -1)
                            if not is_open_hand:
                                cv2.putText(warped, "OPEN HAND NEEDED", (cx-50, cy-30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1)
                            elif hand_size <= SIZE_THRESHOLD:
                                cv2.putText(warped, "TOUCH THE WALL", (cx-50, cy-30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1)

                if not hand_detected:
                    dwell_counter = 0

                cv2.imshow("Warped View (Screen)", warped)



        if not calibrating:
            cv2.putText(display_frame, "ACTIVE - TRACKING HANDS", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            # Show the warped area outline
            if len(calibration_points) == 4:
                 for i in range(4):
                    cv2.line(display_frame, calibration_points[i], calibration_points[(i+1)%4], (0, 255, 0), 2)
        
        cv2.imshow('CLICK HERE - CAMERA FEED', display_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            calibration_points = []
            calibrating = True
            print("🔄 Reset Calibration")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
