import cv2
import numpy as np
import pyautogui
from pynput.mouse import Button, Controller
import mediapipe as mp
import time

# --- INITIALIZATION (Matches iPlanes Repo) ---
cap = cv2.VideoCapture(0)
time.sleep(1.1) 
mouse = Controller()
pts = [(0,0),(0,0),(0,0),(0,0)]
pointIndex = 0
# Logic uses the Warped AR (matches source.py)
AR = (720, 1280) 
oppts = np.float32([[0,0],[AR[1],0],[AR[1],AR[0]],[0,AR[0]]])

# --- MEDIAPIPE SETUP (Replacing the Red LED logic) ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

def draw_circle(event, x, y, flags, param):
    global img, pointIndex, pts
    if event == cv2.EVENT_LBUTTONDOWN:
        if pointIndex < 4:
            cv2.circle(img, (x, y), 5, (0, 255, 0), -1)
            pts[pointIndex] = (x, y)
            pointIndex += 1
            print(f"📍 Point {pointIndex} set: ({x}, {y})")

def get_persp(image, pts):
    ippts = np.float32(pts)
    Map = cv2.getPerspectiveTransform(ippts, oppts)
    warped = cv2.warpPerspective(image, Map, (AR[1], AR[0]))
    return warped

# --- STEP 1: CALIBRATION ---
cv2.namedWindow('img')
cv2.setMouseCallback('img', draw_circle)
print('--- CALIBRATION ---')
print('Order: Top-Left, Top-Right, Bottom-Right, Bottom-Left')

while True:
    ret, img = cap.read()
    if not ret: break
    
    cv2.putText(img, "CLICK 4 CORNERS ON YOUR LAPTOP SCREEN", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Draw existing points
    for p in pts:
        if p != (0,0): cv2.circle(img, p, 5, (0, 255, 0), -1)

    cv2.imshow('img', img)
    if pointIndex == 4 or (cv2.waitKey(1) & 0xFF == 27):
        break

cv2.destroyWindow('img')
print("✅ Calibration complete. Starting Tracking...")

# --- STEP 2: TRACKING (Double Tap Logic) ---
last_check = False
tap_count = 0
last_tap_time = 0
TAP_WINDOW = 0.5 # Must complete 2 taps within 0.5 seconds
COOLDOWN = 2.0   # Wait 2 seconds after a successful double tap
last_click_processed_time = 0

while True:
    ret, frame = cap.read()
    if not ret: break

    # 1. Warp the frame using calibrated points
    warped = get_persp(frame, pts)
    
    # 2. Process for Hand
    rgb_warped = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_warped)
    
    check = False
    target_pos = (0, 0)

    if results.multi_hand_landmarks:
        # Take the first hand detected
        hand_landmarks = results.multi_hand_landmarks[0]
        # MCP of middle finger
        mcp = hand_landmarks.landmark[9]
        target_pos = (mcp.x * AR[1], mcp.y * AR[0])
        check = True
        
        # Draw for debug
        cv2.circle(warped, (int(target_pos[0]), int(target_pos[1])), 15, (0, 255, 255), -1)

    # 3. DOUBLE TAP DETECTION
    current_time = time.time()
    width_scr, height_scr = pyautogui.size()
    
    # Check for the START of a tap (Hand just appeared)
    if check and not last_check:
        if current_time - last_click_processed_time > COOLDOWN:
            # If this is within the window of the previous tap, it's a double tap
            if current_time - last_tap_time < TAP_WINDOW:
                tap_count += 1
                if tap_count >= 2:
                    # TRIGGER DOUBLE TAP CLICK
                    m = (target_pos[0]/AR[1]) * 100
                    n = (target_pos[1]/AR[0]) * 100
                    k = (width_scr * m) / 100
                    c = (height_scr * n) / 100
                    
                    mouse.position = (int(k), int(c))
                    mouse.click(Button.left, 1) # Single click triggered by double-tap action
                    
                    print(f"� DOUBLE TAP DETECTED at ({int(k)}, {int(c)})! Triggering video.")
                    last_click_processed_time = current_time
                    tap_count = 0 
            else:
                # First tap of a new sequence
                tap_count = 1
                print("☝️ Tap 1...")
            
            last_tap_time = current_time

    last_check = check

    # Keep browser focused and hide system elements
    cv2.imshow('Warped View (Projection Area)', warped)
    
    if cv2.waitKey(5) & 0xFF == 27:
        break


cap.release()
cv2.destroyAllWindows()
