
import cv2
import numpy as np
import mediapipe as mp
import math
import sys
import time

# --- CONFIGURATION ---

import cv2
import numpy as np
import mediapipe as mp
import math
import sys
import time

# --- CONFIGURATION ---
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
NODE_RADIUS = 50
PACKET_SPEED = 0.03 # 0.0 to 1.0 per frame

# --- STYLE UTILS ---
def draw_hexagon(img, center, size, color, thickness=1):
    pts = []
    for i in range(6):
        angle_deg = 60 * i - 30
        angle_rad = math.radians(angle_deg)
        x = int(center[0] + size * math.cos(angle_rad))
        y = int(center[1] + size * math.sin(angle_rad))
        pts.append([x, y])
    cv2.polylines(img, [np.array(pts)], True, color, thickness, cv2.LINE_AA)

def draw_tech_brackets(img, center, size, color, thickness=1, gap_angle=45):
    # Draw bracket-like shapes around center
    radius = size
    start_angle = 45 + gap_angle
    end_angle = 45 + 90 - gap_angle
    for i in range(4):
        cv2.ellipse(img, center, (radius, radius), 90*i, start_angle, end_angle, color, thickness, cv2.LINE_AA)

class Node:
    def __init__(self, x, y, label, type="normal"):
        self.x = x
        self.y = y
        self.label = label
        self.type = type # normal, start, end
        self.active = False
        self.hover_progress = 0.0 # 0.0 to 1.0 (for dwell trigger)
        
        # Style
        self.base_color = (100, 100, 100) # Dim Gray
        self.active_color = (255, 255, 255) # Bright White
        self.highlight_color = (0, 255, 255) # Cyan
        self.pulse_phase = 0

    def update(self):
        self.pulse_phase += 0.1

    def draw(self, img):
        color = self.active_color if self.active else self.base_color
        
        # 1. Outer Ring (Hexagon for Tech look)
        size = NODE_RADIUS
        if self.active:
            # Pulsing Effect
            pulse = math.sin(self.pulse_phase) * 5
            draw_hexagon(img, (self.x, self.y), int(size + pulse), color, 2)
            draw_hexagon(img, (self.x, self.y), int(size + pulse + 5), (color[0]//2, color[1]//2, color[2]//2), 1)
        else:
            draw_hexagon(img, (self.x, self.y), size, color, 2)

        # 2. Inner Elements
        if self.type == "start":
            cv2.circle(img, (self.x, self.y), int(size*0.6), self.highlight_color if self.active else color, -1)
        elif self.type == "end":
            draw_hexagon(img, (self.x, self.y), int(size*0.5), self.highlight_color if self.active else color, -1)
        else:
            # Tech Brackets Rotation
            draw_tech_brackets(img, (self.x, self.y), int(size*0.7), color, 2, gap_angle=10)
            cv2.circle(img, (self.x, self.y), 5, color, -1)

        # 3. Progress Ring (Dwell Feedback)
        if self.hover_progress > 0:
            cv2.ellipse(img, (self.x, self.y), (size+15, size+15), -90, 0, 360*self.hover_progress, (0, 255, 0), 3, cv2.LINE_AA)

        # 4. Label
        (tw, th), _ = cv2.getTextSize(self.label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        ty = self.y + size + 25
        # Background box for text readability
        cv2.rectangle(img, (self.x - tw//2 - 5, ty - th - 5), (self.x + tw//2 + 5, ty + 5), (20, 20, 20), -1)
        cv2.putText(img, self.label, (self.x - tw//2, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)

class Edge:
    def __init__(self, start_node, end_node):
        self.start = start_node
        self.end = end_node
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
                return True
        return False

    def draw(self, img):
        p1 = (self.start.x, self.start.y)
        p2 = (self.end.x, self.end.y)
        
        # Base Line
        color = (50, 50, 50)
        thickness = 2
        if self.start.active: 
            color = (100, 100, 100)
            thickness = 2
        if self.end.active: # Fully Connected
            color = (200, 200, 200)
            thickness = 3

        cv2.line(img, p1, p2, color, thickness, cv2.LINE_AA)

        # Traveling Packet (White Light)
        if self.traveling:
            px = int(p1[0] + (p2[0] - p1[0]) * self.progress)
            py = int(p1[1] + (p2[1] - p1[1]) * self.progress)
            
            # Glow for packet
            cv2.circle(img, (px, py), 8, (255, 255, 255), -1)
            cv2.circle(img, (px, py), 15, (200, 255, 255), 2)
            cv2.circle(img, (px, py), 25, (0, 100, 255), 1)

class HakaseFlow:
    def __init__(self):
        # 1. Setup Graph
        self.nodes = []
        self.edges = []
        self.setup_graph()

        # 2. Setup Camera
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.mp_draw = mp.solutions.drawing_utils

        # 3. Calibration State
        self.calibrated = False
        self.points_cam = []
        self.points_proj = []
        self.matrix = None
        
        self.width = WINDOW_WIDTH
        self.height = WINDOW_HEIGHT
        self.cursor_pos = None

        cv2.namedWindow("Projector", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Projector", self.width, self.height)

    def setup_graph(self):
        # Elaborate Flow for Hakase AI
        # Layer 1
        n_input = Node(150, 360, "Protocol Ingest", "start")
        n_input.active = True
        
        # Layer 2
        n_clean = Node(350, 360, "LLM Cleaning")
        
        # Layer 3 (Split)
        n_kol = Node(600, 180, "KOL Map")
        n_deep = Node(600, 360, "Deep Seek")
        n_risk = Node(600, 540, "Risk Radar")
        
        # Layer 4 (Re-Merge)
        n_strat = Node(850, 270, "Strategy Plan")
        n_comp = Node(850, 450, "Competitor Scan")
        
        # Layer 5
        n_final = Node(1100, 360, "Final Report", "end")

        self.nodes = [n_input, n_clean, n_kol, n_deep, n_risk, n_strat, n_comp, n_final]

        # Connections
        self.add_edge(n_input, n_clean)
        
        self.add_edge(n_clean, n_kol)
        self.add_edge(n_clean, n_deep)
        self.add_edge(n_clean, n_risk)
        
        self.add_edge(n_kol, n_strat)
        self.add_edge(n_deep, n_strat)
        
        self.add_edge(n_deep, n_comp)
        self.add_edge(n_risk, n_comp)
        
        self.add_edge(n_strat, n_final)
        self.add_edge(n_comp, n_final)

    def add_edge(self, n1, n2):
        self.edges.append(Edge(n1, n2))


    def calibrate_click(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and not self.calibrated:
            self.points_cam.append([x, y])
            print(f"Calibration Point: {len(self.points_cam)}")

    def run(self):
        # 1. SETUP PERMANENT WINDOWS
        cv2.namedWindow("Projector", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Projector", self.width, self.height)
        
        cv2.namedWindow("Control", cv2.WINDOW_NORMAL)
        cv2.setMouseCallback("Control", self.calibrate_click)
        cv2.resizeWindow("Control", 640, 480)
        
        print("--- APP STARTED [Persistent Windows Mode] ---")
        
        # Calibration Targets
        m = 100
        targets = [
            (m, m), (self.width-m, m), 
            (self.width-m, self.height-m), (m, self.height-m)
        ]
        self.points_proj = np.array(targets, dtype=np.float32)

        while True:
            # Create Blank Canvases
            proj_canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            control_canvas = np.zeros((480, 640, 3), dtype=np.uint8)

            # Capture Camera
            ret, frame = self.cap.read()
            if not ret: break
            
            # --- LOGIC SWITCH ---
            if not self.calibrated:
                # === CALIBRATION MODE ===
                
                # Control Window = Camera Feed
                control_canvas = cv2.resize(frame, (640, 480))
                
                # Projector Window = Red Dot Targets
                if len(self.points_cam) < 4:
                    curr = targets[len(self.points_cam)]
                    # Draw Crosshair
                    cv2.line(proj_canvas, (int(curr[0])-20, int(curr[1])), (int(curr[0])+20, int(curr[1])), (0, 0, 255), 3)
                    cv2.line(proj_canvas, (int(curr[0]), int(curr[1])-20), (int(curr[0]), int(curr[1])+20), (0, 0, 255), 3)
                    
                    cv2.putText(proj_canvas, f"CLICK TARGET {len(self.points_cam)+1}/4", (50, 100),
                                cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
                    
                    # Feedback on Control Window
                    for pt in self.points_cam:
                         # Scale point from camera res? No, clicks are in Control Window coords (640x480)
                         # Wait, click handler gives coords relative to window size.
                         # If we resize frame to 640x480, points are in 640x480 space.
                         # BUT homography needs points in CAMERA NATIVE space (1280x720) if we detect hands in native.
                         # So we must scale clicks.
                         pass
                    
                    cv2.putText(control_canvas, "CLICK RED DOT HERE", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                else:
                     # Compute (Scale points first!)
                     # Assuming clicks were on 640x480 window
                     # Camera is 1280x720. Scale X by 2, Y by 1.5.
                     scale_x = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH) / 640
                     scale_y = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT) / 480
                     
                     scaled_points = []
                     for p in self.points_cam:
                         scaled_points.append([p[0] * scale_x, p[1] * scale_y])
                     
                     pts_src = np.array(scaled_points, dtype=np.float32)
                     try:
                         self.matrix, _ = cv2.findHomography(pts_src, self.points_proj)
                         self.calibrated = True
                         print("CALIBRATION SUCCESS!")
                     except:
                         self.points_cam = []

            else:
                # === FLOW MODE ===
                
                # Update & Logic
                for node in self.nodes: node.update()
                
                # Hand Tracking (Native Resolution)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.hands.process(frame_rgb)
                
                self.cursor_pos = None
                hovered_node = None

                if results.multi_hand_landmarks:
                    for hand_lms in results.multi_hand_landmarks:
                        cx = sum([lm.x for lm in hand_lms.landmark]) / 21
                        cy = sum([lm.y for lm in hand_lms.landmark]) / 21
                        
                        h, w, _ = frame.shape
                        cam_pt = np.array([[[cx * w, cy * h]]], dtype=np.float32)
                        
                        if self.matrix is not None:
                            proj_pt = cv2.perspectiveTransform(cam_pt, self.matrix)
                            px, py = int(proj_pt[0][0][0]), int(proj_pt[0][0][1])
                            self.cursor_pos = (px, py)

                            for node in self.nodes:
                                if node.active:
                                    dist = math.hypot(px - node.x, py - node.y)
                                    if dist < NODE_RADIUS * 1.5:
                                        hovered_node = node
                
                # Node Trigger Logic ... (same as before)
                for node in self.nodes:
                    if node == hovered_node and node.active:
                        node.hover_progress += 0.05
                        if node.hover_progress >= 1.0:
                            node.hover_progress = 1.0
                            # Trigger
                            for edge in self.edges:
                                if edge.start == node: edge.trigger()
                    else:
                        node.hover_progress = max(0, node.hover_progress - 0.1)

                for edge in self.edges: edge.update()

                # Draw Projector
                proj_canvas[:] = (10, 10, 15)
                for edge in self.edges: edge.draw(proj_canvas)
                for node in self.nodes: node.draw(proj_canvas)
                if self.cursor_pos:
                    cv2.circle(proj_canvas, self.cursor_pos, 25, (100, 255, 100), 2)
                
                # Draw Control (Debug View)
                control_canvas = cv2.resize(frame, (640, 480))
                cv2.putText(control_canvas, "SYSTEM RUNNING", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)


            # SHOW WINDOWS
            cv2.imshow("Projector", proj_canvas)
            cv2.imshow("Control", control_canvas)

            if cv2.waitKey(1) == 27: break

        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    app = HakaseFlow()
    app.run()
