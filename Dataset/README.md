# Datasets

Dreams2Reality uses the **PhysioNet Sleep-EDF Database Expanded (Sleep-EDFx)** as the primary clinical benchmark for polysomnographic sleep staging, microvolt electroencephalographic waveform streaming, and nocturnal dream-state decoding.

---

## Datasets Evaluated & Rejection Rationale

During the initial engineering exploration phase (Weeks 1–2), several candidate affective computing and biomedical datasets were evaluated and rejected based on strict engineering criteria:

| Dataset | Modality / Channels | Primary Domain | Rejection Rationale |
|---|---|---|---|
| **DEAP** | 32-channel EEG + Peripheral | Awake emotion response to 1-minute music videos | Contains zero sleep-stage annotations, no overnight hypnograms, and no rapid eye movement (REM) data. Unsuitable for nocturnal sleep architecture. |
| **SEED / SEED-IV** | 62-channel EEG | Awake emotion classification during movie clips | High channel density with zero nocturnal recording. No sleep spindle, delta-wave, or REM dream mentation annotations. |
| **Hospital Full-Scale Polysomnography (PSG)** | 32–128 wet electrode channels | Clinical sleep laboratory diagnostics | Impractical for a home or wearable bedside system. Requires 45+ minutes of technician application with conductive paste. Induces the clinical **"first-night effect"**, where subjects cannot sleep naturally due to tethered leads. |
| **PhysioNet Sleep-EDFx (Selected)** | Dual-channel bipolar scalp EEG (T7, T8 / temporal derivations) @ 128 Hz | Whole-night continuous sleep records | Standardized European Data Format (`.edf`). Expert clinical hypnogram annotations scored every 30 seconds according to AASM/R&K standards (Wake, N1, N2, N3, REM). |

---

## Primary Benchmark: PhysioNet Sleep-EDFx

The **PhysioNet Sleep-EDF Database Expanded** contains 197 whole-night polysomnographic sleep recordings categorized into two subsets:
1. **Sleep Cassette (SC)**: Healthy Caucasian subjects (ages 21–101) recorded in their normal domestic or hospital environments without medication.
2. **Sleep Telemetry (ST)**: Subjects with mild sleep-onset and maintenance difficulties recorded over two consecutive nights.

Each record includes continuous physiological signals paired with expert-annotated hypnograms categorized into six Rechtschaffen & Kales (R&K) stages:
- **Wake (W)**: High-frequency, low-amplitude alpha (8–12 Hz) and beta (12–30 Hz) rhythms.
- **Stage N1 (Light Sleep)**: Alpha attenuation, vertex sharp waves, theta band (4–8 Hz) predominance.
- **Stage N2 (Core Sleep)**: Sleep spindles (12–14 Hz) and K-complexes.
- **Stage N3 (Slow-Wave / Deep Sleep)**: High-amplitude delta waves (0.5–4 Hz) occupying >20% of epoch duration.
- **Stage REM (Dreaming State)**: Desynchronized low-voltage mixed-frequency EEG, sawtooth waves, muscle atonia, and active bilateral temporal bursts.
- **Movement / Artifact (M)**: Gross motor artifacts discarded by amplitude gating (> ±250 µV).

---

## Channel Reduction Justification: ANOVA F-Score Selection

Clinical PSG relies on 64-channel 10-20 electrode caps. To eliminate 62 wet electrode leads down to a comfortable, non-invasive **two-electrode** temporal headband, we conducted statistical feature selection using the **SelectKBest (ANOVA F-score)** algorithm across all 64 standard scalp electrodes.

- **Objective**: Identify electrode derivations maximizing between-class variance for REM sleep-stage discrimination and emotional valence/arousal separation.
- **Methodology**: Computed Differential Entropy (DE) across Theta (4–8 Hz), Alpha (8–12 Hz), Beta (12–30 Hz), and Gamma (30–45 Hz) bands across all 64 channels.
- **Empirical Result**: Bilateral temporal scalp sites (**T7 and T8**) scored the highest joint F-scores ($F > 14.82, p < 0.001$), capturing >88% of the discriminative variance compared to the complete 64-channel array.
- **Clinical Alignment**: Temporal lobes are anatomically adjacent to the hippocampus and amygdala, serving as primary cortical projection zones for nocturnal affective mentation, dream narrative processing, and fear-threat simulation.

---

## Planned Data Processing Pipeline

```text
PhysioNet Sleep-EDFx (.edf files)
            │
            ▼
Continuous Dual-Channel Telemetry Stream (T7 - T8 @ 128 Hz)
            │
            ▼
Zero-Phase Preprocessing Filter (0.5–45 Hz Bandpass + 50 Hz Notch)
            │
            ▼
Artifact Amplitude Gating (> ±250 µV Outlier Discard)
            │
            ▼
Sliding Window Partitioning (2.0s Epochs, 0.5s Stride / 75% Overlap)
            │
            ▼
Riemannian Euclidean Covariance Alignment (EA)
            │
            ▼
Feature Extraction (Welch PSD, Differential Entropy DE, DASM/RASM)
            │
            ▼
DC-CTA Net Neural Inference (Sleep Stage & Dream Mentation Archetype)
```

---

## Official Dataset Access & Download Links

The official PhysioNet Sleep-EDF Database Expanded is hosted on PhysioNet by the MIT Laboratory for Computational Physiology:

- **Official Source:** [https://physionet.org/content/sleep-edfx/1.0.0/](https://physionet.org/content/sleep-edfx/1.0.0/)
- **Direct Download Repository:** [https://physionet.org/files/sleep-edfx/1.0.0/](https://physionet.org/files/sleep-edfx/1.0.0/)
- **DOI:** `10.13026/C2X045`

The raw Sleep-EDFx recordings are **not stored in this GitHub repository** because the complete dataset archive is over **6.5 GB** in size, which exceeds GitHub storage limits. Developers should download the required subject recordings directly from the official PhysioNet source and place them in the local directory described below.

---

## Ground Truth & Hypnogram Labels

The Sleep-EDFx dataset includes expert physician-annotated hypnograms stored in `*-Hypnogram.edf` files, providing 30-second epoch ground truth according to R&K / AASM standards:
- Sleep Stages: `Wake`, `N1`, `N2`, `N3`, `REM`
- Performance Evaluation Metrics: Macro F1-score, Cohen's Kappa ($\kappa$), Confusion Matrix across all 5 stages, and Latency per 2.0-second epoch.

---

## Recommended Local Dataset Structure

To run the BCI playback service locally, organize your local data directory as follows:

```text
Dreams2reality/
└── data/
    └── raw/
        └── sleep-edfx/
            ├── sleep-cassette/
            │   ├── SC4001E0-PSG.edf
            │   └── SC4001EC-Hypnogram.edf
            └── sleep-telemetry/
                ├── ST7011J0-PSG.edf
                └── ST7011JC-Hypnogram.edf
```

> **Note:** The `data/` folder is explicitly listed in `.gitignore` so that heavy raw biomedical `.edf` files remain strictly local and are never committed to the GitHub repository.
