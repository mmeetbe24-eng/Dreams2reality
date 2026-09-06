# BCI Service — Computational Backend & Neural Engine

This directory defines the modular architecture for the **Dreams2Reality BCI Service**, responsible for asynchronous electroencephalographic telemetry playback, digital signal conditioning, Riemannian covariance standardization, and deep neural inference.

---

## Architectural Organization

```text
bci-service/
├── ingestion/              # Asynchronous telemetry streaming from PhysioNet Sleep-EDFx
├── preprocessing/          # Zero-phase Butterworth IIR bandpass & 50 Hz notch filtering
├── alignment/              # Riemannian geometry & Euclidean Covariance Alignment (EA)
├── features/               # Welch PSD, Differential Entropy (DE), and DASM/RASM computation
├── models/                 # PyTorch DC-CTA Net (Dual-Channel Cross-Temporal Attention Network)
├── inference/              # Sliding-window real-time inference worker (500 ms cycle)
└── api/                    # FastAPI WebSocket server and clinical alert endpoints
```

---

## Core Pipeline Components

### 1. Telemetry Ingestion (`ingestion/`)
- Simulates real-time clinical data acquisition by reading calibrated European Data Format (`.edf`) recordings from PhysioNet Sleep-EDFx.
- Emits continuous dual-channel microvolt signals ($T_7, T_8$) at a calibrated sampling frequency of $128\text{ Hz}$.

### 2. Digital Signal Conditioning (`preprocessing/`)
- Implements a 4th-order zero-phase Butterworth IIR bandpass filter ($0.5\text{--}45\text{ Hz}$) to remove DC electrode drift and muscle tremor.
- Implements a $50\text{ Hz}$ IIR powerline notch filter.
- Applies hard amplitude threshold gating ($> \pm 250\ \mu\text{V}$) to isolate gross motor artifacts and prevent false nightmare alarms.

### 3. Riemannian Euclidean Alignment (`alignment/`)
- Standardizes spatial covariance across subjects to solve the skull bone impedance drift problem.
- Computes epoch covariance:
  $$C_i = \frac{1}{N-1} X_i X_i^T \in \mathbb{R}^{2 \times 2}$$
- Projects onto the reference Riemannian mean:
  $$\tilde{C}_i = R^{-\frac{1}{2}} C_i R^{-\frac{1}{2}}$$

### 4. Neural Classification Engine (`models/`)
- **DC-CTA Net (Dual-Channel Cross-Temporal Attention Network)**:
  - Takes 16-dimensional Differential Entropy vectors across sliding 2.0-second epochs.
  - Multi-head self-attention models temporal transitions across successive epochs.
  - Dual classification heads:
    1. *Sleep-Stage Head*: Outputs posterior probabilities for Wake, N1, N2, N3, and REM.
    2. *Dream Mentation Head*: Activated during REM to categorize neural dynamics into Hall-Van de Castle archetypes: *Motor Agitation, Threat Simulation, Vivid Sensory, Cognitive Mentation, Restful Baseline*.

### 5. API & Telemetry Gateway (`api/`)
- Built on FastAPI with asynchronous WebSockets.
- Dispatches 60 FPS live microvolt waveform coordinates, updated hypnogram states, and immediate trauma alerts to the clinical web interface.
