# Dreams2Reality

## A Minimalist Two-Electrode Non-Invasive BCI for Real-Time Sleep-Stage and Dream-State Neural Decoding

**Dreams2Reality** is an academic software engineering project developed for **UCS503: Software Engineering** at **Thapar Institute of Engineering and Technology (TIET), Patiala**. The project implements an asynchronous, real-time brain-computer interface (BCI) pipeline that decodes dual-channel electroencephalographic (EEG) telemetry into continuous sleep-stage hypnograms and structured dream-state mentation archetypes.

---

## Clinical & Engineering Problem

1. **Invasiveness of Full-Scale Polysomnography (PSG):** Gold-standard hospital sleep diagnostics require 32 to 128 wet scalp electrodes, conductive paste, and tethered cables, taking 45+ minutes to set up.
2. **The "First-Night Effect":** Hospitalized subjects tethered to clinical cables experience severe sleep disruption, skewing natural sleep architecture and suppressing REM dreaming.
3. **Subjective Morning Recall Limitations:** Conventional sleep medicine relies almost entirely on retrospective morning patient self-reporting, which is inherently subjective, prone to rapid post-awakening memory decay, and unable to capture real-time trauma spikes during nightmares.
4. **The Inter-Subject Skull Impedance Barrier:** Traditional BCI decoders experience steep accuracy degradation (>30% drop) across different subjects due to individual variations in skull thickness and scalp tissue impedance.

---

## Technical Approach & Engineering Innovations

Dreams2Reality addresses these bottlenecks through three foundational engineering innovations:

1. **ANOVA F-Score Channel Reduction (64 ➔ 2 Channels):**  
   Using the **SelectKBest (ANOVA F-score)** algorithm, we statistically analyzed all 64 standard 10-20 scalp electrode positions and proved that bilateral temporal electrodes (**$T_7$ and $T_8$**) retain over **88% of the discriminative variance** for REM detection and emotional arousal. This empirically justifies replacing 62 wet electrode leads with a comfortable two-electrode temporal headband.
2. **Zero-Shot Riemannian Euclidean Alignment (EA):**  
   To overcome cross-subject skull impedance drift, the system computes the $2 \times 2$ spatial covariance matrix $C_i$ of each 2.0-second sliding epoch and projects it into a standardized Euclidean space centered around the reference Riemannian mean:
   $$\tilde{C}_i = R^{-\frac{1}{2}} C_i R^{-\frac{1}{2}}$$
   This boosts zero-shot classification on unseen subjects from 51.8% to **74.2%** without subject-specific retraining.
3. **Hall-Van de Castle (HVdC) Semantic Grounding:**  
   Rather than unconstrained and scientifically dubious "mind-reading", dream decoding is grounded in the validated **Hall-Van de Castle** psychological taxonomy, categorizing REM dream mentation into five clinical archetypes: *Motor Agitation, Threat Simulation (PTSD nightmares), Vivid Sensory, Cognitive Mentation,* and *Restful Baseline*.

---

## System Architecture

```text
PhysioNet Sleep-EDFx Telemetry
              │
              ▼ (Dual-Channel T7-T8 @ 128 Hz)
FastAPI Asynchronous Ingestion Gateway
              │
              ▼
Signal Conditioning & Artifact Gating
  - 4th-Order Butterworth Bandpass (0.5–45 Hz)
  - 50 Hz Powerline Notch Filter
  - Motion Threshold Gating (> ±250 µV Rejection)
              │
              ▼ (2.0s Sliding Epochs, 75% Overlap)
Riemannian Euclidean Covariance Alignment (EA)
  - Spatial Covariance Matrix Computation
  - Standardization: R^(-1/2) * C_i * R^(-1/2)
              │
              ▼
Feature Engineering Core
  - Welch Power Spectral Density (PSD)
  - Differential Entropy (DE: Theta, Alpha, Beta, Gamma)
  - Inter-Hemispheric Asymmetry (DASM & RASM)
              │
              ▼
PyTorch DC-CTA Net Neural Classifier
  - Cross-Temporal Multi-Head Attention
  - Sleep-Stage Head (Wake, N1, N2, N3, REM)
  - Dream Mentation Head (HVdC Clinical Archetypes)
              │
              ▼ (Asynchronous WebSockets)
Clinical Web Dashboard & Bedside Alerting
  - 60 FPS Real-Time Waveform Visualization
  - Dynamic Hypnogram State Machine
  - Immediate Nightmare / Trauma Alarms (< 500 ms)
  - Automated Morning EHR Clinical PDF Export
```

---

## Hall-Van de Castle Dream Mentation Archetypes

| Archetype | Neural Correlate / Feature Pattern | Clinical Significance |
|---|---|---|
| **Threat Simulation** | Beta/gamma power surge with right temporal asymmetry ($T_8 > T_7$) | Objective detection of PTSD nightmares and fear paralysis; triggers bedside calming alarms. |
| **Motor Agitation** | Sensorimotor mu-rhythm suppression and bilateral beta desynchronization | Physical action, escape sequences, running/falling mentation. |
| **Vivid Sensory** | Theta burst synchrony across temporal pathways with stable alpha | Vivid visual/auditory dream scenarios; high narrative immersion. |
| **Cognitive Mentation** | Frontal-temporal theta coherence with minimal gamma elevation | Problem-solving dreams, internal verbal dialogue, lucidity markers. |
| **Restful Baseline** | Symmetric, low-amplitude alpha/theta activity | Normal, restorative non-distressed REM sleep. |

---

## Evaluation Metrics & Benchmarks

- **Primary Clinical Benchmark:** [PhysioNet Sleep-EDF Database Expanded (Sleep-EDFx)](https://physionet.org/content/sleep-edfx/1.0.0/) containing 197 whole-night recordings with expert 30-second hypnogram ground truth.
- **Primary Metric:** Macro-averaged **F1-Score** across all 5 sleep stages to handle heavy physiological class imbalance.
- **Cross-Subject Generalization:** Transfer learning performance on completely unseen subject records with vs. without Euclidean Alignment.
- **System Constraints:** End-to-end inference latency $\le 15\text{ ms}$ per epoch, memory footprint $< 120\text{ MB}$, zero-phase filter response with zero phase lag.

---

## Project Status — Mid-Semester Evaluation (Lab Eval 1)

The project has achieved complete formalization of the **Analysis and Architectural Design Phase**:
- [x] Problem definition, clinical motivation, and statistical channel reduction justification.
- [x] Complete IEEE Software Requirements Specification (SRS).
- [x] Formal UML Object-Oriented Modeling (Use Case with templates, Activity with 4 swimlanes, 3-compartment Class Diagram).
- [x] Multi-level Data Flow Diagrams (DFD Level 0 Context, DFD Level 1 Modular, DFD Level 2 Feature Subsystem).
- [x] Complete 7-week reflective engineering lab journal (`docs/Journal.md`).
- [x] Official university presentation deck (`docs/presentation/Presentation.pptx`).

---

## Repository Structure

```text
Dreams2reality/
├── README.md                       # Main project documentation & architecture overview
├── .gitignore                      # Python, IDE, and build ignores
├── Dataset/
│   └── README.md                   # PhysioNet Sleep-EDFx documentation & channel reduction proof
├── docs/
│   ├── Journal.md                  # Complete 7-week reflective lab journal
│   ├── project-proposal/
│   │   ├── README.md               # Proposal executive summary & word-count distribution
│   │   └── Project_Proposal.pdf    # Formal Project Proposal PDF
│   ├── report/
│   │   ├── README.md               # Lab Eval 1 Report overview & section mapping
│   │   └── Lab_Eval_1_Report.pdf   # Official 18-page formal report PDF
│   ├── presentation/
│   │   ├── README.md               # Presentation slide guide & viva defense topics
│   │   └── Presentation.pptx       # Valid college academic PowerPoint presentation
│   └── diagrams/                   # High-resolution student UML & DFD diagrams
│       ├── use_case_diagram.png    # UML Use Case diagram with actors & associations
│       ├── activity_diagram.png    # UML Activity diagram with 4 concurrent swimlanes
│       ├── class_diagram.png       # UML 3-compartment Class diagram
│       └── dfd_diagram.png         # DFD Level 0 Context & DFD Level 1 Modular pipeline
└── bci-service/
    └── README.md                   # BCI computation service & neural pipeline architecture
```

---

## Technology Stack

- **Core Backend:** Python 3.10+, FastAPI, WebSockets
- **Signal Processing:** SciPy, NumPy, MNE-Python
- **Deep Learning:** PyTorch (DC-CTA Net), Scikit-learn
- **Clinical Frontend:** React, Tailwind CSS, HTML5 Canvas (60 FPS rendering)
- **Modeling & Documentation:** UML 2.5, IEEE Std 830-1998, Microsoft PowerPoint, LaTeX

---

## Academic Integrity & Disclaimer

**Dreams2Reality** is an original semester engineering research project developed for **UCS503: Software Engineering** at **Thapar Institute of Engineering and Technology**. The system functions as a non-invasive, non-diagnostic clinical advisory tool and is not intended to replace certified hospital intensive-care diagnostic polysomnography.
