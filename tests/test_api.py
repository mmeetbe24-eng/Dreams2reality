# tests/test_api.py
import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bci-service"))

from api.server import app
from api.session_manager import session_manager
from api.pdf_report import generate_clinical_pdf

client = TestClient(app)

def test_api_status_and_health():
    res_h = client.get("/healthz")
    assert res_h.status_code == 200
    assert res_h.json()["status"] == "healthy"

    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert data["cloud_deployment_ready"] is True
    assert data["bci_channels"] == ["T7", "T8"]
    assert "dataset_benchmark" in data

def test_pages_routing():
    res_home = client.get("/")
    assert res_home.status_code == 200
    assert "Dreams2Reality" in res_home.text

    res_session = client.get("/session")
    assert res_session.status_code == 200
    assert "Participant" in res_session.text

    res_mon = client.get("/monitor")
    assert res_mon.status_code == 200
    assert "Supervisor" in res_mon.text

    res_arch = client.get("/archive")
    assert res_arch.status_code == 200
    assert "Archive" in res_arch.text

def test_dataset_api_endpoints():
    res_ds = client.get("/api/dataset/records")
    assert res_ds.status_code == 200
    data = res_ds.json()
    assert len(data["records"]) >= 3
    rec_ids = [r["record_id"] for r in data["records"]]
    assert "SC4001E0" in rec_ids

def test_session_lifecycle_and_interactions():
    sess = session_manager.get_or_create_session("TEST-USER-01", "Dr. Miller", "192.168.1.10", "TestRunner")
    assert sess.session_id == "TEST-USER-01"
    assert sess.user_name == "Dr. Miller"

    # Test loading real PhysioNet dataset record into session
    res_load_ds = client.post("/api/sessions/TEST-USER-01/dataset/load", json={
        "record_id": "SC4001E0"
    })
    assert res_load_ds.status_code == 200
    assert res_load_ds.json()["playback_mode"] == "DATASET"
    assert sess.worker.streamer.playback_mode == "DATASET"

    # Test switching back to simulator
    res_mode = client.post("/api/sessions/TEST-USER-01/dataset/mode?mode=SIMULATOR")
    assert res_mode.status_code == 200
    assert sess.worker.streamer.playback_mode == "SIMULATOR"

    # Test user control endpoint
    res_ctrl = client.post("/api/sessions/TEST-USER-01/control", json={
        "action": "SET_SCENARIO",
        "scenario": "Acute PTSD Nightmare Episode"
    })
    assert res_ctrl.status_code == 200
    assert res_ctrl.json()["status"] == "success"

    # Test cognitive assessment calibration endpoint
    res_assess = client.post("/api/sessions/TEST-USER-01/assessment", json={
        "stress_level": 8,
        "ptsd_frequency": "frequent",
        "pre_sleep_state": "agitated",
        "reaction_time_ms": 285.5,
        "jitter_ms": 32.0
    })
    assert res_assess.status_code == 200
    assert res_assess.json()["status"] == "calibrated"
    assert sess.worker.streamer.beta_bias > 1.0

    # Test subjective dream journal submission
    res_journal = client.post("/api/sessions/TEST-USER-01/journal", json={
        "text": "Felt an intense sensation of falling into an endless tunnel",
        "valence": -0.6,
        "arousal": 0.85
    })
    assert res_journal.status_code == 200
    assert res_journal.json()["journal"]["user_valence"] == -0.6

    # Test supervisor clinical message to user
    res_msg = client.post("/api/sessions/TEST-USER-01/message", json={
        "message": "Adjust headband position slightly forward",
        "level": "urgent"
    })
    assert res_msg.status_code == 200
    assert res_msg.json()["status"] == "delivered"

    # Test PDF generation for this specific user (with assessment included)
    res_pdf = client.get("/api/sessions/TEST-USER-01/report-pdf")
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"
    assert res_pdf.content.startswith(b"%PDF")

    # Clean up test session
    session_manager.remove_session("TEST-USER-01")

def test_pdf_report_generator_direct():
    dummy_report_data = {
        "session_duration_sec": 3600,
        "total_epochs": 120,
        "sleep_efficiency": 88.5,
        "stage_distribution": {
            "Wake": 10.0,
            "N1": 5.0,
            "N2": 50.0,
            "N3": 20.0,
            "REM": 15.0
        },
        "dream_archetype_distribution": {
            "Restful Baseline": 10,
            "Threat Simulation": 2
        },
        "trauma_events": [
            {
                "timestamp": 1240.5,
                "stage": "REM",
                "archetype": "Threat Simulation",
                "threat_probability": 0.85,
                "severity": 0.82
            }
        ]
    }
    dummy_assessment = {
        "stress_level": 7,
        "reaction_time_ms": 290.0,
        "jitter_ms": 25.0,
        "ptsd_frequency": "rare"
    }
    pdf_bytes = generate_clinical_pdf(dummy_report_data, patient_name="Test Subject", assessment=dummy_assessment)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")
