# Lab Evaluation 1 Formal Report

This directory contains the comprehensive **Mid-Semester Lab Evaluation 1 Report** for **Dreams2Reality** submitted for UCS503: Software Engineering at Thapar Institute of Engineering and Technology, Patiala.

---

## Access the Report

* 📖 **[View Full Report Online (Markdown Version)](Lab_Eval_1_Report.md)** — Opens and renders natively inside GitHub with all sections, tables, IEEE SRS, and user stories.
* 📥 **[Download Official Evaluation PDF](Lab_Eval_1_Report.pdf)** — 21-page formal report for MST lab evaluation.

> **Note on GitHub PDF Viewer:** GitHub's in-browser previewer often displays *"Unable to render code block"* on multi-page PDF documents. To view the PDF, click the **Download** button at the top right, or read the full report directly online via [`Lab_Eval_1_Report.md`](Lab_Eval_1_Report.md).

---

## Document Details

- **Title:** UCS503 Software Engineering — Mid-Semester Lab Evaluation 1 Report
- **Project:** Dreams2Reality: A Minimalist Two-Electrode Non-Invasive BCI for Real-Time Sleep-Stage and Dream-State Neural Decoding
- **Document Status:** Final Official Report
- **Template Alignment:** Matches the official `Lab Eval I Template.pdf` Table of Contents **verbatim** 1:1.

---

## Table of Contents Mapping

1. **Project Selection Phase**
   - **1.1 Software Bid**: Executive summary, problem statement & market opportunity, technical feasibility & innovation, economic and operational feasibility.
   - **1.2 Project Overview**: System concept, core architectural pillars (Ingestion, Signal Preprocessing, Machine Learning Engine, Clinical Web UI).
2. **Analysis Phase**
   - **2.1 Use Cases**:
     - *2.1.1 Use-Case Diagrams*: Visual diagram with 3 primary actors, 7 use cases, and `<<include>>` / `<<extend>>` relationships.
     - *2.1.2 Use Case Templates*: Fully detailed sunny-day and rainy-day scenarios with preconditions and postconditions.
   - **2.2 Activity Diagram and Swimlane Diagrams**: UML Activity model organized across 4 concurrent execution swimlanes (Dataset Streamer, Signal Preprocessor, ML Brain Engine, Clinical Web UI).
   - **2.3 Data Flow Diagrams (DFDs)**:
     - *2.3.1 DFD Level 0 (Context Diagram)*: Boundary with external entities (PhysioNet stream, Neurologist, EHR Database).
     - *2.3.2 DFD Level 1 (Modular)*: Decomposition into 5 functional processes (1.0 to 5.0) and 4 persistent data stores (D1 to D4).
     - *2.3.3 DFD Level 2*: Detailed decomposition of Subsystem 3.0 (Feature Engineering & Spatial Alignment).
   - **2.4 Software Requirement Specification (SRS) in IEEE Format**:
     - *1. Introduction*: Purpose, scope, definitions, references.
     - *2. Overall Description*: Product perspective, user classes, operating environment, design constraints.
     - *3. Specific Requirements*: Complete functional requirements (FR-01 to FR-08) and non-functional requirements (NFR-01 to NFR-06: latency, throughput, safety, reliability).
   - **2.5 User Stories and Story Cards**: Formal Agile user stories categorized by epic with acceptance criteria and story point estimates.
