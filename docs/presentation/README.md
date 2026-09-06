# Mid-Semester Evaluation Presentation

This directory contains the official **PowerPoint Presentation (`Presentation.pptx`)** for the UCS503 Mid-Semester Evaluation (Lab Eval 1) at Thapar Institute of Engineering and Technology, Patiala.

---

## Presentation Highlights

- **File Name:** [`Presentation.pptx`](Presentation.pptx)
- **Slide Count:** **9 Slides** (strictly focused on mid-term evaluation scope)
- **Format:** Native Microsoft PowerPoint (`.pptx`)
- **Design Template:** Authentic academic college style featuring a clean white background, institutional Thapar Navy (`#002B49`) headers, and warm Amber/Orange (`#E87722`) accents. Avoids flashy, auto-generated AI templates.
- **Embedded Student Diagrams:** High-resolution Draw.io / StarUML line-art style diagrams embedded directly onto the respective slides:
  - *Slide 5:* UML Use Case Diagram
  - *Slide 6:* UML Activity Diagram (with 4 Swimlanes)
  - *Slide 7:* UML Object-Oriented Class Diagram
  - *Slide 8:* Data Flow Diagrams (DFD Level 0 & DFD Level 1)
- **Whiteboard Checklist Compliance:** 100% compliant with all items specified by the faculty evaluator (`things required in ppt.png`).

---

## Slide Structure (9 Slides)

1. **Slide 1: Title & Specimen Header** — Project title, B.E. COE third-year student details, supervisor info, department banner.
2. **Slide 2: Clinical Context & Problem Statement** — Sleep disorder prevalence, 64-channel PSG invasiveness, first-night effect, and morning recall limitations.
3. **Slide 3: SDLC Process Model (Whiteboard Item 5)** — Agile/Scrum justification, iterative signal filtering sprints, 15-week academic roadmap.
4. **Slide 4: System Architecture & Flow Pipeline** — Ingestion, Preprocessing, ML Engine, and Clinical UI decoupled layers.
5. **Slide 5: UML Use Case Diagram (Whiteboard Item 1)** — Primary actors, system boundary, `<<include>>` and `<<extend>>` relationships.
6. **Slide 6: UML Activity Diagram (Whiteboard Item 2)** — 4 execution swimlanes (Streamer, Preprocessor, ML Engine, Clinical UI).
7. **Slide 7: UML Class Diagram (Whiteboard Item 3)** — 3-compartment OO classes (`EEGStreamer`, `SignalPreprocessor`, `FeatureExtractor`, `EuclideanAligner`, `DCTANetClassifier`, `DreamState`, `TelemetryController`).
8. **Slide 8: Data Flow Diagrams (Whiteboard Item 4)** — DFD Level 0 Context and DFD Level 1 Modular decomposition with data stores D1–D4.
9. **Slide 9: Algorithmic Core: Channel Reduction & Alignment** — ANOVA F-score ranking (SelectKBest) justifying $T_7, T_8$ selection, and Riemannian Euclidean Covariance Alignment ($\tilde{C}_i = R^{-1/2} C_i R^{-1/2}$).

---

## Attached File

- [`Presentation.pptx`](Presentation.pptx) — Open directly in Microsoft PowerPoint for presentation.
