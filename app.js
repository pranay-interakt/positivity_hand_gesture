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

// --- BUTTON LOGIC ---
const button = document.getElementById('vibe-button');
const video = document.getElementById('vibe-video');
let isVibrating = false;

socket.on('click', (data) => {
    // If the hit is around the center (0.5, 0.5)
    if (data.x > 0.4 && data.x < 0.6 && data.y > 0.4 && data.y < 0.6) {
        if (!isVibrating) {
            triggerVibration();
        }
    }

    // Always spawn a ripple at the touch point
    ripples.push(new Ripple(data.x * width, data.y * height));
});

function triggerVibration() {
    isVibrating = true;
    button.classList.add('active');
    button.innerText = "";
    video.style.display = 'block';
    video.play();

    // Reset after 3 seconds
    setTimeout(() => {
        isVibrating = false;
        button.classList.remove('active');
        button.innerText = "PUSH ME";
        video.pause();
        video.style.display = 'none';
        video.currentTime = 0;
    }, 3000);
}
