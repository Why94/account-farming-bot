// Stealth anti-detection scripts for Playwright
// Feature #10: Basic stealth
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});

// Hide chrome runtime
window.chrome = { runtime: {} };

// Override permissions query
Object.defineProperty(navigator, 'permissions', {
    get: () => ({
        query: (query) => Promise.resolve({ state: 'granted' })
    })
});

// Override plugins length
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5]
});

// Override languages
Object.defineProperty(navigator, 'languages', {
    get: () => ['en-US', 'en']
});

// Override webgl vendor
const originalWebGLGetParam = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(parameter) {
    if (parameter === 37445) return 'Google Inc. (AMD)';
    if (parameter === 37446) return 'ANGLE (AMD, AMD Radeon(TM) RX 560 Direct3D11 vs_5_0 ps_5_0)';
    return originalWebGLGetParam.call(this, parameter);
};

// Remove automation indicators
Object.defineProperty(navigator, 'connection', {
    get: () => ({
        effectiveType: '4g',
        rtt: 50,
        downlink: 10,
        saveData: false
    })
});
