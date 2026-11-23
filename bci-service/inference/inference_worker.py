# bci-service/inference/inference_worker.py
import numpy as np
import time
from typing import Dict, List, Optional, Callable
from collections import deque

from ingestion.edf_streamer import EEGStreamer
from preprocessing.filters import SignalPreprocessor
from alignment.euclidean_aligner import EuclideanAligner
from features.feature_extractor import FeatureExtractor
from models.dc_cta_net import DCTANetClassifier

class InferenceWorker:
    """
    Coordinates real-time clinical BCI pipeline:
    Streamer -> Preprocessor -> Euclidean Aligner -> Feature Extractor -> DC-CTA Net
    Maintains overnight hypnogram logs and telemetry broadcast ring buffers.
    """

    def __init__(self, sampling_rate: int = 128):
        self.fs = sampling_rate
        self.streamer = EEGStreamer(sampling_rate=self.fs)
        self.preprocessor = SignalPreprocessor(sampling_rate=self.fs)
        self.aligner = EuclideanAligner()
        self.extractor = FeatureExtractor(sampling_rate=self.fs)
        self.classifier = DCTANetClassifier()

        # Buffer for continuous streaming (stores 2.0s = 256 samples for sliding analysis)
        self.window_size = int(2.0 * self.fs) # 256 samples
        self.stride_size = int(0.5 * self.fs) # 64 samples = 500 ms cycle
        self.raw_buffer_t7 = deque(maxlen=self.window_size)
        self.raw_buffer_t8 = deque(maxlen=self.window_size)

        # Ring buffer for UI live waveform rendering (last 512 samples ~ 4 seconds)
        self.live_waveform_t7 = deque(maxlen=512)
        self.live_waveform_t8 = deque(maxlen=512)

        # Calibrate aligner with synthetic baseline epochs
        self._init_calibration()

        # Session tracking
        self.session_start_time = time.time()
        self.hypnogram_history: List[Dict] = []
        self.trauma_alerts: List[Dict] = []
        self.current_state = {
            "stage": "Wake",
            "dream_archetype": "Restful Baseline",
            "trauma_alert": False,
            "trauma_severity": 0.0,
            "valence": 0.0,
            "arousal": 0.2,
            "artifact_detected": False,
            "t7_uv": 0.0,
            "t8_uv": 0.0
        }

    def _init_calibration(self):
        """Initializes Euclidean Aligner with baseline synthetic reference epochs."""
        dummy_epochs = []
        for _ in range(10):
            ep, _, _ = self.streamer.generate_chunk(self.window_size)
            dummy_epochs.append(ep)
        self.aligner.calibrate(dummy_epochs)

    def step(self, num_samples: int = 16) -> Dict:
        """
        Executes a pipeline step by ingesting new samples, running digital filtering,
        evaluating sliding window epochs when ready, and returning packet payload.
        """
        chunk, gt_stage, meta = self.streamer.generate_chunk(num_samples)
        
        # Add to live buffers
        for i in range(num_samples):
            v7 = float(chunk[0, i])
            v8 = float(chunk[1, i])
            self.raw_buffer_t7.append(v7)
            self.raw_buffer_t8.append(v8)
            self.live_waveform_t7.append(v7)
            self.live_waveform_t8.append(v8)

        self.current_state["t7_uv"] = float(chunk[0, -1])
        self.current_state["t8_uv"] = float(chunk[1, -1])

        inference_event = None

        # Check if full 2.0s epoch is ready for sliding window evaluation
        if len(self.raw_buffer_t7) >= self.window_size:
            raw_epoch = np.array([list(self.raw_buffer_t7), list(self.raw_buffer_t8)], dtype=np.float32)

            # 1. Digital Filter Conditioning
            filtered_epoch = self.preprocessor.preprocess_stream(raw_epoch)

            # 2. Artifact Gating
            is_artifact, max_amp = self.preprocessor.detect_artifact(filtered_epoch)
            self.current_state["artifact_detected"] = is_artifact

            if not is_artifact:
                # 3. Euclidean Covariance Alignment
                aligned_epoch = self.aligner.transform(filtered_epoch)

                # 4. Feature Extraction (16-D vector)
                feat_16d, stats = self.extractor.extract_features(aligned_epoch)

                # 5. Neural Classification (DC-CTA Net)
                pred = self.classifier.predict_epoch(feat_16d)

                # Update current state
                self.current_state["stage"] = pred["stage"]
                self.current_state["dream_archetype"] = pred["dream_archetype"]
                self.current_state["valence"] = pred["valence"]
                self.current_state["arousal"] = pred["arousal"]
                self.current_state["trauma_alert"] = pred["trauma_alert"]
                self.current_state["trauma_severity"] = pred["trauma_severity"]

                now = time.time()
                time_offset = now - self.session_start_time

                hypno_entry = {
                    "time": round(time_offset, 1),
                    "stage": pred["stage"],
                    "dream_archetype": pred["dream_archetype"],
                    "threat_sim_prob": round(pred["threat_sim_prob"], 3),
                    "arousal": round(pred["arousal"], 3),
                    "valence": round(pred["valence"], 3)
                }
                self.hypnogram_history.append(hypno_entry)

                if pred["trauma_alert"]:
                    alert_entry = {
                        "timestamp": round(time_offset, 1),
                        "stage": pred["stage"],
                        "archetype": pred["dream_archetype"],
                        "threat_probability": round(pred["threat_sim_prob"], 2),
                        "severity": round(pred["trauma_severity"], 2),
                        "message": "ACUTE TRAUMA / NIGHTMARE EPISODE DETECTED"
                    }
                    self.trauma_alerts.append(alert_entry)

                inference_event = {
                    "prediction": pred,
                    "stats": stats,
                    "hypnogram_entry": hypno_entry
                }

        packet = {
            "type": "telemetry",
            "timestamp": time.time(),
            "t7": self.current_state["t7_uv"],
            "t8": self.current_state["t8_uv"],
            "state": self.current_state,
            "inference": inference_event,
            "recent_wave_t7": list(self.live_waveform_t7)[-64:],
            "recent_wave_t8": list(self.live_waveform_t8)[-64:],
            "scenario": self.streamer.scenario
        }

        return packet

    def get_summary_report_data(self) -> Dict:
        """Computes summary statistics for morning clinical report."""
        total_epochs = len(self.hypnogram_history)
        if total_epochs == 0:
            return {"error": "No data recorded yet"}

        stages_count = {"Wake": 0, "N1": 0, "N2": 0, "N3": 0, "REM": 0}
        archetypes_count = {}

        for h in self.hypnogram_history:
            st = h.get("stage", "Wake")
            stages_count[st] = stages_count.get(st, 0) + 1
            at = h.get("dream_archetype", "Restful Baseline")
            archetypes_count[at] = archetypes_count.get(at, 0) + 1

        stage_pct = {k: round((v / total_epochs) * 100, 1) for k, v in stages_count.items()}
        sleep_epochs = total_epochs - stages_count.get("Wake", 0)
        sleep_efficiency = round((sleep_epochs / total_epochs) * 100, 1)

        return {
            "session_duration_sec": round(time.time() - self.session_start_time, 1),
            "total_epochs": total_epochs,
            "sleep_efficiency": sleep_efficiency,
            "stage_distribution": stage_pct,
            "dream_archetype_distribution": archetypes_count,
            "trauma_alerts_count": len(self.trauma_alerts),
            "trauma_events": self.trauma_alerts[-10:] # last 10
        }
