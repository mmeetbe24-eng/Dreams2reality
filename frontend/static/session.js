// frontend/static/session.js - Advanced Neurotech Oscilloscope & Clinical Interface

let ws = null;
let sessionId = localStorage.getItem("d2r_session_id") || "SES-" + Math.floor(10000 + Math.random() * 90000);
localStorage.setItem("d2r_session_id", sessionId);

let userName = localStorage.getItem("d2r_user_name") || "Subject-" + sessionId.slice(-4);

let waveT7 = [];
let waveT8 = [];
const MAX_WAVE = 512;
let hypnogramHistory = [];
let isAlarmDismissed = false;
let audioCtx = null;
let oscGain = 1.0; // Oscilloscope vertical gain multiplier
let sweepIndex = 0; // Clinical sweep beam pointer

// Cognitive Assessment State
let reactionTrials = [];
let trialIndex = 0;
let trialStartTime = 0;
let trialTimer = null;
let calculatedProfile = null;

window.addEventListener("DOMContentLoaded", () => {
    document.getElementById("session-id-display").textContent = sessionId;
    const nameInput = document.getElementById("input-user-name");
    nameInput.value = userName;
    nameInput.addEventListener("change", (e) => {
        userName = e.target.value.trim() || ("Subject-" + sessionId.slice(-4));
        localStorage.setItem("d2r_user_name", userName);
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.close();
        }
    });

    initTelemetryWebSocket();
    initCanvases();
    bindControls();
    initAssessmentTest();
    initDatasetControls();
    initDreamTags();
});

function initTelemetryWebSocket() {
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const url = `${proto}//${window.location.host}/ws/telemetry?session_id=${encodeURIComponent(sessionId)}&user_name=${encodeURIComponent(userName)}`;

    ws = new WebSocket(url);

    ws.onopen = () => {
        const badge = document.getElementById("conn-status");
        badge.textContent = "LIVE 128Hz";
        badge.parentElement.style.color = "var(--emerald)";
    };

    ws.onmessage = (event) => {
        const packet = JSON.parse(event.data);

        // Supervisor Messages
        if (packet.type === "SUPERVISOR_MESSAGE") {
            const banner = document.getElementById("supervisor-banner");
            banner.classList.add("active");
            document.getElementById("supervisor-msg-text").textContent = `CLINICAL NOTE [${packet.message.time_str}]: ${packet.message.message}`;
            return;
        }

        handleTelemetry(packet);
    };

    ws.onclose = () => {
        const badge = document.getElementById("conn-status");
        badge.textContent = "RECONNECTING...";
        badge.parentElement.style.color = "var(--amber)";
        setTimeout(initTelemetryWebSocket, 2000);
    };
}

function handleTelemetry(packet) {
    // 1. Waveforms
    if (packet.recent_wave_t7 && packet.recent_wave_t8) {
        for (let i = 0; i < packet.recent_wave_t7.length; i++) {
            waveT7.push(packet.recent_wave_t7[i]);
            waveT8.push(packet.recent_wave_t8[i]);
            if (waveT7.length > MAX_WAVE) waveT7.shift();
            if (waveT8.length > MAX_WAVE) waveT8.shift();
            sweepIndex = (sweepIndex + 1) % MAX_WAVE;
        }
    }

    // 2. Metrics & State
    const st = packet.state;
    if (st) {
        document.getElementById("val-t7").textContent = `${st.t7_uv.toFixed(1)} µV`;
        document.getElementById("val-t8").textContent = `${st.t8_uv.toFixed(1)} µV`;

        const badge = document.getElementById("stage-badge");
        badge.textContent = st.stage;
        badge.className = `stage-badge-large stage-${st.stage.toLowerCase()}`;

        document.getElementById("archetype-name").textContent = st.dream_archetype;

        // Motion artifact badge
        const mBadge = document.getElementById("motion-badge");
        mBadge.style.display = st.artifact_detected ? "block" : "none";

        // Display Ground-Truth if in Dataset mode
        if (packet.playback_mode === "DATASET") {
            document.getElementById("ground-truth-badge").style.display = "block";
            document.getElementById("gt-stage-val").textContent = st.stage;
            document.getElementById("source-badge").textContent = `PhysioNet Sleep-EDFx (${packet.dataset_record_id || 'SC4001E0'})`;
        } else {
            document.getElementById("ground-truth-badge").style.display = "none";
        }

        // Acute Trauma Bedside Alarm
        if (st.trauma_alert && !isAlarmDismissed) {
            const banner = document.getElementById("alarm-banner");
            banner.classList.add("active");
            document.getElementById("alarm-text").textContent = 
                `BEDSIDE ALARM: ACUTE TRAUMA / NIGHTMARE DETECTED [Severity: ${(st.trauma_severity * 100).toFixed(0)}%]`;
            playBedsideChime();
        } else if (!st.trauma_alert) {
            isAlarmDismissed = false;
            document.getElementById("alarm-banner").classList.remove("active");
        }

        drawAffectPlane(st.valence, st.arousal);
    }

    // 3. Inference & Hypnogram
    if (packet.inference) {
        const inf = packet.inference;
        if (inf.hypnogram_entry) {
            hypnogramHistory.push(inf.hypnogram_entry);
            if (hypnogramHistory.length > 120) hypnogramHistory.shift();
            drawHypnogram();
        }
        if (inf.stats && inf.stats.t8_powers) {
            updateBands(inf.stats.t8_powers);
        }
    }
}

function initDatasetControls() {
    const srcSelect = document.getElementById("select-telemetry-source");
    const datasetGroup = document.getElementById("dataset-controls-group");
    const simGroup = document.getElementById("simulator-controls-group");
    const recSelect = document.getElementById("select-physionet-record");
    const fileUpload = document.getElementById("file-upload-eeg");

    srcSelect.addEventListener("change", (e) => {
        if (e.target.value === "DATASET") {
            datasetGroup.style.display = "flex";
            simGroup.style.display = "none";
            const chosenRec = recSelect.value;
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: "SET_DATASET_RECORD", record_id: chosenRec }));
            }
            document.getElementById("source-badge").textContent = `PhysioNet Sleep-EDFx (${chosenRec})`;
        } else {
            datasetGroup.style.display = "none";
            simGroup.style.display = "flex";
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: "SET_SIMULATOR_MODE" }));
            }
            document.getElementById("source-badge").textContent = "Virtual Telemetry Simulator";
        }
    });

    recSelect.addEventListener("change", (e) => {
        const recId = e.target.value;
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "SET_DATASET_RECORD", record_id: recId }));
        }
        document.getElementById("source-badge").textContent = `PhysioNet Sleep-EDFx (${recId})`;
    });

    // Custom File Upload
    fileUpload.addEventListener("change", (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);

        fetch(`/api/sessions/${encodeURIComponent(sessionId)}/dataset/upload`, {
            method: "POST",
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            alert(`File "${file.name}" uploaded successfully! Now streaming clinical channels.`);
            document.getElementById("source-badge").textContent = `Custom Upload: ${file.name}`;
            srcSelect.value = "DATASET";
            datasetGroup.style.display = "flex";
            simGroup.style.display = "none";
        })
        .catch(err => {
            alert("Error uploading file: " + err);
        });
    });
}

function bindControls() {
    // Gain Buttons on Oscilloscope
    document.querySelectorAll(".btn-gain").forEach(btn => {
        btn.addEventListener("click", (e) => {
            document.querySelectorAll(".btn-gain").forEach(b => b.classList.remove("active"));
            e.target.classList.add("active");
            oscGain = parseFloat(e.target.getAttribute("data-gain") || "1.0");
        });
    });

    // Scenario selector
    const sc = document.getElementById("select-scenario");
    sc.addEventListener("change", (e) => {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "SET_SCENARIO", scenario: e.target.value }));
        }
    });

    // Speed slider
    const spd = document.getElementById("slider-speed");
    const spdLbl = document.getElementById("speed-label");
    spd.addEventListener("input", (e) => {
        const val = parseFloat(e.target.value);
        spdLbl.textContent = `${val}x`;
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "SET_SPEED", speed: val }));
        }
    });

    // Triggers
    document.getElementById("btn-trigger-nightmare").addEventListener("click", () => {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "TRIGGER_NIGHTMARE" }));
        }
    });

    document.getElementById("btn-trigger-artifact").addEventListener("click", () => {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "TRIGGER_ARTIFACT" }));
        }
    });

    // Acknowledge alarm
    document.getElementById("btn-ack-alarm").addEventListener("click", () => {
        isAlarmDismissed = true;
        document.getElementById("alarm-banner").classList.remove("active");
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "ACKNOWLEDGE_ALARM" }));
        }
    });

    // Submit Dream Journal
    document.getElementById("btn-submit-journal").addEventListener("click", () => {
        const text = document.getElementById("journal-text").value.trim();
        const val = parseFloat(document.getElementById("journal-val").value) || 0.0;
        const aro = parseFloat(document.getElementById("journal-aro").value) || 0.5;
        if (!text) return;

        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: "SUBMIT_JOURNAL",
                text: text,
                valence: val,
                arousal: aro
            }));
            const fb = document.getElementById("journal-feedback");
            fb.style.display = "block";
            setTimeout(() => fb.style.display = "none", 3000);
            document.getElementById("journal-text").value = "";
        }
    });

    // PDF Export
    document.getElementById("btn-export-pdf").addEventListener("click", () => {
        window.open(`/api/sessions/${encodeURIComponent(sessionId)}/report-pdf`, "_blank");
    });
}

function initDreamTags() {
    document.querySelectorAll(".dream-tag-pill").forEach(pill => {
        pill.addEventListener("click", (e) => {
            const tag = e.target.textContent;
            const textarea = document.getElementById("journal-text");
            if (textarea.value) {
                textarea.value += " " + tag;
            } else {
                textarea.value = `Subjective report: ${tag} mentation episode.`;
            }
        });
    });
}

// Cognitive Assessment Test & Wizard
function initAssessmentTest() {
    const modal = document.getElementById("assessment-modal");
    const btnOpen = document.getElementById("btn-open-assessment");
    const btnClose = document.getElementById("btn-close-modal");
    const stressSlider = document.getElementById("assess-stress");
    const stressDisplay = document.getElementById("stress-val-display");
    const reactBox = document.getElementById("reaction-box");
    const reactRes = document.getElementById("reaction-results");
    const btnApply = document.getElementById("btn-apply-assessment");

    btnOpen.addEventListener("click", () => modal.classList.add("active"));
    btnClose.addEventListener("click", () => modal.classList.remove("active"));

    // Enable Apply button right away by computing a baseline profile
    updateAssessmentProfile();

    stressSlider.addEventListener("input", (e) => {
        stressDisplay.textContent = `${e.target.value} / 10`;
        updateAssessmentProfile();
    });

    document.getElementById("assess-ptsd").addEventListener("change", () => {
        updateAssessmentProfile();
    });

    let trialState = "idle";

    reactBox.addEventListener("click", () => {
        if (trialState === "idle") {
            startNextTrial();
        } else if (trialState === "waiting_green") {
            clearTimeout(trialTimer);
            reactBox.textContent = "Too early! Click to retry.";
            reactBox.classList.remove("ready");
            trialState = "idle";
        } else if (trialState === "green_ready") {
            const latency = Date.now() - trialStartTime;
            reactionTrials.push(latency);
            reactBox.classList.remove("ready");
            trialState = "idle";

            updateAssessmentProfile();

            if (reactionTrials.length < 3) {
                reactBox.textContent = `Trial ${reactionTrials.length} Done (${latency}ms)! Click for Trial ${reactionTrials.length + 1}`;
                reactRes.textContent = `Trial ${reactionTrials.length} / 3: ${latency}ms recorded. You can click 'Apply Calibration' below or click this box to do Trial ${reactionTrials.length + 1}!`;
            } else {
                reactBox.textContent = "✓ All 3 Trials Completed!";
                reactRes.textContent = `Completed 3/3 trials! Mean Latency: ${calculatedProfile.reaction_time_ms}ms. Click 'Apply Calibration' below!`;
            }
        }
    });

    function startNextTrial() {
        trialState = "waiting_green";
        reactBox.textContent = "Wait for GREEN...";
        reactBox.classList.remove("ready");
        const delay = 1000 + Math.random() * 1800;
        trialTimer = setTimeout(() => {
            trialState = "green_ready";
            reactBox.classList.add("ready");
            reactBox.textContent = "CLICK NOW!";
            trialStartTime = Date.now();
        }, delay);
    }

    function updateAssessmentProfile() {
        let meanLatency = 240;
        let jitter = 25;
        if (reactionTrials.length > 0) {
            const sum = reactionTrials.reduce((a, b) => a + b, 0);
            meanLatency = Math.round(sum / reactionTrials.length);
            const variance = reactionTrials.reduce((a, b) => a + Math.pow(b - meanLatency, 2), 0) / reactionTrials.length;
            jitter = Math.round(Math.sqrt(variance));
        }

        const stress = parseInt(stressSlider.value, 10) || 5;
        const ptsd = document.getElementById("assess-ptsd").value || "Occasional";

        const betaBias = (0.7 + (stress / 10.0) * 0.9 + Math.min(0.3, jitter / 100.0)).toFixed(2);
        const alphaBias = Math.max(0.4, 1.4 - (stress / 10.0) * 0.8).toFixed(2);

        calculatedProfile = {
            stress_level: stress,
            ptsd_frequency: ptsd,
            pre_sleep_state: stress > 7 ? "agitated" : "normal",
            reaction_time_ms: meanLatency,
            jitter_ms: jitter,
            beta_bias: parseFloat(betaBias),
            alpha_bias: parseFloat(alphaBias)
        };

        document.getElementById("res-latency").textContent = `${meanLatency} ms`;
        document.getElementById("res-jitter").textContent = `${jitter} ms`;
        document.getElementById("res-beta").textContent = `x${betaBias} (High-Beta Modulated)`;
        document.getElementById("calibration-summary").style.display = "block";

        btnApply.disabled = false;
        btnApply.style.opacity = "1";
        btnApply.style.cursor = "pointer";
    }

    btnApply.addEventListener("click", () => {
        if (!calculatedProfile) {
            updateAssessmentProfile();
        }

        fetch(`/api/sessions/${encodeURIComponent(sessionId)}/assessment`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(calculatedProfile)
        }).catch(() => {});

        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: "SUBMIT_ASSESSMENT",
                assessment: calculatedProfile
            }));
        }

        modal.classList.remove("active");
        document.getElementById("calibration-active-badge").style.display = "block";
        document.getElementById("btn-open-assessment").textContent = "⚙️ Re-Calibrate Baseline";
    });
}

function playBedsideChime() {
    try {
        if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = "sine";
        osc.frequency.setValueAtTime(880, audioCtx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(440, audioCtx.currentTime + 0.4);
        gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.4);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.4);
    } catch (e) {}
}

function updateBands(powers) {
    const total = (powers.delta || 1) + (powers.theta || 1) + (powers.alpha || 1) + (powers.beta || 1) + (powers.gamma || 1);
    const updateBar = (b, val) => {
        const pct = Math.min(100, Math.max(0, (val / total) * 100));
        document.getElementById(`bar-${b}`).style.width = `${pct}%`;
        document.getElementById(`pct-${b}`).textContent = `${pct.toFixed(0)}%`;
    };
    updateBar("delta", powers.delta || 0);
    updateBar("theta", powers.theta || 0);
    updateBar("alpha", powers.alpha || 0);
    updateBar("beta", powers.beta || 0);
    updateBar("gamma", powers.gamma || 0);
}

// Canvases
let oscCanvas, oscCtx;
let hypCanvas, hypCtx;
let affCanvas, affCtx;

function initCanvases() {
    oscCanvas = document.getElementById("osc-canvas");
    oscCtx = oscCanvas.getContext("2d");
    hypCanvas = document.getElementById("hypno-canvas");
    hypCtx = hypCanvas.getContext("2d");
    affCanvas = document.getElementById("affect-canvas");
    affCtx = affCanvas.getContext("2d");

    const resize = () => {
        oscCanvas.width = oscCanvas.clientWidth * window.devicePixelRatio;
        oscCanvas.height = oscCanvas.clientHeight * window.devicePixelRatio;
        hypCanvas.width = hypCanvas.clientWidth * window.devicePixelRatio;
        hypCanvas.height = hypCanvas.clientHeight * window.devicePixelRatio;
        affCanvas.width = 170 * window.devicePixelRatio;
        affCanvas.height = 170 * window.devicePixelRatio;
    };
    resize();
    window.addEventListener("resize", resize);

    const loop = () => {
        drawOscilloscope();
        requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
}

function drawOscilloscope() {
    if (!oscCtx || waveT7.length === 0) return;
    const w = oscCanvas.width;
    const h = oscCanvas.height;
    oscCtx.clearRect(0, 0, w, h);

    // Subtle Medical Grid
    oscCtx.strokeStyle = "rgba(255, 255, 255, 0.04)";
    oscCtx.lineWidth = 1;
    for (let y = 0; y < h; y += 25) {
        oscCtx.beginPath();
        oscCtx.moveTo(0, y);
        oscCtx.lineTo(w, y);
        oscCtx.stroke();
    }
    for (let x = 0; x < w; x += 50) {
        oscCtx.beginPath();
        oscCtx.moveTo(x, 0);
        oscCtx.lineTo(x, h);
        oscCtx.stroke();
    }

    const midY1 = h * 0.30;
    const midY2 = h * 0.75;
    const scale = h * 0.0028 * oscGain;

    // Draw Voltage Reference Labels
    oscCtx.font = "10px JetBrains Mono, monospace";
    oscCtx.fillStyle = "rgba(255, 255, 255, 0.25)";
    oscCtx.fillText("+100µV", 10, midY1 - 50 * scale);
    oscCtx.fillText("0µV", 10, midY1 + 3);
    oscCtx.fillText("-100µV", 10, midY1 + 50 * scale);

    oscCtx.fillText("+100µV", 10, midY2 - 50 * scale);
    oscCtx.fillText("0µV", 10, midY2 + 3);
    oscCtx.fillText("-100µV", 10, midY2 + 50 * scale);

    // T7 Channel (Neon Cyan Glow)
    oscCtx.strokeStyle = "#00f2fe";
    oscCtx.shadowColor = "#00f2fe";
    oscCtx.shadowBlur = 8;
    oscCtx.lineWidth = 2.0;
    oscCtx.beginPath();
    for (let i = 0; i < waveT7.length; i++) {
        const x = (i / MAX_WAVE) * w;
        const y = midY1 - waveT7[i] * scale;
        if (i === 0) oscCtx.moveTo(x, y);
        else oscCtx.lineTo(x, y);
    }
    oscCtx.stroke();

    // T8 Channel (Neon Amber Glow)
    oscCtx.strokeStyle = "#f59e0b";
    oscCtx.shadowColor = "#f59e0b";
    oscCtx.shadowBlur = 8;
    oscCtx.lineWidth = 2.0;
    oscCtx.beginPath();
    for (let i = 0; i < waveT8.length; i++) {
        const x = (i / MAX_WAVE) * w;
        const y = midY2 - waveT8[i] * scale;
        if (i === 0) oscCtx.moveTo(x, y);
        else oscCtx.lineTo(x, y);
    }
    oscCtx.stroke();
    oscCtx.shadowBlur = 0; // reset

    // Clinical Sweep Cursor Beam
    const sweepX = (sweepIndex / MAX_WAVE) * w;
    const grad = oscCtx.createLinearGradient(sweepX - 25, 0, sweepX, 0);
    grad.addColorStop(0, "rgba(0, 242, 254, 0)");
    grad.addColorStop(1, "rgba(0, 242, 254, 0.45)");
    oscCtx.fillStyle = grad;
    oscCtx.fillRect(sweepX - 25, 0, 25, h);

    oscCtx.strokeStyle = "#fff";
    oscCtx.lineWidth = 1.5;
    oscCtx.beginPath();
    oscCtx.moveTo(sweepX, 0);
    oscCtx.lineTo(sweepX, h);
    oscCtx.stroke();
}

function drawHypnogram() {
    if (!hypCtx || hypnogramHistory.length === 0) return;
    const w = hypCanvas.width;
    const h = hypCanvas.height;
    hypCtx.clearRect(0, 0, w, h);

    const stages = ["Wake", "REM", "N1", "N2", "N3"];
    const stageY = { "Wake": h * 0.15, "REM": h * 0.35, "N1": h * 0.55, "N2": h * 0.75, "N3": h * 0.90 };

    // Stage guides
    hypCtx.strokeStyle = "rgba(255, 255, 255, 0.05)";
    stages.forEach(st => {
        hypCtx.beginPath();
        hypCtx.moveTo(0, stageY[st]);
        hypCtx.lineTo(w, stageY[st]);
        hypCtx.stroke();
    });

    // Filled Area Gradient
    const areaGrad = hypCtx.createLinearGradient(0, 0, 0, h);
    areaGrad.addColorStop(0, "rgba(168, 85, 247, 0.35)");
    areaGrad.addColorStop(1, "rgba(99, 102, 241, 0.02)");

    hypCtx.beginPath();
    for (let i = 0; i < hypnogramHistory.length; i++) {
        const x = (i / (hypnogramHistory.length || 1)) * w;
        const y = stageY[hypnogramHistory[i].stage] || stageY["Wake"];
        if (i === 0) hypCtx.moveTo(x, y);
        else {
            const prevY = stageY[hypnogramHistory[i - 1].stage] || stageY["Wake"];
            hypCtx.lineTo(x, prevY);
            hypCtx.lineTo(x, y);
        }
    }
    // Close area for fill
    const lastX = w;
    hypCtx.lineTo(lastX, h);
    hypCtx.lineTo(0, h);
    hypCtx.closePath();
    hypCtx.fillStyle = areaGrad;
    hypCtx.fill();

    // Step line on top
    hypCtx.strokeStyle = "#a855f7";
    hypCtx.shadowColor = "#a855f7";
    hypCtx.shadowBlur = 6;
    hypCtx.lineWidth = 2.4;
    hypCtx.beginPath();
    for (let i = 0; i < hypnogramHistory.length; i++) {
        const x = (i / (hypnogramHistory.length || 1)) * w;
        const y = stageY[hypnogramHistory[i].stage] || stageY["Wake"];
        if (i === 0) hypCtx.moveTo(x, y);
        else {
            const prevY = stageY[hypnogramHistory[i - 1].stage] || stageY["Wake"];
            hypCtx.lineTo(x, prevY);
            hypCtx.lineTo(x, y);
        }
    }
    hypCtx.stroke();
    hypCtx.shadowBlur = 0;
}

function drawAffectPlane(val, aro) {
    if (!affCtx) return;
    const w = affCanvas.width;
    const h = affCanvas.height;
    const cx = w / 2;
    const cy = h / 2;
    const r = (w / 2) - 8;

    affCtx.clearRect(0, 0, w, h);
    affCtx.strokeStyle = "rgba(255, 255, 255, 0.08)";
    affCtx.lineWidth = 1.5;
    affCtx.beginPath();
    affCtx.arc(cx, cy, r, 0, 2 * Math.PI);
    affCtx.stroke();

    affCtx.beginPath();
    affCtx.moveTo(cx - r, cy);
    affCtx.lineTo(cx + r, cy);
    affCtx.moveTo(cx, cy - r);
    affCtx.lineTo(cx, cy + r);
    affCtx.stroke();

    const px = cx + (val || 0) * (r * 0.85);
    const py = cy - ((aro || 0.2) - 0.5) * 2 * (r * 0.85);

    // Glowing coordinate dot
    const isAlert = (aro > 0.75 && val < -0.3);
    affCtx.fillStyle = isAlert ? "#f43f5e" : "#00f2fe";
    affCtx.shadowColor = affCtx.fillStyle;
    affCtx.shadowBlur = 12;
    affCtx.beginPath();
    affCtx.arc(px, py, 6.5, 0, 2 * Math.PI);
    affCtx.fill();
    affCtx.shadowBlur = 0;
}
