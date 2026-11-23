# bci-service/ingestion/edf_streamer.py
import numpy as np
import time
import math
from typing import Generator, Dict, Optional, Tuple
from ingestion.dataset_loader import dataset_loader

class EEGStreamer:
    """
    Asynchronous dual-channel (T7, T8) electroencephalographic telemetry engine.
    Supports TWO modes:
    1. MODE "SIMULATOR": Virtual BCI headband parameterized by user cognitive assessment.
    2. MODE "DATASET": Actual clinical human sleep records streamed from PhysioNet Sleep-EDFx benchmark.
    """

    def __init__(self, sampling_rate: int = 128):
        self.fs = sampling_rate
        self.time_step = 1.0 / self.fs
        self.current_time = 0.0
        self.scenario = "Standard Polysomnography Night"
        self.active_stage = "Wake"
        self.is_playing = True
        self.speed_multiplier = 1.0
        self.inject_nightmare = False
        self.inject_artifact = False

        # Playback Mode
        self.playback_mode = "SIMULATOR" # "SIMULATOR" or "DATASET"
        self.dataset_record_id: Optional[str] = None
        self.dataset_loader = dataset_loader

        # Cognitive Profile Modulators
        self.alpha_bias = 1.0
        self.beta_bias = 1.0
        self.nightmare_susceptibility = 1.0
        self.cognitive_profile: Dict = {}

        # Internal state for smooth stage transitions
        self.stage_duration_sec = 20.0
        self.scenario_timer = 0.0

    def set_dataset_mode(self, record_id: str) -> bool:
        """Switches telemetry stream to real clinical PhysioNet dataset record."""
        success = self.dataset_loader.load_record(record_id)
        if success:
            self.playback_mode = "DATASET"
            self.dataset_record_id = record_id
            self.scenario = f"PhysioNet Sleep-EDFx ({record_id})"
        return success

    def set_simulator_mode(self):
        """Switches telemetry back to the adaptive virtual simulator."""
        self.playback_mode = "SIMULATOR"
        self.scenario = "Standard Polysomnography Night"
        self.dataset_record_id = None

    def apply_cognitive_profile(self, profile: Dict):
        """Calibrates simulated neurodynamics based on real user interactive test results."""
        self.cognitive_profile = profile
        stress = float(profile.get("stress_level", 5)) # 1 - 10
        reaction_jitter = float(profile.get("jitter_ms", 30)) # ms

        # Higher stress/jitter increases Beta (agitation) and decreases Alpha (relaxation)
        self.beta_bias = 0.7 + (stress / 10.0) * 0.9 + min(0.3, reaction_jitter / 100.0)
        self.alpha_bias = max(0.4, 1.4 - (stress / 10.0) * 0.8)

        ptsd_freq = profile.get("ptsd_frequency", "never")
        if ptsd_freq == "frequent":
            self.nightmare_susceptibility = 1.8
        elif ptsd_freq == "rare":
            self.nightmare_susceptibility = 1.2
        else:
            self.nightmare_susceptibility = 0.7

    def set_scenario(self, scenario_name: str):
        self.scenario = scenario_name
        self.scenario_timer = 0.0
        if scenario_name == "Acute PTSD Nightmare Episode":
            self.active_stage = "REM"
            self.inject_nightmare = True
        elif scenario_name == "Movement & Muscle Artifact Test":
            self.inject_artifact = True
        elif scenario_name == "Deep Delta Slow-Wave Rest":
            self.active_stage = "N3"
            self.inject_nightmare = False
        else:
            self.active_stage = "Wake"
            self.inject_nightmare = False

    def trigger_nightmare_spike(self):
        self.active_stage = "REM"
        self.inject_nightmare = True

    def trigger_movement_artifact(self):
        self.inject_artifact = True

    def _update_stage_progression(self, dt: float):
        if self.scenario != "Standard Polysomnography Night":
            return

        self.scenario_timer += dt
        cycle_time = self.scenario_timer % 120.0
        if cycle_time < 20.0:
            self.active_stage = "Wake"
        elif cycle_time < 40.0:
            self.active_stage = "N1"
        elif cycle_time < 65.0:
            self.active_stage = "N2"
        elif cycle_time < 90.0:
            self.active_stage = "N3"
        else:
            self.active_stage = "REM"
            if self.nightmare_susceptibility >= 1.2:
                self.inject_nightmare = (cycle_time > 100.0)
            else:
                self.inject_nightmare = (cycle_time > 112.0)

    def generate_sample(self) -> Tuple[float, float, str, Dict]:
        t = self.current_time
        dt = self.time_step * self.speed_multiplier
        self.current_time += dt
        self._update_stage_progression(dt)

        stage = self.active_stage
        t7 = 0.0
        t8 = 0.0

        noise_t7 = np.random.normal(0, 3.5)
        noise_t8 = np.random.normal(0, 3.5)
        hum_50hz = 4.0 * math.sin(2 * math.pi * 50.0 * t)

        if stage == "Wake":
            alpha = (25.0 * self.alpha_bias) * math.sin(2 * math.pi * 10.0 * t)
            beta = (10.0 * self.beta_bias) * math.sin(2 * math.pi * 18.0 * t)
            t7 = alpha + beta + noise_t7
            t8 = alpha * 0.95 + beta + noise_t8

        elif stage == "N1":
            theta = 35.0 * math.sin(2 * math.pi * 5.5 * t)
            vertex_sharp = 40.0 * math.exp(-((t % 4.0 - 2.0) ** 2) / 0.02) if (t % 4.0 < 2.2) else 0.0
            t7 = theta + vertex_sharp + noise_t7
            t8 = theta * 1.05 + vertex_sharp + noise_t8

        elif stage == "N2":
            spindle_active = (t % 5.0) < 0.8
            spindle = 35.0 * math.sin(2 * math.pi * 13.0 * t) if spindle_active else 0.0
            k_active = (t % 8.0) < 0.5
            k_complex = -90.0 * math.sin(2 * math.pi * 1.5 * (t % 8.0)) if k_active else 0.0
            theta_bg = 20.0 * math.sin(2 * math.pi * 6.0 * t)
            t7 = spindle + k_complex + theta_bg + noise_t7
            t8 = spindle * 0.9 + k_complex + theta_bg + noise_t8

        elif stage == "N3":
            delta_1 = 85.0 * math.sin(2 * math.pi * 1.2 * t)
            delta_2 = 45.0 * math.sin(2 * math.pi * 0.8 * t + 0.4)
            t7 = delta_1 + delta_2 + noise_t7
            t8 = delta_1 * 1.02 + delta_2 * 0.98 + noise_t8

        elif stage == "REM":
            sawtooth = 22.0 * (2.0 * ((t * 4.0) % 1.0) - 1.0)
            theta_burst = 25.0 * math.sin(2 * math.pi * 6.5 * t)
            beta_burst = 12.0 * math.sin(2 * math.pi * 24.0 * t)

            if self.inject_nightmare:
                gamma_amp = 28.0 * self.nightmare_susceptibility
                beta_amp = 35.0 * self.nightmare_susceptibility
                nightmare_gamma = gamma_amp * math.sin(2 * math.pi * 38.0 * t)
                nightmare_beta = beta_amp * math.sin(2 * math.pi * 26.0 * t)
                t7 = sawtooth * 0.8 + theta_burst + beta_burst + noise_t7
                t8 = sawtooth * 1.3 + theta_burst * 1.5 + nightmare_beta + nightmare_gamma + noise_t8
            else:
                t7 = sawtooth + theta_burst + beta_burst + noise_t7
                t8 = sawtooth * 0.95 + theta_burst * 1.05 + beta_burst + noise_t8

        t7 += hum_50hz
        t8 += hum_50hz

        if self.inject_artifact:
            artifact_spike = 380.0 * math.sin(2 * math.pi * 2.0 * t)
            t7 += artifact_spike
            t8 += artifact_spike
            if (self.current_time % 1.0) > 0.8:
                self.inject_artifact = False

        meta = {
            "timestamp": t,
            "scenario": self.scenario,
            "nightmare_active": self.inject_nightmare,
            "artifact_active": self.inject_artifact,
            "calibrated_profile": bool(self.cognitive_profile),
            "playback_mode": self.playback_mode
        }

        return float(t7), float(t8), stage, meta

    def generate_chunk(self, num_samples: int = 64) -> Tuple[np.ndarray, str, Dict]:
        """
        Generates batch of samples either from clinical dataset record or adaptive simulator.
        """
        if self.playback_mode == "DATASET" and self.dataset_record_id:
            chunk, gt_stage, meta = self.dataset_loader.get_next_samples(num_samples)
            self.active_stage = gt_stage
            meta["playback_mode"] = "DATASET"
            return chunk, gt_stage, meta

        # Fallback to simulator
        t7_list = []
        t8_list = []
        last_stage = self.active_stage
        last_meta = {}

        for _ in range(num_samples):
            v7, v8, stage, meta = self.generate_sample()
            t7_list.append(v7)
            t8_list.append(v8)
            last_stage = stage
            last_meta = meta

        chunk = np.array([t7_list, t8_list], dtype=np.float32)
        return chunk, last_stage, last_meta
