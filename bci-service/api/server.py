# bci-service/api/server.py
import asyncio
import os
import sys
import time
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Response, Query, Request, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

# Add parent path to allow module imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.session_manager import session_manager
from api.pdf_report import generate_clinical_pdf
from ingestion.dataset_loader import dataset_loader

app = FastAPI(
    title="Dreams2Reality BCI Service",
    description="Multi-User Real-Time BCI Platform with PhysioNet Sleep-EDFx Clinical Dataset Streaming",
    version="2.2.0"
)

# CORS configuration for cloud deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
static_dir = frontend_dir / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Models for request validation
class ControlRequest(BaseModel):
    action: str
    scenario: Optional[str] = None
    speed: Optional[float] = None

class JournalRequest(BaseModel):
    text: str
    valence: float = 0.0
    arousal: float = 0.5

class AssessmentRequest(BaseModel):
    stress_level: int = 5
    ptsd_frequency: str = "never"
    pre_sleep_state: str = "normal"
    reaction_time_ms: float = 300.0
    jitter_ms: float = 35.0

class DatasetLoadRequest(BaseModel):
    record_id: str

class SupervisorMessageRequest(BaseModel):
    message: str
    level: str = "info" # info, warning, urgent

# Health and status endpoints for Cloud deployments (Render, Railway, Fly, AWS)
@app.get("/healthz")
async def healthz():
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/api/status")
async def get_system_status():
    active_count = len(session_manager.active_sessions)
    supervisors_count = len(session_manager.supervisor_websockets)
    return {
        "status": "online",
        "service": "Dreams2Reality BCI Neural Platform",
        "version": "2.2.0-physionet",
        "active_users": active_count,
        "connected_supervisors": supervisors_count,
        "sampling_rate": 128,
        "bci_channels": ["T7", "T8"],
        "dataset_benchmark": "PhysioNet Sleep-EDFx (Sleep Cassette & Telemetry)",
        "available_records": len(dataset_loader.list_records()),
        "cloud_deployment_ready": True
    }

# Clinical Dataset Endpoints (PhysioNet Sleep-EDFx)
@app.get("/api/dataset/records")
async def get_dataset_records():
    return {
        "benchmark": "PhysioNet Sleep-EDF Database Expanded (Sleep-EDFx)",
        "records": dataset_loader.list_records()
    }

@app.post("/api/sessions/{session_id}/dataset/load")
async def load_clinical_record(session_id: str, req: DatasetLoadRequest):
    if session_id not in session_manager.active_sessions:
        raise HTTPException(status_code=404, detail="Active session not found")
    
    session = session_manager.active_sessions[session_id]
    success = session.worker.streamer.set_dataset_mode(req.record_id)
    if not success:
        raise HTTPException(status_code=400, detail=f"Could not load record '{req.record_id}'")

    session_manager.log_user_action(session_id, "DATASET_RECORD_LOADED", {
        "record_id": req.record_id,
        "source": "PhysioNet Sleep-EDFx Benchmark"
    })
    return {"status": "success", "playback_mode": "DATASET", "record_id": req.record_id}

@app.post("/api/sessions/{session_id}/dataset/mode")
async def set_playback_mode(session_id: str, mode: str = Query(default="SIMULATOR")):
    if session_id not in session_manager.active_sessions:
        raise HTTPException(status_code=404, detail="Active session not found")
    
    session = session_manager.active_sessions[session_id]
    if mode.upper() == "SIMULATOR":
        session.worker.streamer.set_simulator_mode()
        session_manager.log_user_action(session_id, "SET_SIMULATOR_MODE", {})
    return {"status": "success", "playback_mode": session.worker.streamer.playback_mode}

@app.post("/api/sessions/{session_id}/dataset/upload")
async def upload_custom_eeg_file(session_id: str, file: UploadFile = File(...)):
    if session_id not in session_manager.active_sessions:
        raise HTTPException(status_code=404, detail="Active session not found")
    
    content = await file.read()
    rec_id = dataset_loader.parse_and_save_uploaded_edf(file.filename, content)
    session = session_manager.active_sessions[session_id]
    session.worker.streamer.set_dataset_mode(rec_id)

    session_manager.log_user_action(session_id, "CUSTOM_EEG_FILE_UPLOADED", {
        "filename": file.filename,
        "record_id": rec_id,
        "file_size": len(content)
    })
    return {"status": "uploaded_and_streaming", "record_id": rec_id, "filename": file.filename}

# Session Management API Endpoints
@app.get("/api/sessions")
async def list_active_sessions():
    return {
        "count": len(session_manager.active_sessions),
        "sessions": session_manager.list_active_sessions()
    }

@app.get("/api/sessions/archived")
async def list_archived_sessions():
    return {
        "count": len(session_manager.archived_sessions),
        "sessions": session_manager.list_archived_sessions()
    }

@app.get("/api/sessions/{session_id}")
async def get_session_details(session_id: str):
    if session_id in session_manager.active_sessions:
        session = session_manager.active_sessions[session_id]
        return {
            "summary": session.to_summary(),
            "hypnogram": session.worker.hypnogram_history[-60:],
            "trauma_alerts": session.worker.trauma_alerts,
            "journals": session.dream_journals,
            "recent_actions": session.interaction_history[-20:],
            "assessment": session.cognitive_assessment
        }
    elif session_id in session_manager.archived_sessions:
        return session_manager.archived_sessions[session_id]
    raise HTTPException(status_code=404, detail="Session not found")

@app.post("/api/sessions/{session_id}/control")
async def control_user_session(session_id: str, req: ControlRequest):
    if session_id not in session_manager.active_sessions:
        raise HTTPException(status_code=404, detail="Active session not found")
    
    session = session_manager.active_sessions[session_id]
    action = req.action
    details = {}

    if action == "SET_SCENARIO" and req.scenario:
        session.worker.streamer.set_scenario(req.scenario)
        details = {"scenario": req.scenario}
    elif action == "SET_SPEED" and req.speed:
        session.worker.streamer.speed_multiplier = max(0.25, min(req.speed, 20.0))
        details = {"speed": session.worker.streamer.speed_multiplier}
    elif action == "TRIGGER_NIGHTMARE":
        session.worker.streamer.trigger_nightmare_spike()
        details = {"event": "acute_nightmare_spike"}
    elif action == "TRIGGER_ARTIFACT":
        session.worker.streamer.trigger_movement_artifact()
        details = {"event": "movement_artifact_injected"}
    elif action == "ACKNOWLEDGE_ALARM":
        session.worker.current_state["trauma_alert"] = False
        details = {"event": "bedside_alarm_acknowledged"}
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    session_manager.log_user_action(session_id, action, details)
    return {"status": "success", "action": action, "session_id": session_id}

@app.post("/api/sessions/{session_id}/assessment")
async def save_cognitive_assessment(session_id: str, req: AssessmentRequest):
    if session_id not in session_manager.active_sessions:
        raise HTTPException(status_code=404, detail="Active session not found")
    
    session = session_manager.active_sessions[session_id]
    data = req.model_dump() if hasattr(req, "model_dump") else req.dict()
    session.apply_assessment(data)

    session_manager.log_user_action(session_id, "COGNITIVE_ASSESSMENT_COMPLETED", {
        "stress": f"{req.stress_level}/10",
        "reaction_time_ms": f"{req.reaction_time_ms:.1f}ms",
        "jitter_ms": f"{req.jitter_ms:.1f}ms",
        "ptsd_risk": req.ptsd_frequency
    })
    return {"status": "calibrated", "session_id": session_id, "profile": data}

@app.post("/api/sessions/{session_id}/journal")
async def submit_dream_journal(session_id: str, req: JournalRequest):
    if session_id not in session_manager.active_sessions:
        raise HTTPException(status_code=404, detail="Active session not found")
    
    session = session_manager.active_sessions[session_id]
    entry = session.add_journal(req.text, req.valence, req.arousal)
    session_manager.log_user_action(session_id, "DREAM_JOURNAL_SUBMITTED", {
        "text_preview": req.text[:60] + "..." if len(req.text) > 60 else req.text,
        "valence": req.valence,
        "arousal": req.arousal
    })
    return {"status": "success", "journal": entry}

@app.post("/api/sessions/{session_id}/message")
async def send_supervisor_message(session_id: str, req: SupervisorMessageRequest):
    if session_id not in session_manager.active_sessions:
        raise HTTPException(status_code=404, detail="Active session not found")
    
    session = session_manager.active_sessions[session_id]
    msg_obj = {
        "timestamp": time.time(),
        "time_str": time.strftime("%H:%M:%S"),
        "message": req.message,
        "level": req.level
    }
    session.supervisor_messages.append(msg_obj)
    
    if session.websocket:
        try:
            await session.websocket.send_json({
                "type": "SUPERVISOR_MESSAGE",
                "message": msg_obj
            })
        except Exception:
            pass

    session_manager.log_user_action(session_id, "SUPERVISOR_INTERVENTION", {"message": req.message})
    return {"status": "delivered", "session_id": session_id}

@app.get("/api/sessions/{session_id}/report-pdf")
async def export_session_pdf(session_id: str):
    assessment_data = None
    if session_id in session_manager.active_sessions:
        session = session_manager.active_sessions[session_id]
        report_data = session.worker.get_summary_report_data()
        patient_name = session.user_name
        assessment_data = session.cognitive_assessment
    elif session_id in session_manager.archived_sessions:
        arch = session_manager.archived_sessions[session_id]
        report_data = arch["report"]
        patient_name = arch["summary"]["user_name"]
        assessment_data = arch.get("assessment")
    else:
        from inference.inference_worker import InferenceWorker
        temp_worker = InferenceWorker()
        report_data = temp_worker.get_summary_report_data()
        patient_name = "Subject-01"

    pdf_bytes = generate_clinical_pdf(report_data, patient_name=patient_name, session_id=session_id, assessment=assessment_data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Report_{session_id}_{patient_name.replace(' ', '_')}.pdf"}
    )

# HTML Web Pages (Multi-Page Architecture)
@app.get("/", response_class=HTMLResponse)
async def serve_portal():
    path = frontend_dir / "index.html"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return "<h1>Dreams2Reality Portal</h1>"

@app.get("/session", response_class=HTMLResponse)
@app.get("/cockpit", response_class=HTMLResponse)
async def serve_session_cockpit():
    path = frontend_dir / "session.html"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return "<h1>Participant Cockpit</h1>"

@app.get("/monitor", response_class=HTMLResponse)
@app.get("/admin", response_class=HTMLResponse)
async def serve_monitor():
    path = frontend_dir / "monitor.html"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return "<h1>Clinical Supervisor Monitor</h1>"

@app.get("/archive", response_class=HTMLResponse)
async def serve_archive():
    path = frontend_dir / "archive.html"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return "<h1>Trial Archive & Records</h1>"

# WebSocket 1: Participant / User Live Telemetry Channel
@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket, session_id: str = Query(default=""), user_name: str = Query(default="")):
    await websocket.accept()
    
    client_host = websocket.client.host if websocket.client else "127.0.0.1"
    headers = dict(websocket.headers)
    user_agent = headers.get("user-agent", "Browser Client")
    
    if not session_id:
        session_id = f"SES-{int(time.time() * 1000) % 100000:05d}"
    if not user_name:
        user_name = f"Subject-{session_id[-4:]}"

    session = session_manager.get_or_create_session(session_id, user_name, ip=client_host, user_agent=user_agent)
    session.websocket = websocket
    
    async def listen_for_client_controls():
        try:
            while True:
                data = await websocket.receive_json()
                msg_type = data.get("type", "")
                if msg_type == "SET_SCENARIO":
                    sc = data.get("scenario")
                    session.worker.streamer.set_scenario(sc)
                    session_manager.log_user_action(session_id, "SET_SCENARIO", {"scenario": sc})
                elif msg_type == "SET_DATASET_RECORD":
                    rec = data.get("record_id")
                    session.worker.streamer.set_dataset_mode(rec)
                    session_manager.log_user_action(session_id, "DATASET_RECORD_LOADED", {"record_id": rec})
                elif msg_type == "SET_SIMULATOR_MODE":
                    session.worker.streamer.set_simulator_mode()
                    session_manager.log_user_action(session_id, "SET_SIMULATOR_MODE", {})
                elif msg_type == "SET_SPEED":
                    sp = float(data.get("speed", 1.0))
                    session.worker.streamer.speed_multiplier = max(0.25, min(sp, 20.0))
                    session_manager.log_user_action(session_id, "SET_SPEED", {"speed": sp})
                elif msg_type == "TRIGGER_NIGHTMARE":
                    session.worker.streamer.trigger_nightmare_spike()
                    session_manager.log_user_action(session_id, "TRIGGER_NIGHTMARE", {"trigger": "manual_spike"})
                elif msg_type == "TRIGGER_ARTIFACT":
                    session.worker.streamer.trigger_movement_artifact()
                    session_manager.log_user_action(session_id, "TRIGGER_ARTIFACT", {"trigger": "motion_burst"})
                elif msg_type == "ACKNOWLEDGE_ALARM":
                    session.worker.current_state["trauma_alert"] = False
                    session_manager.log_user_action(session_id, "ACKNOWLEDGE_ALARM", {})
                elif msg_type == "SUBMIT_JOURNAL":
                    j_text = data.get("text", "")
                    j_val = float(data.get("valence", 0.0))
                    j_aro = float(data.get("arousal", 0.5))
                    session.add_journal(j_text, j_val, j_aro)
                    session_manager.log_user_action(session_id, "DREAM_JOURNAL_SUBMITTED", {
                        "text": j_text,
                        "valence": j_val,
                        "arousal": j_aro
                    })
                elif msg_type == "SUBMIT_ASSESSMENT":
                    assess_dict = data.get("assessment", {})
                    session.apply_assessment(assess_dict)
                    session_manager.log_user_action(session_id, "COGNITIVE_ASSESSMENT_COMPLETED", assess_dict)
        except WebSocketDisconnect:
            pass
        except Exception:
            pass

    listener_task = asyncio.create_task(listen_for_client_controls())

    try:
        while True:
            packet = session.worker.step(num_samples=16)
            packet["session_id"] = session_id
            packet["user_name"] = session.user_name
            packet["playback_mode"] = session.worker.streamer.playback_mode
            packet["dataset_record_id"] = session.worker.streamer.dataset_record_id

            await websocket.send_json(packet)

            if packet.get("state", {}).get("trauma_alert") and packet.get("inference"):
                asyncio.create_task(session_manager.broadcast_supervisor_event({
                    "type": "ACUTE_TRAUMA_EVENT",
                    "session_id": session_id,
                    "user_name": session.user_name,
                    "severity": packet["state"]["trauma_severity"],
                    "stage": packet["state"]["stage"],
                    "archetype": packet["state"]["dream_archetype"],
                    "time": time.time()
                }))

            await asyncio.sleep(0.08)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"User WebSocket closed: {e}")
    finally:
        listener_task.cancel()
        session_manager.remove_session(session_id)

# WebSocket 2: Live Supervisor Monitoring Channel
@app.websocket("/ws/monitor")
async def websocket_supervisor(websocket: WebSocket):
    await websocket.accept()
    session_manager.register_supervisor(websocket)
    spectate_target: Optional[str] = None

    await websocket.send_json({
        "type": "SUPERVISOR_INIT",
        "active_sessions": session_manager.list_active_sessions(),
        "archived_sessions": session_manager.list_archived_sessions(),
        "timestamp": time.time()
    })

    async def listen_for_supervisor_commands():
        nonlocal spectate_target
        try:
            while True:
                data = await websocket.receive_json()
                action = data.get("action")
                if action == "SPECTATE":
                    spectate_target = data.get("target_session_id")
                elif action == "STOP_SPECTATE":
                    spectate_target = None
                elif action == "SEND_ALERT":
                    tgt = data.get("target_session_id")
                    msg = data.get("message", "Attention required from Clinical Supervisor")
                    if tgt and tgt in session_manager.active_sessions:
                        session = session_manager.active_sessions[tgt]
                        if session.websocket:
                            await session.websocket.send_json({
                                "type": "SUPERVISOR_MESSAGE",
                                "message": {"time_str": time.strftime("%H:%M:%S"), "message": msg, "level": "urgent"}
                            })
        except WebSocketDisconnect:
            pass
        except Exception:
            pass

    cmd_task = asyncio.create_task(listen_for_supervisor_commands())

    try:
        while True:
            sessions_data = session_manager.list_active_sessions()
            payload = {
                "type": "HEARTBEAT",
                "active_sessions": sessions_data,
                "timestamp": time.time()
            }

            if spectate_target and spectate_target in session_manager.active_sessions:
                target_sess = session_manager.active_sessions[spectate_target]
                payload["spectate_data"] = {
                    "session_id": spectate_target,
                    "user_name": target_sess.user_name,
                    "t7_wave": list(target_sess.worker.live_waveform_t7)[-64:],
                    "t8_wave": list(target_sess.worker.live_waveform_t8)[-64:],
                    "state": target_sess.worker.current_state,
                    "scenario": target_sess.worker.streamer.scenario,
                    "playback_mode": target_sess.worker.streamer.playback_mode
                }

            await websocket.send_json(payload)
            await asyncio.sleep(0.3)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Supervisor WebSocket closed: {e}")
    finally:
        cmd_task.cancel()
        session_manager.unregister_supervisor(websocket)
