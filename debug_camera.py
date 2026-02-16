
import cv2
import numpy as np

print("Opening camera (0)...")
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Camera 0 failed. Trying 1...")
    cap = cv2.VideoCapture(1)

if not cap.isOpened():
    print("FATAL: No camera found.")
    exit(1)

print("Camera opened. Creating windows...")

cv2.namedWindow("Test Camera Feed", cv2.WINDOW_NORMAL)
cv2.moveWindow("Test Camera Feed", 50, 50) # Laptop screen

cv2.namedWindow("Test Projector", cv2.WINDOW_NORMAL)
cv2.moveWindow("Test Projector", 800, 50) # Laptop screen (preview)

frame_num = 0
while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to read frame.")
        break
    
    # Check if frame is all black
    mean_val = np.mean(frame)
    if mean_val < 5:
        color = (0, 0, 255) # RED TEXT if camera is suspiciously black
        status = f"CAMERA FEED BLACK (Mean: {mean_val:.1f})"
    else:
        color = (0, 255, 0) # GREEN TEXT if camera sees light
        status = f"Camera OK (Mean: {mean_val:.1f})"

    # Draw on Camera Feed
    cv2.putText(frame, status, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    cv2.putText(frame, f"Frame: {frame_num}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.imshow("Test Camera Feed", frame)

    # Draw on Projector Window (Bright Red Background)
    proj_img = np.zeros((600, 800, 3), dtype=np.uint8)
    proj_img[:] = (0, 0, 255) # ALL RED
    cv2.putText(proj_img, "PROJECTOR TEST - RED SCREEN", (50, 300), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.imshow("Test Projector", proj_img)

    k = cv2.waitKey(1)
    if k == 27:
        break
    
    frame_num += 1

cap.release()
cv2.destroyAllWindows()
