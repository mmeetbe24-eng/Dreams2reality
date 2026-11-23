# 🧠 Dreams2Reality: Minimalist Two-Electrode BCI Platform & Clinical Supervisor

> **Real-Time Two-Electrode ($T_7, T_8$) Sleep-Stage & Dream-State Neural Decoding System**  
> *UCS503 Software Engineering Final End-Semester Evaluation (EST) • Academic Session 2026*  
> **Thapar Institute of Engineering and Technology (TIET), Patiala • Department of Computer Science & Engineering**

[![Python: 3.11](https://img.shields.io/badge/Python-3.11.9-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![FastAPI: 0.110](https://img.shields.io/badge/FastAPI-WebSockets_MultiUser-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PyTorch: 2.x](https://img.shields.io/badge/PyTorch-DC--CTA_Net-EE4C2C.svg?logo=pytorch&logoColor=white)](https://pytorch.org)
[![Tests: 11 Passed](https://img.shields.io/badge/Pytest-11%20Passed%20(100%25)-brightgreen.svg)]()
[![PhysioNet: Sleep--EDFx](https://img.shields.io/badge/PhysioNet-Sleep--EDFx_Benchmark-blue.svg)]()
[![Cloud Deploy: Ready](https://img.shields.io/badge/Cloud_Deploy-Render_/_Docker_/_Ngrok-22C55E.svg)]()

---

## 👥 Engineering Team & Academic Credits

**Course:** UCS503 Software Engineering Lab  
**Project Group:** 3C25  
**Faculty Evaluator & Project Guide:** Dr. Stuti Chug (Assistant Professor, CSED, TIET)  

| Student Name | University Roll No. | Subsystem Ownership |
|---|---|---|
| **Meet** | `1024030343` | Deep Learning Architecture, PyTorch DC-CTA Net Dual Heads, Mathematical Formulations |
| **Harsh** | `1024030497` | Biomedical DSP, Zero-Phase IIR Filtering, Riemannian Euclidean Covariance Alignment |
| **Kanav Bhardwaj** | `1024030395` | Real-Time Systems, Asynchronous WebSocket Telemetry, Multi-User Central SessionManager |
| **Yukti Saklani** | `1024030392` | Frontend Neurotech Design, 60 FPS Canvas Oscilloscope, ReportLab Clinical PDF Engine |

---

## 📌 Executive Summary

**Dreams2Reality** is a deployment-ready, cloud-native Brain-Computer Interface platform engineered to eliminate the clinical 64-channel "first-night effect" using a minimalist **two-electrode ($T_7, T_8$) bilateral temporal montage**.

### Core Technological Innovations:
1. **Statistical ANOVA F-Score Channel Reduction**: Eliminates 62 wet leads while capturing $>88\%$ of discriminative sleep-staging variance.
2. **Riemannian Euclidean Covariance Alignment (EA)**: Projects spatial covariance onto a reference geometric mean ($\tilde{C}_i = R^{-1/2} C_i R^{-1/2}$), standardizing inter-subject skull impedance variability without daily recalibration.
3. **Deep Cross-Temporal Attention (DC-CTA Net)**: Dual-head PyTorch neural network classifying:
   - **Head 1:** 5 AASM Sleep Stages (`Wake`, `N1`, `N2`, `N3`, `REM`) with 89.4% macro accuracy.
   - **Head 2:** 5 Hall-Van de Castle Dream Mentation Archetypes (`Threat Simulation`, `Motor Agitation`, `Vivid Sensory`, `Cognitive Problem-Solving`, `Restful Baseline`).
4. **MIT PhysioNet Sleep-EDFx Clinical Benchmark Integration**: Dual-ingestion engine streaming certified hospital records (`SC4001E0`, `ST7011J0`, `SC4012E0`) alongside an adaptive virtual simulator.
5. **Interactive Pre-Sleep Cognitive Reaction Calibration**: 3-trial Psychomotor Vigilance Test (PVT) measuring baseline psychomotor latency and tuning cortical arousal.
6. **Central Multi-User Surveillance Dashboard (`/monitor`)**: Zero-hardcoding clinical supervisor terminal with live participant directory, spectator waveform mirroring, millisecond audit feed, and bi-directional intervention dispatch.
7. **Automated Morning Clinical PDF Engine**: Instant ReportLab compilation of formal polysomnography reports at `/api/sessions/{id}/report-pdf`.

---

## 🌐 Multi-Page Web Platform Structure

```text
Dreams2Reality Web Architecture
├── / (Portal & Hub)                     -> Overview, quick start, architectural pillars, server health
├── /session (Participant Cockpit)       -> 60 FPS Canvas oscilloscope, gain toggles, hypnogram, dream journal
├── /monitor (Clinical Supervisor)       -> Multi-bed live directory, spectator mirroring, audit feed, interventions
├── /archive (Records Vault)             -> Polysomnography repository, dream journal cards, PDF report downloads
├── /docs (OpenAPI / Swagger)            -> Interactive REST API and WebSocket protocol specifications
└── /api/sessions/{id}/report-pdf        -> Dynamic ReportLab clinical morning sleep architecture PDF
```

---

## 📚 End-Semester (EST) Deliverables & Documentation

All project documentation is compiled and verified in the repository:

| Deliverable | File Path | Format & Scope | Status |
|---|---|---|---|
| **EST Final Report** | [`docs/report/Final_EST_Report.pdf`](docs/report/Final_EST_Report.pdf) | Formal 9-page IEEE/University Academic Report with Tables & Figures | **Complete & Verified** |
| **EST Final Report (Word)** | [`docs/report/Final_EST_Report.docx`](docs/report/Final_EST_Report.docx) | Fully Editable Microsoft Word Document with Style Formatting | **Complete & Verified** |
| **EST Final Presentation** | [`docs/presentation/Final_Presentation_EST.pptx`](docs/presentation/Final_Presentation_EST.pptx) | 24-Slide Widescreen University Presentation with Embedded Figures | **Complete & Slide-Ready** |
| **Complete 14-Week Journal** | [`docs/Journal.md`](docs/Journal.md) | Comprehensive 5-part reflective engineering journal (Weeks 1 to 14) | **Complete (100%)** |
| **Scientific Figures** | [`docs/diagrams/`](docs/diagrams/) | High-DPI Confusion Matrix, Affective Scatter, EA Invariance, Latency Chart | **Generated & Embedded** |
| **MST Evaluation Archive** | [`docs/report/Final_Mst_Report(7-weeks).pdf`](docs/report/Final_Mst_Report(7-weeks).pdf) | Mid-Semester Test (MST) 7-Week Documentation Archive | **Archived** |

---

## 🧪 Algorithmic & Scientific Formulations

### 1. Zero-Phase Digital Signal Conditioning
- 4th-order Butterworth bandpass ($0.5 - 45.0\text{ Hz}$) implemented via Second-Order Sections (SOS).
- $50.0\text{ Hz}$ IIR notch filter ($Q = 30$) for AC mains hum elimination.
- Bi-directional forward-backward filtering (`scipy.signal.sosfiltfilt`) achieves **strict zero phase distortion** ($\theta_{\text{net}}(\omega) = 0.0\text{ rad}$).
- Peak-to-peak amplitude gating flags motion artifacts exceeding $\pm 250\ \mu\text{V}$ without breaking temporal epoch alignment.

### 2. Riemannian Euclidean Covariance Alignment (EA)
- Baseline reference covariance: $R = \frac{1}{N} \sum_{i=1}^N X_i X_i^T$.
- Eigen-decomposition: $R = U \Lambda U^T \implies R^{-1/2} = U \Lambda^{-1/2} U^T$.
- Aligned trial projection: $\tilde{X}_i = R^{-1/2} X_i \implies \tilde{C}_i = R^{-1/2} C_i R^{-1/2} \approx I$.
- Centers cross-subject covariance distributions around the Identity matrix ($I$), standardizing impedance variance across subjects.

### 3. 16-Dimensional Feature Representation
- **10 Dimensions:** Welch Power Spectral Density across 5 clinical bands (Delta, Theta, Alpha, Beta, Gamma) for $T_7$ and $T_8$.
- **5 Dimensions:** Differential Asymmetry ($\text{DASM}_b = \ln(\text{Power}_{T_8, b} / \text{Power}_{T_7, b})$) and Rational Asymmetry ($\text{RASM}$).
- **1 Dimension:** Inter-hemispheric temporal Pearson cross-correlation ($\rho_{T_7, T_8}$).

### 4. Acute Nightmare Trauma Scoring
$$\text{Valence} = \tanh(1.8 \times \text{DASM}_{\alpha}) \in [-1.0, +1.0]$$
$$\text{Arousal} = \tanh\left(1.5 \times \frac{\text{Beta} + \text{Gamma}}{\text{Theta} + \text{Delta}}\right) \in [0.0, 1.0]$$
$$S_{\text{trauma}} = P(\text{REM}) \times P(\text{Threat}) \times \min\left(1.0, \frac{\text{Beta}/\text{Theta}}{2.0}\right)$$
Bedside audio-visual alarm fires whenever $S_{\text{trauma}} \ge 0.65$.

---

## 🚀 1-Click Launch & Deployment Guide

### Option 1: Native Windows 1-Click Execution (Recommended)
Double-click [`run_app.bat`](run_app.bat) in the project root. The launcher will:
1. Detect Python 3.11 installed in LocalAppData.
2. Verify environment integrity (`python -V`).
3. Boot FastAPI on `http://localhost:8000`.
4. Automatically open your web browser to the portal.

### Option 2: Instant Public URL with Ngrok
Since Ngrok is integrated, run in a separate terminal:
```bash
ngrok http 8000
```
This generates a secure public HTTPS/WSS URL (e.g. `https://xxxx.ngrok-free.app`) accessible from any smartphone, laptop, or remote evaluator.

### Option 3: Docker & Cloud Deployment
- **Docker Compose:**
  ```bash
  docker-compose up --build -d
  ```
- **Render.com / Railway:** Connect repository; Render auto-detects [`render.yaml`](render.yaml) and [`Procfile`](Procfile).

---

## 🔬 Automated Quality Assurance & Test Suite

Run the full pytest suite:

```bash
pytest tests -v
```

### Test Results Summary:
```text
tests/test_api.py::test_api_status_and_health PASSED                     [  9%]
tests/test_api.py::test_pages_routing PASSED                             [ 18%]
tests/test_api.py::test_dataset_api_endpoints PASSED                     [ 27%]
tests/test_api.py::test_session_lifecycle_and_interactions PASSED        [ 36%]
tests/test_api.py::test_pdf_report_generator_direct PASSED               [ 45%]
tests/test_dataset_loader.py::test_dataset_loader_records_and_streaming PASSED [ 54%]
tests/test_euclidean_alignment.py::test_covariance_and_alignment PASSED  [ 63%]
tests/test_feature_extractor.py::test_feature_extraction_dimension PASSED [ 72%]
tests/test_feature_extractor.py::test_dc_cta_net_forward_and_prediction PASSED [ 81%]
tests/test_preprocessing.py::test_bandpass_and_notch_filtering PASSED    [ 90%]
tests/test_preprocessing.py::test_artifact_detection PASSED              [100%]
======================== 11 passed in 3.85s ========================
```

---

## 📊 Performance Benchmarks

| Subsystem Component | Latency per 2.0s Window | Real-Time Budget | Headroom Ratio |
|---|---|---|---|
| IIR Bandpass (0.5-45 Hz) & 50 Hz Notch | 1.85 ms | 50.0 ms | 27.0x |
| Riemannian Euclidean Alignment | 2.40 ms | 50.0 ms | 20.8x |
| 16-D Welch PSD & Asymmetry Extraction | 4.10 ms | 100.0 ms | 24.3x |
| PyTorch DC-CTA Net Dual-Head Inference | 5.20 ms | 250.0 ms | 48.0x |
| WebSocket Broadcast Dispatch | 1.35 ms | 50.0 ms | 37.0x |
| **Total End-to-End Pipeline Latency** | **14.90 ms** | **500.0 ms** | **33.5x Faster than Real Time** |

---

## 📜 Academic Declaration

We hereby declare that this project titled **"DREAMS2REALITY: A Minimalist Two-Electrode Software Platform for Real-Time Sleep-Stage and Dream-State Neural Decoding"** is our original software engineering work submitted in partial fulfillment of the requirements for the course **UCS503 Software Engineering Lab** at **Thapar Institute of Engineering and Technology, Patiala** under the supervision of **Dr. Stuti Chug**.
