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
document.addEventListener('click', () => {
    primer.style.display = 'none';
    console.log("🚀 Interaction enabled. Video primed.");

    // Request Fullscreen
    if (document.documentElement.requestFullscreen) {
        document.documentElement.requestFullscreen();
    } else if (document.documentElement.webkitRequestFullscreen) { /* Safari */
        document.documentElement.webkitRequestFullscreen();
    }

    // Prime the video
    const video = document.getElementById('vibe-video');
    video.play().then(() => {
        video.pause(); // Just a tiny bit of play to satisfy Chrome
    }).catch(e => console.error("Video Prime Error:", e));
}, { once: true });

// --- RIPPLE EFFECT ---
class Ripple {
    constructor(x, y) {
        this.x = x; this.y = y;
        this.radius = 0;
        this.alpha = 1.0;
    }
    update() {
        this.radius += 10;
        this.alpha -= 0.02;
    }
    draw() {
        if (this.alpha <= 0) return;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(0, 242, 255, ${this.alpha})`;
        ctx.lineWidth = 4;
        ctx.stroke();
    }
}

let ripples = [];

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
let isVibrating = false;

socket.on('connect', () => {
    console.log("✅ Connected to Vision Engine!");
});

socket.on('click', (data) => {
    console.log("🖱️ SIGNAL RECEIVED:", data);

    // Always spawn ripple where touch was detected
    ripples.push(new Ripple(data.x * width, data.y * height));

    // Backend sends (0.5, 0.5) when hand hits target
    // We check if it's the "HIT" signal (which is usually centered)
    if (data.x > 0.4 && data.x < 0.6 && data.y > 0.4 && data.y < 0.6) {
        if (!isVibrating) {
            console.log("🎯 HIT TARGET! Triggering Vibe.");
            triggerVibration();
        }
    }
});

// --- KEYBOARD / MOUSE FALLBACK ---
document.addEventListener('keydown', (e) => {
    if (e.code === 'Space' || e.code === 'Enter') {
        if (!isVibrating && primer.style.display === 'none') {
            triggerVibration();
        }
    }
});

document.addEventListener('click', (e) => {
    // Determine if primer is active. If so, ignore (primer handles its own click)
    if (primer.style.display !== 'none') return;

    // Spawn ripple at click location
    ripples.push(new Ripple(e.clientX, e.clientY));

    // Check if click is near center (Visual Target Zone)
    // Update: Allow click ANYWHERE since target is hidden
    if (!isVibrating) {
        console.log("🖱️ MOUSE CLICK TRIGGERed Vibe.");
        triggerVibration();
    }
});

function triggerVibration() {
    isVibrating = true;

    // Add class to body to hide target
    document.body.classList.add('video-active');

    video.classList.add('playing');
    video.currentTime = 0;
    video.muted = false;
    video.loop = false;

    video.style.display = 'block'; // Ensure it's visible before playing

    video.play().then(() => {
        video.classList.add('playing'); // Ensure opacity transition happens
    }).catch(e => {
        console.error("Video Play Failed:", e);
        setTimeout(resetState, 2000);
    });

    video.onended = () => {
        resetState();
    };
}

function resetState() {
    isVibrating = false;
    document.body.classList.remove('video-active');
    video.classList.remove('playing');

    setTimeout(() => {
        video.pause();
        video.style.display = 'none';
        video.currentTime = 0;
    }, 500); // Wait for fade out
}
