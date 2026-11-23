# bci-service/api/session_manager.py
import time
import asyncio
from typing import Dict, List, Optional, Set
from fastapi import WebSocket
from inference.inference_worker import InferenceWorker

def safe_create_task(coro):
    """Safely schedules an async task if an event loop is running, or cancels it if in sync test context."""
    try:
        loop = asyncio.get_running_loop()
        return loop.create_task(coro)
    except RuntimeError:
        coro.close()
        return None

class UserSession:
    """Represents a live user interacting with the BCI application."""
    def __init__(self, session_id: str, user_name: str, ip_address: str = "127.0.0.1", user_agent: str = "Unknown"):
        self.session_id = session_id
        self.user_name = user_name
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.connected_at = time.time()
        self.last_active = time.time()
        self.is_active = True
        self.worker = InferenceWorker()
        self.interaction_history: List[Dict] = []
        self.dream_journals: List[Dict] = []
        self.supervisor_messages: List[Dict] = []
        self.cognitive_assessment: Optional[Dict] = None
        self.websocket: Optional[WebSocket] = None

    def log_action(self, action_type: str, details: Dict) -> Dict:
        now = time.time()
        self.last_active = now
        entry = {
            "timestamp": round(now, 2),
            "session_id": self.session_id,
            "user_name": self.user_name,
            "action": action_type,
            "details": details,
            "stage": self.worker.current_state.get("stage", "Wake"),
            "archetype": self.worker.current_state.get("dream_archetype", "Restful Baseline")
        }
        self.interaction_history.append(entry)
        if len(self.interaction_history) > 100:
            self.interaction_history.pop(0)
        return entry

    def add_journal(self, text: str, user_valence: float, user_arousal: float) -> Dict:
        now = time.time()
        self.last_active = now
        journal_entry = {
            "timestamp": round(now, 2),
            "time_str": time.strftime("%H:%M:%S", time.localtime(now)),
            "text": text,
            "user_valence": user_valence,
            "user_arousal": user_arousal,
            "predicted_stage": self.worker.current_state.get("stage", "REM"),
            "predicted_archetype": self.worker.current_state.get("dream_archetype", "Restful Baseline"),
            "trauma_severity": self.worker.current_state.get("trauma_severity", 0.0)
        }
        self.dream_journals.append(journal_entry)
        return journal_entry

    def apply_assessment(self, assessment_data: Dict):
        self.cognitive_assessment = assessment_data
        self.worker.streamer.apply_cognitive_profile(assessment_data)

    def to_summary(self) -> Dict:
        now = time.time()
        st = self.worker.current_state
        return {
            "session_id": self.session_id,
            "user_name": self.user_name,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent[:40] if self.user_agent else "Browser",
            "connected_at": round(self.connected_at, 1),
            "duration_sec": round(now - self.connected_at, 1),
            "last_active": round(self.last_active, 1),
            "is_active": self.is_active,
            "stage": st.get("stage", "Wake"),
            "dream_archetype": st.get("dream_archetype", "Restful Baseline"),
            "trauma_alert": st.get("trauma_alert", False),
            "trauma_severity": round(st.get("trauma_severity", 0.0), 2),
            "valence": round(st.get("valence", 0.0), 2),
            "arousal": round(st.get("arousal", 0.0), 2),
            "t7_uv": round(st.get("t7_uv", 0.0), 1),
            "t8_uv": round(st.get("t8_uv", 0.0), 1),
            "scenario": self.worker.streamer.scenario,
            "speed": self.worker.streamer.speed_multiplier,
            "total_actions": len(self.interaction_history),
            "total_journals": len(self.dream_journals),
            "total_traumas": len(self.worker.trauma_alerts),
            "calibrated": self.cognitive_assessment is not None,
            "assessment": self.cognitive_assessment
        }

class SessionManager:
    """Central supervisor coordinating live user sessions and broadcasting telemetry."""
    def __init__(self):
        self.active_sessions: Dict[str, UserSession] = {}
        self.archived_sessions: Dict[str, Dict] = {}
        self.supervisor_websockets: Set[WebSocket] = set()

    def get_or_create_session(self, session_id: str, user_name: str, ip: str = "127.0.0.1", user_agent: str = "Browser") -> UserSession:
        if session_id not in self.active_sessions:
            session = UserSession(session_id, user_name, ip_address=ip, user_agent=user_agent)
            self.active_sessions[session_id] = session
            safe_create_task(self.broadcast_supervisor_event({
                "type": "USER_CONNECTED",
                "session": session.to_summary(),
                "message": f"User '{user_name}' [{session_id}] connected from {ip}"
            }))
        else:
            session = self.active_sessions[session_id]
            if user_name and user_name != session.user_name:
                session.user_name = user_name
            session.is_active = True
            session.last_active = time.time()
        return session

    def remove_session(self, session_id: str):
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.is_active = False
            self.archived_sessions[session_id] = {
                "summary": session.to_summary(),
                "report": session.worker.get_summary_report_data(),
                "journals": session.dream_journals,
                "history": session.interaction_history,
                "assessment": session.cognitive_assessment
            }
            del self.active_sessions[session_id]
            safe_create_task(self.broadcast_supervisor_event({
                "type": "USER_DISCONNECTED",
                "session_id": session_id,
                "user_name": session.user_name,
                "message": f"User '{session.user_name}' [{session_id}] disconnected"
            }))

    def log_user_action(self, session_id: str, action_type: str, details: Dict):
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            action_entry = session.log_action(action_type, details)
            safe_create_task(self.broadcast_supervisor_event({
                "type": "USER_ACTION",
                "action": action_entry,
                "session": session.to_summary()
            }))

    async def broadcast_supervisor_event(self, event_data: Dict):
        """Sends real-time updates to all connected clinical supervisor screens."""
        dead_sockets = set()
        for ws in self.supervisor_websockets:
            try:
                await ws.send_json(event_data)
            except Exception:
                dead_sockets.add(ws)
        self.supervisor_websockets.difference_update(dead_sockets)

    def register_supervisor(self, ws: WebSocket):
        self.supervisor_websockets.add(ws)

    def unregister_supervisor(self, ws: WebSocket):
        self.supervisor_websockets.discard(ws)

    def list_active_sessions(self) -> List[Dict]:
        return [sess.to_summary() for sess in self.active_sessions.values()]

    def list_archived_sessions(self) -> List[Dict]:
        return [arch["summary"] for arch in self.archived_sessions.values()]

session_manager = SessionManager()
