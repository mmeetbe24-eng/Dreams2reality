// frontend/static/monitor.js - Real-Time Multi-User Clinical Supervisor

let ws = null;
let activeSessionsMap = {};
let totalEventsCount = 0;
let currentSpectateId = null;
let specWaveT7 = [];
let specWaveT8 = [];
const MAX_SPEC_WAVE = 384;

let specCanvas, specCtx;
let sweepX = 0;

window.addEventListener("DOMContentLoaded", () => {
    initSupervisorWebSocket();
    initSpectatorCanvas();
    bindSupervisorControls();
});

function initSupervisorWebSocket() {
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const url = `${proto}//${window.location.host}/ws/monitor`;

    ws = new WebSocket(url);

    ws.onopen = () => {
        const badge = document.getElementById("sup-status");
        badge.textContent = "SUPERVISOR CONNECTED (LIVE)";
        badge.parentElement.style.borderColor = "rgba(16, 185, 129, 0.4)";
        badge.parentElement.style.color = "var(--emerald)";
    };

    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        handleSupervisorPacket(msg);
    };

    ws.onclose = () => {
        const badge = document.getElementById("sup-status");
        badge.textContent = "DISCONNECTED - RECONNECTING...";
        badge.parentElement.style.borderColor = "rgba(245, 158, 11, 0.4)";
        badge.parentElement.style.color = "var(--amber)";
        setTimeout(initSupervisorWebSocket, 2000);
    };
}

function handleSupervisorPacket(msg) {
    if (msg.type === "SUPERVISOR_INIT") {
        updateActiveSessions(msg.active_sessions || []);
    } else if (msg.type === "HEARTBEAT") {
        updateActiveSessions(msg.active_sessions || []);
        if (msg.spectate_data) {
            handleSpectateData(msg.spectate_data);
        }
    } else if (msg.type === "USER_CONNECTED") {
        logEvent("USER CONNECTED", msg.message, "feed-badge-connect");
        totalEventsCount++;
        document.getElementById("kpi-events-count").textContent = totalEventsCount;
    } else if (msg.type === "USER_DISCONNECTED") {
        logEvent("USER DISCONNECTED", msg.message, "feed-badge-action");
        totalEventsCount++;
        document.getElementById("kpi-events-count").textContent = totalEventsCount;
    } else if (msg.type === "USER_ACTION") {
        totalEventsCount++;
        document.getElementById("kpi-events-count").textContent = totalEventsCount;
        const act = msg.action;
        let detailStr = JSON.stringify(act.details || {});
        let badgeType = "feed-badge-action";

        if (act.action === "SET_SCENARIO") detailStr = `Switched EEG scenario to "${act.details.scenario}"`;
        else if (act.action === "SET_SPEED") detailStr = `Adjusted telemetry stream speed to ${act.details.speed}x`;
        else if (act.action === "TRIGGER_NIGHTMARE") {
            detailStr = `Simulated Acute Nightmare Spike Triggered!`;
            badgeType = "feed-badge-trauma";
        }
        else if (act.action === "TRIGGER_ARTIFACT") detailStr = `Injected Gross Motion Artifact (>250µV)`;
        else if (act.action === "DREAM_JOURNAL_SUBMITTED") {
            detailStr = `Logged Dream Journal: "${act.details.text || act.details.text_preview}" (Valence: ${act.details.valence}, Arousal: ${act.details.arousal})`;
            badgeType = "feed-badge-journal";
        }
        else if (act.action === "ACKNOWLEDGE_ALARM") detailStr = `Acknowledged bedside trauma alarm`;
        else if (act.action === "SUPERVISOR_INTERVENTION") detailStr = `Supervisor intervention dispatched: "${act.details.message}"`;
        else if (act.action === "COGNITIVE_TEST_COMPLETED") detailStr = `Completed Pre-Sleep Reaction Test (Mean Latency: ${act.details.mean_reaction_ms}ms)`;

        logEvent(act.action, `[${act.user_name}] ${detailStr}`, badgeType);
    } else if (msg.type === "ACUTE_TRAUMA_EVENT") {
        totalEventsCount++;
        document.getElementById("kpi-events-count").textContent = totalEventsCount;
        logEvent("ACUTE TRAUMA EPISODE", `🚨 Subject '${msg.user_name}' experiencing Nightmare episode in REM! (Severity: ${(msg.severity * 100).toFixed(0)}%, Archetype: ${msg.archetype})`, "feed-badge-trauma");
    }
}

function updateActiveSessions(sessions) {
    document.getElementById("table-timestamp").textContent = new Date().toLocaleTimeString();
    document.getElementById("kpi-active-users").textContent = sessions.length;

    let remCount = 0;
    let traumaCount = 0;

    const tbody = document.getElementById("participants-table-body");
    const targetSelect = document.getElementById("select-target-user");

    if (sessions.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" style="text-align: center; color: var(--text-muted); padding: 36px;">
                    No active participants connected right now.<br>
                    <a href="/session" target="_blank" style="color: var(--cyan); text-decoration: underline; margin-top: 8px; display: inline-block;">
                        Open a Participant Session Tab ↗
                    </a> to see live interactions here!
                </td>
            </tr>
        `;
        targetSelect.innerHTML = `<option value="">-- No Active Users --</option>`;
        document.getElementById("kpi-rem-count").textContent = 0;
        document.getElementById("kpi-trauma-count").textContent = 0;
        return;
    }

    const currentSelectedTarget = targetSelect.value;
    targetSelect.innerHTML = "";

    let rowsHtml = "";
    sessions.forEach((s) => {
        activeSessionsMap[s.session_id] = s;
        if (s.stage === "REM") remCount++;
        if (s.trauma_active) traumaCount++;

        const opt = document.createElement("option");
        opt.value = s.session_id;
        opt.textContent = `${s.user_name} (${s.session_id})`;
        if (s.session_id === currentSelectedTarget) opt.selected = true;
        targetSelect.appendChild(opt);

        const stageLower = (s.stage || "wake").toLowerCase();
        const stageBadge = `<span class="tag tag-${stageLower}">${s.stage || "Wake"}</span>`;

        const traumaBadge = s.trauma_active
            ? `<span class="tag tag-alert" style="animation: pulse-ring 1s infinite;">🚨 ACUTE SPIKE</span>`
            : `<span style="color: var(--emerald); font-size: 11px; font-family: var(--font-mono);">0 (Normal)</span>`;

        const isSpectating = s.session_id === currentSpectateId;
        const specBtn = isSpectating
            ? `<button onclick="closeSpectator()" style="width:auto; padding: 4px 8px; font-size: 11px; background: rgba(0, 242, 254, 0.2); border-color: var(--cyan); color: #fff;">Spectating ◉</button>`
            : `<button onclick="startSpectate('${s.session_id}', '${escapeHtml(s.user_name)}')" style="width:auto; padding: 4px 8px; font-size: 11px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12);">👁️ Spectate</button>`;

        rowsHtml += `
            <tr style="${isSpectating ? 'background: rgba(0, 242, 254, 0.05);' : ''}">
                <td>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div class="pulse-dot" style="background: ${s.trauma_active ? '#ef4444' : 'var(--emerald)'};"></div>
                        <b style="color: #fff;">${escapeHtml(s.user_name)}</b>
                    </div>
                </td>
                <td style="font-family: var(--font-mono); color: var(--cyan); font-size: 11.5px;">${s.session_id}</td>
                <td style="color: var(--text-secondary); font-size: 11.5px;">
                    ${s.dataset_record ? `<span style="color:var(--emerald);">PhysioNet (${s.dataset_record})</span>` : 'Virtual Simulator'}
                </td>
                <td style="font-family: var(--font-mono); font-size: 11.5px;">${formatDuration(s.duration_sec)}</td>
                <td>${stageBadge}</td>
                <td style="color: #cbd5e1; font-size: 12px;">${escapeHtml(s.dream_archetype || "Baseline")}</td>
                <td>${traumaBadge}</td>
                <td>
                    <div style="display: flex; gap: 6px; align-items: center;">
                        ${specBtn}
                        <button onclick="quickMessage('${s.session_id}', '${escapeHtml(s.user_name)}')" style="width:auto; padding: 4px 8px; font-size: 11px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12);">💬 Note</button>
                        <a href="/api/sessions/${s.session_id}/report-pdf" target="_blank" style="text-decoration:none;">
                            <button style="width:auto; padding: 4px 8px; font-size: 11px; background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.3); color: var(--amber);">PDF</button>
                        </a>
                    </div>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = rowsHtml;
    document.getElementById("kpi-rem-count").textContent = remCount;
    document.getElementById("kpi-trauma-count").textContent = traumaCount;
}

function logEvent(tag, message, badgeClass) {
    const feed = document.getElementById("event-feed-container");
    if (!feed) return;

    const timeStr = new Date().toLocaleTimeString() + "." + Math.floor(new Date().getMilliseconds() / 100);

    const item = document.createElement("div");
    item.className = "event-item";
    item.innerHTML = `
        <div class="event-header">
            <span class="feed-badge ${badgeClass}">${escapeHtml(tag)}</span>
            <span style="font-family: var(--font-mono); font-size: 10px;">${timeStr}</span>
        </div>
        <div class="event-msg" style="color: #e2e8f0; font-size: 11.5px;">
            ${escapeHtml(message)}
        </div>
    `;

    feed.insertBefore(item, feed.firstChild);

    while (feed.children.length > 50) {
        feed.removeChild(feed.lastChild);
    }
}

function startSpectate(sessionId, userName) {
    currentSpectateId = sessionId;
    const card = document.getElementById("spectator-card");
    card.style.display = "flex";
    document.getElementById("spec-user-title").textContent = `${userName} [${sessionId}]`;
    specWaveT7 = [];
    specWaveT8 = [];

    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: "SPECTATE", target_session_id: sessionId }));
    }
}

function closeSpectator() {
    currentSpectateId = null;
    document.getElementById("spectator-card").style.display = "none";
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: "STOP_SPECTATE" }));
    }
}

function handleSpectateData(data) {
    if (data.session_id !== currentSpectateId) return;

    if (data.t7_wave && data.t8_wave) {
        for (let i = 0; i < data.t7_wave.length; i++) {
            specWaveT7.push(data.t7_wave[i]);
            specWaveT8.push(data.t8_wave[i]);
            if (specWaveT7.length > MAX_SPEC_WAVE) specWaveT7.shift();
            if (specWaveT8.length > MAX_SPEC_WAVE) specWaveT8.shift();
        }
    }

    if (data.state) {
        document.getElementById("spec-t7-val").textContent = `${data.state.t7_uv.toFixed(1)} µV`;
        document.getElementById("spec-t8-val").textContent = `${data.state.t8_uv.toFixed(1)} µV`;
        document.getElementById("spec-scenario-val").textContent = data.scenario || "Standard";
    }
}

function quickMessage(sessionId, userName) {
    const text = prompt(`Enter clinical note or instruction to display on ${userName}'s screen:`, "Technician note: Please remain still for artifact calibration.");
    if (text) {
        fetch(`/api/sessions/${sessionId}/message`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text, level: "info" })
        });
    }
}

function bindSupervisorControls() {
    document.getElementById("btn-close-spectator").addEventListener("click", closeSpectator);

    document.getElementById("btn-send-supervisor-msg").addEventListener("click", () => {
        const select = document.getElementById("select-target-user");
        const targetId = select.value;
        const msg = document.getElementById("input-supervisor-msg").value.trim();

        if (!targetId) {
            alert("Please select a target participant first.");
            return;
        }
        if (!msg) {
            alert("Please enter a message to send.");
            return;
        }

        fetch(`/api/sessions/${targetId}/message`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: msg, level: "urgent" })
        }).then(() => {
            const st = document.getElementById("intervention-status");
            st.style.display = "block";
            setTimeout(() => st.style.display = "none", 3000);
            document.getElementById("input-supervisor-msg").value = "";
        });
    });
}

function initSpectatorCanvas() {
    specCanvas = document.getElementById("spec-canvas");
    specCtx = specCanvas.getContext("2d");

    const resize = () => {
        specCanvas.width = specCanvas.clientWidth * window.devicePixelRatio;
        specCanvas.height = specCanvas.clientHeight * window.devicePixelRatio;
    };
    resize();
    window.addEventListener("resize", resize);

    const renderLoop = () => {
        drawSpectatorOscilloscope();
        requestAnimationFrame(renderLoop);
    };
    requestAnimationFrame(renderLoop);
}

function drawSpectatorOscilloscope() {
    if (!specCtx || !currentSpectateId) return;

    const w = specCanvas.width;
    const h = specCanvas.height;
    specCtx.clearRect(0, 0, w, h);

    // Subtle Grid Lines
    specCtx.strokeStyle = "rgba(255, 255, 255, 0.05)";
    specCtx.lineWidth = 1;
    const gridCols = 12;
    for (let c = 0; c <= gridCols; c++) {
        const gx = (c / gridCols) * w;
        specCtx.beginPath();
        specCtx.moveTo(gx, 0);
        specCtx.lineTo(gx, h);
        specCtx.stroke();
    }
    const midY1 = h * 0.32;
    const midY2 = h * 0.72;

    // Baselines
    specCtx.strokeStyle = "rgba(0, 242, 254, 0.15)";
    specCtx.beginPath();
    specCtx.moveTo(0, midY1);
    specCtx.lineTo(w, midY1);
    specCtx.stroke();

    specCtx.strokeStyle = "rgba(245, 158, 11, 0.15)";
    specCtx.beginPath();
    specCtx.moveTo(0, midY2);
    specCtx.lineTo(w, midY2);
    specCtx.stroke();

    if (specWaveT7.length < 2) return;

    const scale = h * 0.0035;

    // T7 Cyan Waveform
    specCtx.shadowColor = "#00f2fe";
    specCtx.shadowBlur = 6;
    specCtx.strokeStyle = "#00f2fe";
    specCtx.lineWidth = 2;
    specCtx.beginPath();
    for (let i = 0; i < specWaveT7.length; i++) {
        const x = (i / MAX_SPEC_WAVE) * w;
        const y = midY1 - specWaveT7[i] * scale;
        if (i === 0) specCtx.moveTo(x, y);
        else specCtx.lineTo(x, y);
    }
    specCtx.stroke();

    // T8 Amber Waveform
    specCtx.shadowColor = "#f59e0b";
    specCtx.shadowBlur = 6;
    specCtx.strokeStyle = "#f59e0b";
    specCtx.lineWidth = 2;
    specCtx.beginPath();
    for (let i = 0; i < specWaveT8.length; i++) {
        const x = (i / MAX_SPEC_WAVE) * w;
        const y = midY2 - specWaveT8[i] * scale;
        if (i === 0) specCtx.moveTo(x, y);
        else specCtx.lineTo(x, y);
    }
    specCtx.stroke();
    specCtx.shadowBlur = 0;

    // Sweep cursor beam
    sweepX = (sweepX + 2.5) % w;
    specCtx.strokeStyle = "rgba(255, 255, 255, 0.4)";
    specCtx.lineWidth = 1.5;
    specCtx.beginPath();
    specCtx.moveTo(sweepX, 0);
    specCtx.lineTo(sweepX, h);
    specCtx.stroke();
}

function formatDuration(sec) {
    if (!sec || sec < 0) return "0s";
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

function escapeHtml(text) {
    if (!text) return "";
    return text.toString()
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
