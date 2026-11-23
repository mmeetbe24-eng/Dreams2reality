// frontend/static/app.js

let ws = null;
let waveBufferT7 = [];
let waveBufferT8 = [];
const MAX_WAVE_POINTS = 512;
let hypnogramData = [];
let isAlarmActive = false;
let audioCtx = null;

// Initialize on DOM load
window.addEventListener('DOMContentLoaded', () => {
    initWebSocket();
    initCanvasRenderers();
    bindControls();
});

function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/telemetry`;
    
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        document.getElementById('connection-status').textContent = 'CONNECTED';
        document.getElementById('connection-status').className = 'status-badge';
    };

    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        handleTelemetryPacket(msg);
    };

    ws.onclose = () => {
        document.getElementById('connection-status').textContent = 'RECONNECTING...';
        document.getElementById('connection-status').className = 'status-badge';
        setTimeout(initWebSocket, 2000);
    };
}

function handleTelemetryPacket(packet) {
    // 1. Add waveform samples
    if (packet.recent_wave_t7 && packet.recent_wave_t8) {
        for (let i = 0; i < packet.recent_wave_t7.length; i++) {
            waveBufferT7.push(packet.recent_wave_t7[i]);
            waveBufferT8.push(packet.recent_wave_t8[i]);
            if (waveBufferT7.length > MAX_WAVE_POINTS) waveBufferT7.shift();
            if (waveBufferT8.length > MAX_WAVE_POINTS) waveBufferT8.shift();
        }
    }

    // 2. Update status metrics
    const state = packet.state;
    if (state) {
        document.getElementById('val-t7').textContent = `${state.t7_uv.toFixed(1)} µV`;
        document.getElementById('val-t8').textContent = `${state.t8_uv.toFixed(1)} µV`;

        // Sleep stage badge
        const stageEl = document.getElementById('stage-badge');
        stageEl.textContent = state.stage;
        stageEl.className = `stage-badge-large stage-${state.stage.toLowerCase()}`;

        // Dream Archetype
        document.getElementById('archetype-name').textContent = state.dream_archetype;

        // Artifact Indicator
        const artEl = document.getElementById('artifact-indicator');
        if (state.artifact_detected) {
            artEl.textContent = 'MOTION ARTIFACT (>250µV REJECTED)';
            artEl.style.display = 'block';
        } else {
            artEl.style.display = 'none';
        }

        // Trauma Alarm Banner
        if (state.trauma_alert && !isAlarmActive) {
            triggerAlarmBanner(state);
        }

        // Update Affective Plane
        drawAffectPlane(state.valence, state.arousal);
    }

    // 3. Update Inference Details if present
    if (packet.inference) {
        const inf = packet.inference;
        if (inf.hypnogram_entry) {
            hypnogramData.push(inf.hypnogram_entry);
            if (hypnogramData.length > 120) hypnogramData.shift();
            drawHypnogram();
        }

        if (inf.stats && inf.stats.t8_powers) {
            updateSpectralBars(inf.stats.t8_powers);
        }
    }
}

function triggerAlarmBanner(state) {
    isAlarmActive = true;
    const banner = document.getElementById('alarm-banner');
    banner.classList.add('active');
    document.getElementById('alarm-text').textContent = 
        `BEDSIDE ALARM: ACUTE TRAUMA / NIGHTMARE DETECTED [Severity: ${(state.trauma_severity * 100).toFixed(0)}%]`;
    playBedsideChime();
}

function acknowledgeAlarm() {
    isAlarmActive = false;
    document.getElementById('alarm-banner').classList.remove('active');
}

function playBedsideChime() {
    try {
        if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(880, audioCtx.currentTime); // A5 note
        osc.frequency.exponentialRampToValueAtTime(440, audioCtx.currentTime + 0.5);
        gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.5);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.5);
    } catch (e) {
        console.warn('Audio chime blocked or unavailable:', e);
    }
}

function updateSpectralBars(powers) {
    const total = (powers.delta || 1) + (powers.theta || 1) + (powers.alpha || 1) + (powers.beta || 1) + (powers.gamma || 1);
    
    const setBar = (band, val) => {
        const pct = Math.min(100, Math.max(0, (val / total) * 100));
        const el = document.getElementById(`bar-${band}`);
        const textEl = document.getElementById(`pct-${band}`);
        if (el) el.style.width = `${pct.toFixed(1)}%`;
        if (textEl) textEl.textContent = `${pct.toFixed(0)}%`;
    };

    setBar('delta', powers.delta || 0);
    setBar('theta', powers.theta || 0);
    setBar('alpha', powers.alpha || 0);
    setBar('beta', powers.beta || 0);
    setBar('gamma', powers.gamma || 0);
}

// Canvas Renderers
let oscCanvas, oscCtx;
let hypCanvas, hypCtx;
let affCanvas, affCtx;

function initCanvasRenderers() {
    oscCanvas = document.getElementById('oscilloscope-canvas');
    oscCtx = oscCanvas.getContext('2d');

    hypCanvas = document.getElementById('hypnogram-canvas');
    hypCtx = hypCanvas.getContext('2d');

    affCanvas = document.getElementById('affect-canvas');
    affCtx = affCanvas.getContext('2d');

    resizeCanvases();
    window.addEventListener('resize', resizeCanvases);

    // Start 60 FPS animation loop
    requestAnimationFrame(renderLoop);
}

function resizeCanvases() {
    if (oscCanvas) {
        oscCanvas.width = oscCanvas.clientWidth * window.devicePixelRatio;
        oscCanvas.height = oscCanvas.clientHeight * window.devicePixelRatio;
    }
    if (hypCanvas) {
        hypCanvas.width = hypCanvas.clientWidth * window.devicePixelRatio;
        hypCanvas.height = hypCanvas.clientHeight * window.devicePixelRatio;
    }
    if (affCanvas) {
        affCanvas.width = 180 * window.devicePixelRatio;
        affCanvas.height = 180 * window.devicePixelRatio;
    }
}

function renderLoop() {
    drawOscilloscope();
    requestAnimationFrame(renderLoop);
}

function drawOscilloscope() {
    if (!oscCtx || waveBufferT7.length === 0) return;

    const w = oscCanvas.width;
    const h = oscCanvas.height;
    oscCtx.clearRect(0, 0, w, h);

    // Draw grid
    oscCtx.strokeStyle = '#111a28';
    oscCtx.lineWidth = 1;
    for (let y = 0; y < h; y += 30) {
        oscCtx.beginPath();
        oscCtx.moveTo(0, y);
        oscCtx.lineTo(w, y);
        oscCtx.stroke();
    }

    // Midlines for T7 and T8
    const midY1 = h * 0.30;
    const midY2 = h * 0.75;
    const scale = h * 0.0028; // scale microvolts to canvas

    // T7 Channel (Cyan)
    oscCtx.strokeStyle = '#00f2fe';
    oscCtx.lineWidth = 1.8;
    oscCtx.beginPath();
    for (let i = 0; i < waveBufferT7.length; i++) {
        const x = (i / MAX_WAVE_POINTS) * w;
        const y = midY1 - waveBufferT7[i] * scale;
        if (i === 0) oscCtx.moveTo(x, y);
        else oscCtx.lineTo(x, y);
    }
    oscCtx.stroke();

    // T8 Channel (Amber)
    oscCtx.strokeStyle = '#e87722';
    oscCtx.lineWidth = 1.8;
    oscCtx.beginPath();
    for (let i = 0; i < waveBufferT8.length; i++) {
        const x = (i / MAX_WAVE_POINTS) * w;
        const y = midY2 - waveBufferT8[i] * scale;
        if (i === 0) oscCtx.moveTo(x, y);
        else oscCtx.lineTo(x, y);
    }
    oscCtx.stroke();
}

function drawHypnogram() {
    if (!hypCtx || hypnogramData.length === 0) return;

    const w = hypCanvas.width;
    const h = hypCanvas.height;
    hypCtx.clearRect(0, 0, w, h);

    const stages = ["Wake", "REM", "N1", "N2", "N3"];
    const stageY = {
        "Wake": h * 0.15,
        "REM": h * 0.35,
        "N1": h * 0.55,
        "N2": h * 0.75,
        "N3": h * 0.90
    };

    // Stage horizontal guide lines
    hypCtx.strokeStyle = '#152033';
    hypCtx.lineWidth = 1;
    stages.forEach(st => {
        hypCtx.beginPath();
        hypCtx.moveTo(0, stageY[st]);
        hypCtx.lineTo(w, stageY[st]);
        hypCtx.stroke();
    });

    // Step chart line
    hypCtx.strokeStyle = '#a855f7';
    hypCtx.lineWidth = 2.2;
    hypCtx.beginPath();

    for (let i = 0; i < hypnogramData.length; i++) {
        const item = hypnogramData[i];
        const x = (i / (hypnogramData.length || 1)) * w;
        const y = stageY[item.stage] || stageY["Wake"];

        if (i === 0) {
            hypCtx.moveTo(x, y);
        } else {
            const prevY = stageY[hypnogramData[i - 1].stage] || stageY["Wake"];
            hypCtx.lineTo(x, prevY); // Step horizontal then vertical
            hypCtx.lineTo(x, y);
        }
    }
    hypCtx.stroke();
}

function drawAffectPlane(valence, arousal) {
    if (!affCtx) return;

    const w = affCanvas.width;
    const h = affCanvas.height;
    const cx = w / 2;
    const cy = h / 2;
    const r = (w / 2) - 8;

    affCtx.clearRect(0, 0, w, h);

    // Circular border
    affCtx.strokeStyle = '#1e293b';
    affCtx.lineWidth = 1.5;
    affCtx.beginPath();
    affCtx.arc(cx, cy, r, 0, 2 * Math.PI);
    affCtx.stroke();

    // Crosshairs
    affCtx.strokeStyle = '#152033';
    affCtx.beginPath();
    affCtx.moveTo(cx - r, cy);
    affCtx.lineTo(cx + r, cy);
    affCtx.moveTo(cx, cy - r);
    affCtx.lineTo(cx, cy + r);
    affCtx.stroke();

    // Plot point: valence (-1 to +1) on X, arousal (0 to 1) on Y (inverted so high arousal is top)
    const px = cx + (valence || 0) * (r * 0.85);
    const py = cy - ((arousal || 0.2) - 0.5) * 2 * (r * 0.85);

    // Glowing point
    affCtx.fillStyle = (arousal > 0.75 && valence < -0.3) ? '#ef4444' : '#00f2fe';
    affCtx.shadowColor = affCtx.fillStyle;
    affCtx.shadowBlur = 10;
    affCtx.beginPath();
    affCtx.arc(px, py, 6, 0, 2 * Math.PI);
    affCtx.fill();
    affCtx.shadowBlur = 0;
}

function bindControls() {
    // Scenario selector
    const scenarioSelect = document.getElementById('scenario-select');
    if (scenarioSelect) {
        scenarioSelect.addEventListener('change', (e) => {
            fetch('/api/control/scenario', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ scenario: e.target.value })
            });
        });
    }

    // Speed slider
    const speedRange = document.getElementById('speed-range');
    const speedVal = document.getElementById('speed-val');
    if (speedRange) {
        speedRange.addEventListener('input', (e) => {
            const spd = parseFloat(e.target.value);
            speedVal.textContent = `${spd}x`;
            fetch('/api/control/speed', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ speed: spd })
            });
        });
    }

    // Trigger buttons
    document.getElementById('btn-nightmare')?.addEventListener('click', () => {
        fetch('/api/control/trigger-nightmare', { method: 'POST' });
    });

    document.getElementById('btn-artifact')?.addEventListener('click', () => {
        fetch('/api/control/trigger-artifact', { method: 'POST' });
    });

    // Morning PDF Export
    document.getElementById('btn-export-pdf')?.addEventListener('click', () => {
        const patient = document.getElementById('patient-select')?.value || 'Subject-01';
        window.open(`/api/report/export-pdf?patient=${encodeURI(patient)}`, '_blank');
    });

    // Alarm dismiss button
    document.getElementById('btn-ack-alarm')?.addEventListener('click', acknowledgeAlarm);
}
