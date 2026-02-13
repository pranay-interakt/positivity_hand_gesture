const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const socket = io('http://localhost:5001');

console.log("Connecting to Vision Engine on port 5001...");

let width, height;
function resize() {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
}
window.addEventListener('resize', resize);
resize();

// --- BROWSER PRIVACY BYPASS & FULLSCREEN ---
const primer = document.getElementById('interaction-primer');

function goFullscreen() {
    if (document.documentElement.requestFullscreen) {
        document.documentElement.requestFullscreen();
    } else if (document.documentElement.webkitRequestFullscreen) {
        document.documentElement.webkitRequestFullscreen();
    }
}

document.addEventListener('click', () => {
    primer.style.display = 'none';
    console.log("🚀 Interaction enabled. Fullscreen requested.");
    goFullscreen();

    // Prime the video
    const video = document.getElementById('vibe-video');
    video.play().then(() => {
        video.pause();
    }).catch(e => console.error("Video Prime Error:", e));
}, { once: true });

// --- CURSOR HIDER ---
document.body.style.cursor = 'none';

// --- CONCENTRIC WAVE EFFECT ---
class Wave {
    constructor(x, y, delay = 0) {
        this.x = x; this.y = y;
        this.radius = 0;
        this.alpha = 1.0;
        this.delay = delay;
        this.speed = 5; // Slower, tighter expansion
        this.maxRadius = Math.min(width, height) * 0.15; // Smaller footprint
    }
    update() {
        if (this.delay > 0) {
            this.delay--;
            return;
        }
        this.radius += this.speed;
        this.alpha = 1 - (this.radius / this.maxRadius);
    }
    draw() {
        if (this.delay > 0 || this.alpha <= 0) return;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(0, 242, 255, ${this.alpha * 0.8})`;
        ctx.lineWidth = 3;
        ctx.stroke();

        // Secondary subtle glow
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius + 20, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(0, 242, 255, ${this.alpha * 0.2})`;
        ctx.lineWidth = 10;
        ctx.stroke();
    }
}

let ripples = [];

function createWaveImpact(x, y) {
    for (let i = 0; i < 4; i++) {
        ripples.push(new Wave(x, y, i * 10));
    }
}

function animate() {
    ctx.clearRect(0, 0, width, height);
    for (let i = ripples.length - 1; i >= 0; i--) {
        ripples[i].update();
        ripples[i].draw();
        if (ripples[i].alpha <= 0) ripples.splice(i, 1);
    }
    requestAnimationFrame(animate);
}
animate();

// --- LOGIC ---
const video = document.getElementById('vibe-video');
let isVideoActive = false;

socket.on('connect', () => {
    console.log("✅ Connected to Vision Engine!");
});

socket.on('click', (data) => {
    console.log("🖱️ SIGNAL RECEIVED:", data);
    handleTap(data.x * width, data.y * height);
});

// --- KEYBOARD / MOUSE FALLBACK ---
document.addEventListener('keydown', (e) => {
    if (e.code === 'Space' || e.code === 'Enter') {
        if (primer.style.display === 'none') {
            handleTap(width / 2, height / 2);
        }
    }
});

document.addEventListener('click', (e) => {
    if (primer.style.display !== 'none') return;
    handleTap(e.clientX, e.clientY);
});

function handleTap(x, y) {
    createWaveImpact(x, y);

    if (isVideoActive) {
        stopVideo();
    } else {
        startVideo();
    }
}

function startVideo() {
    isVideoActive = true;
    document.body.classList.add('video-active');
    video.style.display = 'block';
    video.classList.add('playing');
    video.currentTime = 0;
    video.muted = false;
    video.loop = true; // Loop as requested until re-tap

    video.play().catch(e => {
        console.error("Video Play Failed:", e);
    });
}

function stopVideo() {
    isVideoActive = false;
    video.classList.remove('playing');
    document.body.classList.remove('video-active');

    setTimeout(() => {
        video.pause();
        video.style.display = 'none';
        video.currentTime = 0;
    }, 500);
}

