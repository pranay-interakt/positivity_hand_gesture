
import cv2
import numpy as np
import mediapipe as mp
import math
import sys
import time

# --- CONFIGURATION ---
PROJECTOR_W = 1280
PROJECTOR_H = 720
CONTROL_W = 640
CONTROL_H = 480
CENTER_X = PROJECTOR_W // 2
CENTER_Y = PROJECTOR_H // 2

NODE_RADIUS = 50
PACKET_SPEED = 0.04
DWELL_SPEED = 0.05
DECAY_SPEED = 0.02

# --- VISUALIZATION CLASSES ---

class Node:
    def __init__(self, x, y, label, node_type="normal"):
        self.x = int(x)
        self.y = int(y)
        self.label = label
        self.type = node_type
        self.active = False
        self.hover_progress = 0.0
        self.pulse_phase = 0.0
    

    def update(self):
        self.pulse_phase += 0.15

    def draw(self, canvas, show_overlay=False, tx=0, ty=0, scale=1.0):
        # --- Transform Coordinates ---
        # Scale around center (CENTER_X, CENTER_Y), then translate
        sx = int((self.x - CENTER_X) * scale + CENTER_X + tx)
        sy = int((self.y - CENTER_Y) * scale + CENTER_Y + ty)
        s_radius = int(NODE_RADIUS * scale)

        # --- LOGIC: Draw Base if show_overlay is True ---
        if show_overlay:
            # Draw Base Hexagon (Grey)
            pts = []
            for i in range(6):
                angle_deg = 60 * i
                angle_rad = math.radians(angle_deg)
                px = int(sx + s_radius * math.cos(angle_rad))
                py = int(sy + s_radius * math.sin(angle_rad))
                pts.append([px, py])
            cv2.polylines(canvas, [np.array(pts)], True, (100, 100, 100), 2, cv2.LINE_AA)
            
            # Label (Approx pos)
            cv2.putText(canvas, self.label, (sx - 40, sy + s_radius + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5 * scale, (200, 200, 200), 1, cv2.LINE_AA)

        # --- Active Illumination (White Glow) ---
        if self.active:
            pulse = math.sin(self.pulse_phase) * 5
            
            # Draw Glowing Hexagon
            pts = []
            for i in range(6):
                angle_deg = 60 * i
                angle_rad = math.radians(angle_deg)
                px = int(sx + (s_radius + pulse) * math.cos(angle_rad))
                py = int(sy + (s_radius + pulse) * math.sin(angle_rad))
                pts.append([px, py])
            
            # Main Glow
            cv2.polylines(canvas, [np.array(pts)], True, (255, 255, 255), 4, cv2.LINE_AA)
            # Inner Detail
            cv2.polylines(canvas, [np.array(pts)], True, (200, 255, 255), 2, cv2.LINE_AA)

            # Special Colors for Start/End
            if self.type == "start":
                cv2.circle(canvas, (sx, sy), int(s_radius*0.6), (255, 255, 0), -1) # Cyan Center
            elif self.type == "end":
                cv2.circle(canvas, (sx, sy), int(s_radius*0.4), (200, 50, 0), -1) # Blue Center

        # --- Dwell Interaction (Cyan Ring) ---
        if self.hover_progress > 0:
            angle = 360 * self.hover_progress
            cv2.ellipse(canvas, (sx, sy), (s_radius+15, s_radius+15), -90, 0, angle, (255, 255, 0), 4, cv2.LINE_AA)


class Edge:
    def __init__(self, start_n, end_n):
        self.start = start_n
        self.end = end_n
        self.traveling = False
        self.progress = 0.0

    def trigger(self):
        if not self.traveling and not self.end.active:
            self.traveling = True
            self.progress = 0.0
    
    def update(self):
        if self.traveling:
            self.progress += PACKET_SPEED
            if self.progress >= 1.0:
                self.traveling = False
                self.progress = 0.0
                self.end.active = True
                return True # Triggered end
        return False

    def draw(self, canvas, show_overlay=False, tx=0, ty=0, scale=1.0):
        # Calculate Transformed Points
        sx1 = int((self.start.x - CENTER_X) * scale + CENTER_X + tx)
        sy1 = int((self.start.y - CENTER_Y) * scale + CENTER_Y + ty)
        sx2 = int((self.end.x - CENTER_X) * scale + CENTER_X + tx)
        sy2 = int((self.end.y - CENTER_Y) * scale + CENTER_Y + ty)

        p1 = (sx1, sy1)
        p2 = (sx2, sy2)
        
        # Base Line (Alignment Mode Only)
        if show_overlay:
            cv2.line(canvas, p1, p2, (60, 60, 60), 2, cv2.LINE_AA)
        
        # Active Connection
        if self.start.active:
             cv2.line(canvas, p1, p2, (50, 50, 50), 1, cv2.LINE_AA)

        if self.end.active: 
             cv2.line(canvas, p1, p2, (200, 200, 200), 2, cv2.LINE_AA)

        # Data Packet
        if self.traveling:
            curr_x = int(p1[0] + (p2[0]-p1[0])*self.progress)
            curr_y = int(p1[1] + (p2[1]-p1[1])*self.progress)
            
            # Glow
            cv2.circle(canvas, (curr_x, curr_y), 15, (255, 255, 0), 2)
            cv2.circle(canvas, (curr_x, curr_y), 8, (255, 255, 255), -1)


class HakaseEngine:
    def __init__(self):
        # 1. Windows (Persistent)
        cv2.namedWindow("Projector", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Projector", PROJECTOR_W, PROJECTOR_H)
        
        cv2.namedWindow("Control", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Control", CONTROL_W, CONTROL_H)
        cv2.setMouseCallback("Control", self.mouse_callback)

        # 2. Camera
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        # 3. MediaPipe
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.mp_draw = mp.solutions.drawing_utils

        # 4. State
        self.calibrated = False
        self.points_cam = []
        self.points_proj = []
        self.homography = None
        
        # 5. Graph
        self.nodes = []
        self.edges = []
        self.setup_graph()

        # Calibration Targets (Corners with margin)
        m = 100
        self.targets = [
            (m, m), 
            (PROJECTOR_W - m, m),
            (PROJECTOR_W - m, PROJECTOR_H - m), 
            (m, PROJECTOR_H - m)
        ]
        self.points_proj = np.array(self.targets, dtype=np.float32)

    def setup_graph(self):
        # Hakase Flow Layout
        n1 = Node(200, 360, "INPUT PROTOCOL", "start")
        n1.active = True
        
        n2 = Node(500, 360, "AI CLEANING")
        
        n3_up = Node(800, 200, "KOL MAPPING")
        n3_mid = Node(800, 360, "DEEP SEEK")
        n3_down = Node(800, 520, "RISK RADAR")
        
        n4 = Node(1100, 360, "FINAL REPORT", "end")
        
        self.nodes = [n1, n2, n3_up, n3_mid, n3_down, n4]
        
        self.edges.append(Edge(n1, n2))
        self.edges.append(Edge(n2, n3_up))
        self.edges.append(Edge(n2, n3_mid))
        self.edges.append(Edge(n2, n3_down))
        self.edges.append(Edge(n3_up, n4))
        self.edges.append(Edge(n3_mid, n4))
        self.edges.append(Edge(n3_down, n4))

        # --- RESET LOGIC ---
        self.reset_timer = None
        self.reset_duration = 5.0 # Seconds
        
        # --- VIEW MODES ---
        self.alignment_mode = True 
        
        # --- TRANSFORMS (Pan/Zoom) ---
        self.offset_x = 0
        self.offset_y = 0
        self.scale = 1.0

    def get_pos(self, x, y):
        # Applies current engine transform to a point
        sx = int((x - CENTER_X) * self.scale + CENTER_X + self.offset_x)
        sy = int((y - CENTER_Y) * self.scale + CENTER_Y + self.offset_y)
        return sx, sy

    def reset_flow(self):
        print("RESETTING FLOW...")
        for node in self.nodes:
            node.active = False
            node.hover_progress = 0.0
            node.pulse_phase = 0.0
        
        for edge in self.edges:
            edge.traveling = False
            edge.progress = 0.0
            
        # Activate Start Node
        self.nodes[0].active = True
        self.reset_timer = None

    def check_completion(self):
        # Check if ALL nodes are active
        all_active = all(n.active for n in self.nodes)
        if all_active:
            if self.reset_timer is None:
                self.reset_timer = time.time()
                print("FLOW COMPLETE! Resetting in 5s...")
            
            # Check elapsed time
            if time.time() - self.reset_timer > self.reset_duration:
                self.reset_flow()

    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if not self.calibrated and len(self.points_cam) < 4:
                frame_w = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                frame_h = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                
                scale_x = frame_w / CONTROL_W
                scale_y = frame_h / CONTROL_H
                
                real_x = x * scale_x
                real_y = y * scale_y
                
                self.points_cam.append([real_x, real_y])
                print(f"Point {len(self.points_cam)} captured at camera coords: {real_x}, {real_y}")

    def run(self):
        print("HAKASE ENGINE LAUNCHED")
        print("1. Calibration: Click 4 Red Points.")
        print("   - Look at Wall Projector.")
        print("   - Find matching Red Dot in 'Control' Window.")
        print("   - Click on the DOT in the 'Control' Window.")
        print("2. Alignment: Press 'a' to toggle the 'Wireframe' for aligning your poster.")
        
        # Position Windows
        cv2.moveWindow("Projector", 0, 0)
        cv2.moveWindow("Control", 800, 0) # Move to side
        
        while True:
            # --- 1. CAPTURE ---
            ret, frame = self.cap.read()
            if not ret: break
            
            # Create Canvases
            # Projector: Full HD Black
            proj_canvas = np.zeros((PROJECTOR_H, PROJECTOR_W, 3), dtype=np.uint8)
            proj_canvas[:] = (10, 10, 15) # Dark Blue BG
            
            # Control: Resized Camera View overlay
            control_view = cv2.resize(frame, (CONTROL_W, CONTROL_H))

            # --- 2. LOGIC ---
            
            if not self.calibrated:
                # === CALIBRATION MODE ===
                idx = len(self.points_cam)
                
                if idx < 4:
                    curr_target = self.targets[idx]
                    
                    # Projector: Show Target
                    # Draw a distinct color for the current target
                    cv2.circle(proj_canvas, (int(curr_target[0]), int(curr_target[1])), 40, (0, 0, 255), -1)
                    cv2.circle(proj_canvas, (int(curr_target[0]), int(curr_target[1])), 60, (0, 0, 255), 2)
                    
                    cv2.line(proj_canvas, (int(curr_target[0])-30, int(curr_target[1])), (int(curr_target[0])+30, int(curr_target[1])), (255, 255, 255), 2)
                    cv2.line(proj_canvas, (int(curr_target[0]), int(curr_target[1])-30), (int(curr_target[0]), int(curr_target[1])+30), (255, 255, 255), 2)

                    msg = f"CLICK POINT {idx+1}/4"
                    cv2.putText(proj_canvas, msg, (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)

                    # Control: Overlay Instructions
                    cv2.putText(control_view, f"CLICK RED DOT HERE ({idx+1}/4)", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    # Show previous clicks
                    frame_w = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                    frame_h = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                    sx = CONTROL_W / frame_w
                    sy = CONTROL_H / frame_h
                    
                    for pt in self.points_cam:
                        cx, cy = int(pt[0]*sx), int(pt[1]*sy)
                        cv2.circle(control_view, (cx, cy), 5, (0, 255, 0), -1)
                
                else:
                    # Calculate Homography
                    print("Computing Matrix...")
                    src = np.array(self.points_cam, dtype=np.float32)
                    dst = self.points_proj
                    try:
                        self.homography, _ = cv2.findHomography(src, dst)
                        if self.homography is None:
                            raise Exception("Homography Matrix is None (Points might be collinear?)")
                        self.calibrated = True
                        print("SUCCESS! Matrix Computed.")
                    except Exception as e:
                        print(f"Calibration Failed: {e}")
                        self.points_cam = [] # Retry

            else:
                # === INTERACTIVE MODE ===
                try:
                    # Hand Tracking
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = self.hands.process(frame_rgb)
                    
                    cursor = None
                    
                    if results.multi_hand_landmarks:
                        # DEBUG: Draw on Control View for verification
                        for hlm in results.multi_hand_landmarks:
                            self.mp_draw.draw_landmarks(control_view, hlm, self.mp_hands.HAND_CONNECTIONS)

                        for hand_lms in results.multi_hand_landmarks:
                            # Get Centroid
                            cx = sum([lm.x for lm in hand_lms.landmark]) / 21
                            cy = sum([lm.y for lm in hand_lms.landmark]) / 21
                            
                            # Convert to Camera Pixels
                            h, w, _ = frame.shape
                            cam_x, cam_y = cx * w, cy * h
                            
                            # Project to Screen
                            pt_cam = np.array([[[cam_x, cam_y]]], dtype=np.float32)
                            
                            if self.homography is not None:
                                pt_proj = cv2.perspectiveTransform(pt_cam, self.homography)
                                px, py = int(pt_proj[0][0][0]), int(pt_proj[0][0][1])
                                cursor = (px, py)
                            
                                # Interaction Check
                                if cursor:
                                    for node in self.nodes:
                                        # Transform Node Logic Position to Screen Position for Check
                                        nsx, nsy = self.get_pos(node.x, node.y)
                                        transformed_radius = NODE_RADIUS * self.scale
                                        
                                        if node.active:
                                            dist = math.hypot(cursor[0] - nsx, cursor[1] - nsy)
                                            if dist < transformed_radius * 1.5:
                                                node.hover_progress += DWELL_SPEED
                                                if node.hover_progress >= 1.0:
                                                    node.hover_progress = 1.0
                                                    # Trigger Outgoing Edges
                                                    for edge in self.edges:
                                                        if edge.start == node: edge.trigger()
                    
                    # Decay Progress
                    for node in self.nodes:
                        nsx, nsy = self.get_pos(node.x, node.y)
                        transformed_radius = NODE_RADIUS * self.scale
                        
                        if cursor:
                            dist = math.hypot(cursor[0] - nsx, cursor[1] - nsy)
                            if dist >= transformed_radius * 1.5:
                                node.hover_progress = max(0, node.hover_progress - DECAY_SPEED)
                        else:
                            node.hover_progress = max(0, node.hover_progress - DECAY_SPEED)
                    
                    # Updates
                    for node in self.nodes: node.update()
                    for edge in self.edges: edge.update()
                    self.check_completion()
                    
                    # Draw Scenegraph with Transforms
                    # Pass alignment mode flag and transforms
                    for edge in self.edges: 
                        edge.draw(proj_canvas, self.alignment_mode, self.offset_x, self.offset_y, self.scale)
                    for node in self.nodes: 
                        node.draw(proj_canvas, self.alignment_mode, self.offset_x, self.offset_y, self.scale)
                    
                    # Reset Timer Feedback
                    if self.reset_timer:
                        remaining = 5.0 - (time.time() - self.reset_timer)
                        cv2.putText(proj_canvas, f"RESETTING IN {int(remaining)+1}...", (PROJECTOR_W//2 - 200, PROJECTOR_H - 50), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

                    # Cursor Feedback
                    if cursor:
                        cv2.circle(proj_canvas, cursor, 20, (255, 255, 0), 2)
                        cv2.line(proj_canvas, (cursor[0]-10, cursor[1]), (cursor[0]+10, cursor[1]), (255, 255, 0), 1)
                        cv2.line(proj_canvas, (cursor[0], cursor[1]-10), (cursor[0], cursor[1]+10), (255, 255, 0), 1)

                    cv2.putText(control_view, "SYSTEM RUNNING", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    if self.alignment_mode:
                        cv2.putText(proj_canvas, "ALIGN: Used Arrow Keys to Move, W/S to Scale", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)
                        cv2.putText(proj_canvas, f"Pos: {self.offset_x},{self.offset_y} Scale: {self.scale:.2f}", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1)
                    
                    if not results.multi_hand_landmarks:
                        cv2.putText(control_view, "NO HAND DETECTED", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                except Exception as e:
                    print(f"INTERACTIVE LOOP ERROR: {e}")
                    # If catastrophic failure, maybe reset calibration?
                    # self.calibrated = False 

            # --- 3. DISPLAY ---
            cv2.imshow("Projector", proj_canvas)
            cv2.imshow("Control", control_view)
            
            # FPS Lock (approx 60)
            key = cv2.waitKey(16)
            if key == 27: break # ESC
            if key == ord('a'): 
                self.alignment_mode = not self.alignment_mode
            
            # Key Controls (Re-mapped to I/J/K/L for reliability)
            if self.alignment_mode:
                # Movement: I=Up, K=Down, J=Left, L=Right
                if key == ord('i'): 
                    self.offset_y -= 5
                    print("Moved UP")
                if key == ord('k'): 
                    self.offset_y += 5
                    print("Moved DOWN")
                if key == ord('j'): 
                    self.offset_x -= 5
                    print("Moved LEFT")
                if key == ord('l'): 
                    self.offset_x += 5
                    print("Moved RIGHT")
                
                # Scale: W=Zoom In, S=Zoom Out
                if key == ord('w'): 
                    self.scale += 0.02
                    print(f"Scaled IN: {self.scale:.2f}")
                if key == ord('s'): 
                    self.scale -= 0.02
                    print(f"Scaled OUT: {self.scale:.2f}")
        
        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    app = HakaseEngine()
    app.run()
