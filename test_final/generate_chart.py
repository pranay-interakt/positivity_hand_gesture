
import cv2
import numpy as np
import math

# --- CONFIGURATION (Match Engine) ---
PROJECTOR_W = 1280
PROJECTOR_H = 720
NODE_RADIUS = 50

# --- CLASSES (Simplified for Drawing) ---
class Node:
    def __init__(self, x, y, label, node_type="normal"):
        self.x = int(x)
        self.y = int(y)
        self.label = label
        self.type = node_type
    
    def draw(self, canvas):
        # Draw Hexagon (Grey/White for print)
        # User might want a "Dark Mode" print or "Light Mode" print?
        # Usually for printing on a wall, white background with black lines is standard document style.
        # But if they want it to look "Tech", maybe they print a dark poster?
        # I'll generate a "Tech Dark" version since that matches the app style.
        
        color = (100, 100, 100) # Visible Grey
        thick = 3
        
        # Draw Hexagon
        pts = []
        for i in range(6):
            angle_deg = 60 * i
            angle_rad = math.radians(angle_deg)
            px = int(self.x + NODE_RADIUS * math.cos(angle_rad))
            py = int(self.y + NODE_RADIUS * math.sin(angle_rad))
            pts.append([px, py])
        cv2.polylines(canvas, [np.array(pts)], True, color, thick, cv2.LINE_AA)

        # Labels
        (tw, th), _ = cv2.getTextSize(self.label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
        ty = self.y + NODE_RADIUS + 30
        cv2.putText(canvas, self.label, (self.x - tw//2, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2, cv2.LINE_AA)

class Edge:
    def __init__(self, start_n, end_n):
        self.start = start_n
        self.end = end_n

    def draw(self, canvas):
        p1 = (self.start.x, self.start.y)
        p2 = (self.end.x, self.end.y)
        cv2.line(canvas, p1, p2, (60, 60, 60), 2, cv2.LINE_AA)

# --- SETUP GRAPH ---
n1 = Node(200, 360, "INPUT PROTOCOL", "start")
n2 = Node(500, 360, "AI CLEANING")
n3_up = Node(800, 200, "KOL MAPPING")
n3_mid = Node(800, 360, "DEEP SEEK")
n3_down = Node(800, 520, "RISK RADAR")
n4 = Node(1100, 360, "FINAL REPORT", "end")

nodes = [n1, n2, n3_up, n3_mid, n3_down, n4]
edges = [
    Edge(n1, n2),
    Edge(n2, n3_up), Edge(n2, n3_mid), Edge(n2, n3_down),
    Edge(n3_up, n4), Edge(n3_mid, n4), Edge(n3_down, n4)
]

# --- DRAW ---
canvas = np.zeros((PROJECTOR_H, PROJECTOR_W, 3), dtype=np.uint8)
canvas[:] = (20, 20, 25) # Dark Background matched to engine default (approx)

for e in edges: e.draw(canvas)
for n in nodes: n.draw(canvas)

# Save
output_path = "hakase_flowchart_print.png"
cv2.imwrite(output_path, canvas)
print(f"Flowchart saved to {output_path}")
