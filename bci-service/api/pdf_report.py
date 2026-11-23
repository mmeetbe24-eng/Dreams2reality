# bci-service/api/pdf_report.py
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

def generate_clinical_pdf(
    report_data: dict, 
    patient_name: str = "Subject-01 (Clinical Trial)", 
    session_id: str = "D2R-REC-2026-X1",
    assessment: dict = None
) -> bytes:
    """
    Generates a formal Polysomnographic Sleep & Dream State Clinical Report.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#002B49') # Thapar Navy
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#555555')
    )
    heading2_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#E87722') # Thapar Amber
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#222222')
    )

    elements = []

    # Header
    elements.append(Paragraph("Dreams2Reality — Clinical BCI Neurological Report", title_style))
    elements.append(Paragraph("Two-Electrode (T7-T8) Non-Invasive Polysomnography & Nocturnal Affective Decoding", subtitle_style))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#002B49'), spaceAfter=15))

    # Patient & Session Info Table
    info_data = [
        [
            Paragraph(f"<b>Patient / Subject:</b> {patient_name}", body_style),
            Paragraph(f"<b>Session ID:</b> {session_id}", body_style)
        ],
        [
            Paragraph(f"<b>Date of Record:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", body_style),
            Paragraph(f"<b>BCI Montage:</b> Bipolar Scalp T7-T8 (128 Hz)", body_style)
        ],
        [
            Paragraph(f"<b>Session Duration:</b> {report_data.get('session_duration_sec', 0)} seconds", body_style),
            Paragraph(f"<b>Sleep Efficiency:</b> {report_data.get('sleep_efficiency', 0)}%", body_style)
        ]
    ]
    info_table = Table(info_data, colWidths=[270, 270])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F4F6F9')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#D0D7DE')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E1E4E8')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 15))

    # Section 1: Sleep Stage Distribution
    elements.append(Paragraph("1. Polysomnographic Architecture & Stage Breakdown", heading2_style))
    elements.append(Spacer(1, 6))

    dist = report_data.get('stage_distribution', {})
    stage_data = [
        ["Sleep Stage", "AASM Clinical Classification", "Percentage of Night", "Target Normal Range"],
        ["Wake", "Resting awake state (Alpha / Beta)", f"{dist.get('Wake', 0)}%", "5.0 - 15.0%"],
        ["Stage N1", "Light Sleep / Drowsiness (Theta)", f"{dist.get('N1', 0)}%", "2.0 - 5.0%"],
        ["Stage N2", "Core NREM (Sleep Spindles & K-Complexes)", f"{dist.get('N2', 0)}%", "45.0 - 55.0%"],
        ["Stage N3", "Slow-Wave Sleep (Deep Delta Waves)", f"{dist.get('N3', 0)}%", "15.0 - 25.0%"],
        ["Stage REM", "Dreaming / Paradoxical (Desynchronized)", f"{dist.get('REM', 0)}%", "20.0 - 25.0%"]
    ]
    stage_table = Table(stage_data, colWidths=[80, 220, 120, 120])
    stage_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#002B49')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#FFFFFF'), colors.HexColor('#F8FAFC')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(stage_table)
    elements.append(Spacer(1, 15))

    # Section 2: Hall-Van de Castle Dream Mentation Decoding
    elements.append(Paragraph("2. Hall-Van de Castle Dream Mentation & Affective Decoding", heading2_style))
    elements.append(Spacer(1, 6))

    archetypes = report_data.get('dream_archetype_distribution', {})
    arch_data = [
        ["HVdC Clinical Archetype", "Neurological Marker", "Detected Epochs"],
        ["Restful Baseline", "Symmetric temporal theta baseline", str(archetypes.get("Restful Baseline", 0))],
        ["Vivid Sensory", "Enhanced bilateral occipito-temporal beta", str(archetypes.get("Vivid Sensory", 0))],
        ["Cognitive Mentation", "Frontotemporal coherence, rational processing", str(archetypes.get("Cognitive Mentation", 0))],
        ["Motor Agitation", "Transient motor cortex delta/beta burst", str(archetypes.get("Motor Agitation", 0))],
        ["Threat Simulation", "Lateralized right temporal gamma spike (T8 > T7)", str(archetypes.get("Threat Simulation", 0))]
    ]
    arch_table = Table(arch_data, colWidths=[140, 260, 140])
    arch_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E87722')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#FFFFFF'), colors.HexColor('#FFF7ED')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#FDBA74')),
        ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(arch_table)
    elements.append(Spacer(1, 15))

    # Section 3: Pre-Sleep Cognitive & Stress Assessment (If Available)
    if assessment:
        elements.append(Paragraph("3. Pre-Sleep Cognitive & Stress Assessment Profile", heading2_style))
        elements.append(Spacer(1, 6))

        stress_score = assessment.get("stress_level", "N/A")
        react_time = assessment.get("reaction_time_ms", "N/A")
        jitter = assessment.get("jitter_ms", "N/A")
        ptsd_freq = assessment.get("ptsd_frequency", "None")

        assess_data = [
            ["Clinical Assessment Metric", "Patient Response / Measured Value", "Calibrated Physiological Bias"],
            ["Self-Reported Stress (1-10)", f"{stress_score} / 10", f"Beta Power Modulator: x{0.7 + (float(stress_score)/10.0)*0.8:.2f}"],
            ["Attention Reaction Latency", f"{react_time} ms", "Cognitive processing speed"],
            ["Neuromotor Reaction Jitter", f"{jitter} ms variance", "Autonomic arousal stability"],
            ["Nightmare / PTSD Vulnerability", f"{str(ptsd_freq).upper()}", "AASM REM Threat Agitation Threshold"]
        ]
        assess_table = Table(assess_data, colWidths=[160, 180, 200])
        assess_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284C7')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#FFFFFF'), colors.HexColor('#F0F9FF')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BAE6FD')),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(assess_table)
        elements.append(Spacer(1, 15))

    # Section 4: Trauma / Nightmare Episode Log
    sec_num = "4" if assessment else "3"
    elements.append(Paragraph(f"{sec_num}. Acute Nightmare & Bedside Trauma Alerts Log", heading2_style))
    elements.append(Spacer(1, 6))

    trauma_events = report_data.get('trauma_events', [])
    if trauma_events:
        alert_rows = [["Timestamp (s)", "Sleep Stage", "Archetype", "Threat Conf.", "Severity"]]
        for ev in trauma_events:
            alert_rows.append([
                f"{ev.get('timestamp', 0)}s",
                str(ev.get('stage', 'REM')),
                str(ev.get('archetype', 'Threat Simulation')),
                f"{ev.get('threat_probability', 0):.2f}",
                f"{ev.get('severity', 0):.2f}"
            ])
        alert_table = Table(alert_rows, colWidths=[100, 100, 160, 90, 90])
        alert_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#DC2626')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#FCA5A5')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#FEF2F2'), colors.white]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(alert_table)
    else:
        elements.append(Paragraph("<i>No acute nightmare spikes or trauma alerts recorded during this session. Normal nocturnal physiology observed.</i>", body_style))

    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=10))
    elements.append(Paragraph("Verified by Dreams2Reality Automated Neural Inference Engine (DC-CTA Net v2.0). For clinical research and sleep health supervision.", subtitle_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
