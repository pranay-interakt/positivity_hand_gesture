/**
 * Configuration File for Gesture Recognition App
 * Modify these settings to customize the app behavior
 */

const CONFIG = {
    // ========================================
    // Gesture Detection Settings
    // ========================================

    // Confidence threshold for gesture detection (0.0 - 1.0)
    // Lower = more sensitive, Higher = more strict
    confidenceThreshold: 0.7,

    // Number of consecutive frames a gesture must be held
    // Higher = more stable but slower response
    gestureHoldFrames: 5,

    // ========================================
    // Camera Settings
    // ========================================

    camera: {
        // Ideal camera resolution
        width: 1280,
        height: 720,

        // Which camera to use ('user' = front, 'environment' = back)
        facingMode: 'user',

        // Frame rate (higher = smoother but more CPU intensive)
        frameRate: 30
    },

    // ========================================
    // MediaPipe Hands Settings
    // ========================================

    mediaPipe: {
        // Maximum number of hands to detect (1 or 2)
        maxNumHands: 2,

        // Model complexity (0 = lite, 1 = full)
        // Higher = more accurate but slower
        modelComplexity: 1,

        // Minimum confidence for hand detection (0.0 - 1.0)
        minDetectionConfidence: 0.7,

        // Minimum confidence for hand tracking (0.0 - 1.0)
        minTrackingConfidence: 0.7
    },

    // ========================================
    // Visual Settings
    // ========================================

    visual: {
        // Show hand landmarks on video
        showLandmarks: true,

        // Hand connection line color
        connectionColor: '#6366f1',

        // Hand landmark point color
        landmarkColor: '#ec4899',

        // Line width for connections
        connectionLineWidth: 3,

        // Landmark point radius
        landmarkRadius: 4
    },

    // ========================================
    // Animation Settings
    // ========================================

    animation: {
        // Image reveal/hide animation duration (ms)
        transitionDuration: 500,

        // Status message auto-hide delay (ms)
        statusMessageDelay: 2000
    },

    // ========================================
    // Debug Settings
    // ========================================

    debug: {
        // Show debug panel
        showDebugPanel: true,

        // Log gestures to console
        logGestures: false,

        // Show FPS counter
        showFPS: true
    },

    // ========================================
    // Image Settings
    // ========================================

    image: {
        // Path to the image to display
        path: 'photo/6065510171_bb00e7222b_z.jpg',

        // Image fit mode ('cover', 'contain', 'fill')
        objectFit: 'cover'
    },

    // ========================================
    // Server Settings
    // ========================================

    server: {
        // Port number for the Python server
        port: 8000,

        // Enable CORS
        enableCORS: true
    }
};

// Export for use in app.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}
