const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const socket = io('http://localhost:5001');

let width, height;
function resize() {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
}
window.addEventListener('resize', resize);
resize();

// --- SCHEMATIC UI SYSTEM ---
const nodes = [];
const connections = [];

class Node {
    constructor(id, x, y, label, type = 'MODULE') {
        this.id = id;
        this.x = x;
        this.y = y;
        this.label = label;
        this.type = type;
        this.activeLevel = 0; // 0 to 1
        this.radius = type === 'CORE' ? 60 : 35;
    }

    draw() {
        // Outline
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(0, 242, 255, ${0.3 + this.activeLevel})`;
        ctx.lineWidth = 2 + (this.activeLevel * 5);
        ctx.stroke();

        // Fill
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius - 5, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(0, 20, 40, 0.9)`;
        ctx.fill();

        // Inner Glow
        if (this.activeLevel > 0.01) {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(0, 242, 255, ${this.activeLevel * 0.3})`;
            ctx.fill();
        }

        // Label
        ctx.fillStyle = `rgba(255, 255, 255, ${0.7 + this.activeLevel})`;
        ctx.font = `${this.type === 'CORE' ? 'bold 20px' : '14px'} monospace`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(this.label, this.x, this.y);

        // Decay
        this.activeLevel *= 0.95;
    }

    activate() {
        this.activeLevel = 1.0;
        // Trigger output
        connections.forEach(c => {
            if (c.from === this) c.spawnPacket();
        });

        // Update stats
        document.getElementById('flow-rate').innerText = Math.floor(Math.random() * 40 + 60) + "%";
    }
}

class Connection {
    constructor(from, to) {
        this.from = from;
        this.to = to;
        this.packets = [];
    }

    spawnPacket() {
        this.packets.push({ progress: 0, speed: 0.02 + Math.random() * 0.02 });
    }

    update() {
        this.packets.forEach(p => p.progress += p.speed);
        // Remove finished packets and trigger target
        for (let i = this.packets.length - 1; i >= 0; i--) {
            if (this.packets[i].progress >= 1.0) {
                this.packets.splice(i, 1);
                this.to.activate();
            }
        }
    }

    draw() {
        // Draw Line
        ctx.beginPath();
        ctx.moveTo(this.from.x, this.from.y);
        ctx.lineTo(this.to.x, this.to.y);
        ctx.strokeStyle = 'rgba(0, 242, 255, 0.1)';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Draw Packets
        this.packets.forEach(p => {
            const px = this.from.x + (this.to.x - this.from.x) * p.progress;
            const py = this.from.y + (this.to.y - this.from.y) * p.progress;

            ctx.beginPath();
            ctx.arc(px, py, 6, 0, Math.PI * 2);
            ctx.fillStyle = '#ff00ea';
            ctx.shadowBlur = 15;
            ctx.shadowColor = '#ff00ea';
            ctx.fill();
            ctx.shadowBlur = 0;
        });
    }
}

// Graph removed for button mode


// --- PARTICLE PHYSICS (TOUCH LAYER) ---
// (Keeping existing particle code...)

// --- RIPPLE VISUALS ---
class Ripple {
    constructor(x, y) {
        this.x = x; this.y = y;
        this.radius = 0;
        this.maxRadius = 300;
        this.alpha = 1.0;
    }
    update() {
        this.radius += 8;
        this.alpha -= 0.02;
    }
    draw() {
        if (this.alpha <= 0) return;

        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(0, 242, 255, ${this.alpha})`;
        ctx.lineWidth = 3;
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(this.x, this.y, Math.max(0, this.radius - 30), 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(255, 0, 234, ${this.alpha * 0.5})`;
        ctx.lineWidth = 2;
        ctx.stroke();
    }
}

let ripples = [];

function animate() {
    ctx.clearRect(0, 0, width, height);

    // Ripples (Middle)
    ripples.forEach((r, i) => {
        r.update();
        r.draw();
        if (r.alpha <= 0) ripples.splice(i, 1);
    });

    requestAnimationFrame(animate);
}
animate();

// Auto-pulse removed

// --- BUTTON INTERACTION ---
const button = document.getElementById('vibe-button');
const video = document.getElementById('vibe-video');
let buttonActive = false;
const BUTTON_RADIUS = 100; // Matches CSS 200px width/height / 2

// Center coordinates
let cx, cy;
function updateCenter() {
    cx = width / 2;
    cy = height / 2;
}
window.addEventListener('resize', updateCenter);
updateCenter();

// --- INTERACTION LOGIC ---
socket.on('click', (data) => {
    const rx = data.x * width;
    const ry = data.y * height;

    // Add visual splash
    ripples.push(new Ripple(rx, ry));

    // Check Button Hit
    const dist = Math.hypot(rx - cx, ry - cy);

    if (dist < BUTTON_RADIUS + 20) { // Tolerance
        if (!buttonActive) {
            buttonActive = true;
            button.classList.add('active');
            button.innerText = ""; // Hide text
            video.style.display = 'block';
            video.currentTime = 0;
            video.play();

            // Auto reset after video length (approx 2s or loop)
            // For now, let's keep it active for 3 seconds then reset
            setTimeout(() => {
                buttonActive = false;
                button.classList.remove('active');
                button.innerText = "PUSH ME";
                video.pause();
                video.style.display = 'none';
            }, 3000); // 3 seconds of vibe
        }
    }
});

// Touch feedback removed for clean UI

// --- CALIBRATION ---
const calibGuide = document.getElementById('calibration-guide');
socket.on('calibration_start', () => { calibGuide.style.display = 'block'; });
socket.on('calibration_end', () => { calibGuide.style.display = 'none'; });

// Initialize
// Graph is initialized by resize event
