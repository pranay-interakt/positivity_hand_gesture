// ========================================
// Hand Gesture Recognition Application
// ========================================

class GestureRecognitionApp {
    constructor() {
        // DOM Elements
        this.video = document.getElementById('webcam');
        this.canvas = document.getElementById('canvas');
        this.canvasCtx = this.canvas.getContext('2d');
        this.imageContainer = document.getElementById('imageContainer');
        this.statusElement = document.getElementById('status');
        this.currentGestureElement = document.getElementById('currentGesture');
        this.confidenceElement = document.getElementById('confidence');
        this.fpsElement = document.getElementById('fps');

        // State
        this.currentGesture = 'none';
        this.gestureConfidence = 0;
        this.isImageVisible = false;
        this.lastFrameTime = Date.now();
        this.frameCount = 0;
        this.fps = 0;

        // MediaPipe Hands
        this.hands = null;
        this.camera = null;

        // Gesture detection thresholds
        this.CONFIDENCE_THRESHOLD = 0.7;
        this.GESTURE_HOLD_FRAMES = 5;
        this.gestureFrameCount = 0;
        this.lastDetectedGesture = 'none';

        this.init();
    }

    async init() {
        try {
            this.updateStatus('Initializing camera...', '#f59e0b');
            await this.setupCamera();
            await this.setupMediaPipe();
            this.updateStatus('Ready! Show your gestures', '#10b981');
        } catch (error) {
            console.error('Initialization error:', error);
            this.updateStatus('Error: ' + error.message, '#ef4444');
        }
    }

    async setupCamera() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: 'user'
                }
            });

            this.video.srcObject = stream;

            return new Promise((resolve) => {
                this.video.onloadedmetadata = () => {
                    this.video.play();
                    this.canvas.width = this.video.videoWidth;
                    this.canvas.height = this.video.videoHeight;
                    resolve();
                };
            });
        } catch (error) {
            throw new Error('Camera access denied. Please allow camera permissions.');
        }
    }

    async setupMediaPipe() {
        this.hands = new Hands({
            locateFile: (file) => {
                return `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`;
            }
        });

        this.hands.setOptions({
            maxNumHands: 2,
            modelComplexity: 1,
            minDetectionConfidence: 0.7,
            minTrackingConfidence: 0.7
        });

        this.hands.onResults((results) => this.onResults(results));

        // Start camera processing
        this.camera = new Camera(this.video, {
            onFrame: async () => {
                await this.hands.send({ image: this.video });
                this.updateFPS();
            },
            width: 1280,
            height: 720
        });

        this.camera.start();
    }

    onResults(results) {
        // Clear canvas
        this.canvasCtx.save();
        this.canvasCtx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Draw hand landmarks if detected
        if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
            for (const landmarks of results.multiHandLandmarks) {
                // Draw connections
                drawConnectors(this.canvasCtx, landmarks, HAND_CONNECTIONS, {
                    color: '#6366f1',
                    lineWidth: 3
                });

                // Draw landmarks
                drawLandmarks(this.canvasCtx, landmarks, {
                    color: '#ec4899',
                    lineWidth: 2,
                    radius: 4
                });
            }

            // Detect gesture
            const gesture = this.detectGesture(results.multiHandLandmarks, results.multiHandedness);
            this.processGesture(gesture);
        } else {
            this.processGesture({ type: 'none', confidence: 0 });
        }

        this.canvasCtx.restore();
    }

    detectGesture(handLandmarks, handedness) {
        if (!handLandmarks || handLandmarks.length === 0) {
            return { type: 'none', confidence: 0 };
        }

        // Check for prayer hands (two hands together)
        if (handLandmarks.length === 2) {
            const prayerResult = this.detectPrayerHands(handLandmarks);
            if (prayerResult.confidence > this.CONFIDENCE_THRESHOLD) {
                return prayerResult;
            }
        }

        // Check for middle finger on each hand
        for (let i = 0; i < handLandmarks.length; i++) {
            const landmarks = handLandmarks[i];
            const middleFingerResult = this.detectMiddleFinger(landmarks);
            if (middleFingerResult.confidence > this.CONFIDENCE_THRESHOLD) {
                return middleFingerResult;
            }
        }

        return { type: 'none', confidence: 0 };
    }

    detectMiddleFinger(landmarks) {
        // Finger tip indices: thumb=4, index=8, middle=12, ring=16, pinky=20
        // Finger PIP indices: thumb=2, index=6, middle=10, ring=14, pinky=18

        const middleTip = landmarks[12];
        const middlePip = landmarks[10];
        const middleMcp = landmarks[9];

        const indexTip = landmarks[8];
        const indexPip = landmarks[6];

        const ringTip = landmarks[16];
        const ringPip = landmarks[14];

        const pinkyTip = landmarks[20];
        const pinkyPip = landmarks[18];

        const thumbTip = landmarks[4];
        const thumbIp = landmarks[3];

        // Middle finger should be extended (tip higher than PIP)
        const middleExtended = middleTip.y < middlePip.y && middlePip.y < middleMcp.y;

        // Other fingers should be curled (tip lower than PIP)
        const indexCurled = indexTip.y > indexPip.y;
        const ringCurled = ringTip.y > ringPip.y;
        const pinkyCurled = pinkyTip.y > pinkyPip.y;
        const thumbCurled = thumbTip.y > thumbIp.y;

        // Calculate confidence
        let confidence = 0;
        if (middleExtended) confidence += 0.4;
        if (indexCurled) confidence += 0.15;
        if (ringCurled) confidence += 0.15;
        if (pinkyCurled) confidence += 0.15;
        if (thumbCurled) confidence += 0.15;

        return {
            type: 'middle_finger',
            confidence: confidence
        };
    }

    detectPrayerHands(handLandmarks) {
        if (handLandmarks.length !== 2) {
            return { type: 'prayer', confidence: 0 };
        }

        const hand1 = handLandmarks[0];
        const hand2 = handLandmarks[1];

        // Get palm centers (landmark 0 is wrist, 9 is middle finger MCP)
        const palm1 = hand1[9];
        const palm2 = hand2[9];

        // Calculate distance between palms
        const palmDistance = Math.sqrt(
            Math.pow(palm1.x - palm2.x, 2) +
            Math.pow(palm1.y - palm2.y, 2)
        );

        // Get fingertip positions for both hands
        const fingertips1 = [hand1[4], hand1[8], hand1[12], hand1[16], hand1[20]];
        const fingertips2 = [hand2[4], hand2[8], hand2[12], hand2[16], hand2[20]];

        // Calculate average distance between corresponding fingertips
        let avgFingerDistance = 0;
        for (let i = 0; i < 5; i++) {
            const dist = Math.sqrt(
                Math.pow(fingertips1[i].x - fingertips2[i].x, 2) +
                Math.pow(fingertips1[i].y - fingertips2[i].y, 2)
            );
            avgFingerDistance += dist;
        }
        avgFingerDistance /= 5;

        // Check if hands are close together (prayer position)
        // Palms should be close, and fingers should be pointing upward
        const handsClose = palmDistance < 0.15 && avgFingerDistance < 0.2;

        // Check if fingers are pointing upward (y coordinate decreases from wrist to tips)
        let fingersUp = 0;
        for (let i = 1; i < 5; i++) { // Skip thumb
            if (fingertips1[i].y < hand1[0].y) fingersUp++;
            if (fingertips2[i].y < hand2[0].y) fingersUp++;
        }

        const fingersUpward = fingersUp >= 6; // At least 3 fingers on each hand

        // Calculate confidence
        let confidence = 0;
        if (handsClose) confidence += 0.6;
        if (fingersUpward) confidence += 0.4;

        return {
            type: 'prayer',
            confidence: confidence
        };
    }

    processGesture(gesture) {
        // Update debug info
        this.currentGestureElement.textContent = gesture.type.replace('_', ' ').toUpperCase();
        this.confidenceElement.textContent = (gesture.confidence * 100).toFixed(0) + '%';

        // Require gesture to be held for multiple frames to avoid false positives
        if (gesture.type === this.lastDetectedGesture) {
            this.gestureFrameCount++;
        } else {
            this.gestureFrameCount = 0;
            this.lastDetectedGesture = gesture.type;
        }

        // Only trigger action if gesture is held for enough frames
        if (this.gestureFrameCount >= this.GESTURE_HOLD_FRAMES) {
            if (gesture.type === 'middle_finger' && !this.isImageVisible) {
                this.showImage();
            } else if (gesture.type === 'prayer' && this.isImageVisible) {
                this.hideImage();
            }
        }
    }

    showImage() {
        this.isImageVisible = true;
        this.imageContainer.classList.remove('hidden');
        this.updateStatus('🖕 Image revealed!', '#ec4899');

        // Play reveal animation
        this.imageContainer.style.animation = 'none';
        setTimeout(() => {
            this.imageContainer.style.animation = 'fadeInRight 0.5s ease-out';
        }, 10);

        // Reset status after 2 seconds
        setTimeout(() => {
            if (this.isImageVisible) {
                this.updateStatus('Ready! Show your gestures', '#10b981');
            }
        }, 2000);
    }

    hideImage() {
        this.isImageVisible = false;
        this.imageContainer.classList.add('hidden');
        this.updateStatus('🙏 Image hidden!', '#8b5cf6');

        // Reset status after 2 seconds
        setTimeout(() => {
            if (!this.isImageVisible) {
                this.updateStatus('Ready! Show your gestures', '#10b981');
            }
        }, 2000);
    }

    updateStatus(message, color) {
        this.statusElement.textContent = message;
        this.statusElement.style.background = `linear-gradient(135deg, ${color}dd, ${color}aa)`;
    }

    updateFPS() {
        this.frameCount++;
        const now = Date.now();
        const elapsed = now - this.lastFrameTime;

        if (elapsed >= 1000) {
            this.fps = Math.round(this.frameCount * 1000 / elapsed);
            this.fpsElement.textContent = this.fps;
            this.frameCount = 0;
            this.lastFrameTime = now;
        }
    }
}

// Initialize the application when the page loads
window.addEventListener('DOMContentLoaded', () => {
    const app = new GestureRecognitionApp();
});
