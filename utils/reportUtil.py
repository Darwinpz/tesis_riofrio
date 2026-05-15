import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

HEADER_COLOR = colors.HexColor("#1a1a2e")
ACCENT_COLOR = colors.HexColor("#0f3460")
LIGHT_GRAY = colors.HexColor("#f8f9fa")
DARK_GRAY = colors.HexColor("#6c757d")

def _build_doc(buffer):
    return SimpleDocTemplate(buffer, pagesize=A4,
                              leftMargin=1.5*cm, rightMargin=1.5*cm,
                              topMargin=2*cm, bottomMargin=2*cm)

def _header_table(title: str, subtitle: str = "") -> Table:
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('title', parent=styles['Normal'],
                                 fontSize=16, textColor=colors.white,
                                 fontName='Helvetica-Bold', alignment=TA_LEFT)
    sub_style = ParagraphStyle('sub', parent=styles['Normal'],
                               fontSize=9, textColor=colors.HexColor("#cccccc"),
                               fontName='Helvetica', alignment=TA_LEFT)
    date_style = ParagraphStyle('date', parent=styles['Normal'],
                                fontSize=9, textColor=colors.white,
                                fontName='Helvetica', alignment=TA_RIGHT)

    data = [[Paragraph(f"Mechita — {title}", title_style),
             Paragraph(datetime.now().strftime("%d/%m/%Y %H:%M"), date_style)]]
    if subtitle:
        data.append([Paragraph(subtitle, sub_style), ""])

    tbl = Table(data, colWidths=['*', 5*cm])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HEADER_COLOR),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, -1), 10),
        ('RIGHTPADDING', (-1, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('SPAN', (0, 1), (-1, 1)) if subtitle else ('', (0, 0), (0, 0), ''),
    ]))
    return tbl


def generate_stock_report(parts: list, critical_only: bool = False) -> bytes:
    buffer = io.BytesIO()
    doc = _build_doc(buffer)
    styles = getSampleStyleSheet()
    story = []

    title = "Reporte de Stock Crítico" if critical_only else "Reporte de Inventario"
    story.append(_header_table(title, f"Total de repuestos: {len(parts)}"))
    story.append(Spacer(1, 0.4*cm))

    headers = ["Código", "Nombre", "Stock Actual", "Stock Mínimo", "Stock Máximo", "Precio Venta", "Estado"]
    rows = [headers]
    for p in parts:
        status = "CRÍTICO" if p.stock_actual <= p.stock_minimo else "OK"
        rows.append([
            p.code,
            p.name,
            str(p.stock_actual),
            str(p.stock_minimo),
            str(p.stock_maximo),
            f"${p.precio_venta:.2f}",
            status
        ])

    col_widths = [2.5*cm, 5.5*cm, 2.2*cm, 2.2*cm, 2.5*cm, 2.5*cm, 2*cm]
    tbl = Table(rows, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

    # Colorear filas críticas en rojo claro
    for i, p in enumerate(parts, start=1):
        if p.stock_actual <= p.stock_minimo:
            tbl.setStyle(TableStyle([
                ('BACKGROUND', (0, i), (-1, i), colors.HexColor("#ffe0e0")),
                ('TEXTCOLOR', (6, i), (6, i), colors.HexColor("#cc0000")),
                ('FONTNAME', (6, i), (6, i), 'Helvetica-Bold'),
            ]))

    story.append(tbl)
    doc.build(story)
    return buffer.getvalue()


def generate_movements_report(movements: list, parts_map: dict,
                               start_date: str = None, end_date: str = None) -> bytes:
    buffer = io.BytesIO()
    doc = _build_doc(buffer)
    story = []

    subtitle = ""
    if start_date or end_date:
        subtitle = f"Período: {start_date or '—'} a {end_date or '—'}"
    story.append(_header_table("Reporte de Movimientos de Stock", subtitle))
    story.append(Spacer(1, 0.4*cm))

    headers = ["Fecha", "Repuesto", "Tipo", "Cantidad", "Motivo", "Nota"]
    rows = [headers]
    for m in movements:
        rows.append([
            m.created_at.strftime("%d/%m/%Y %H:%M") if hasattr(m.created_at, 'strftime') else str(m.created_at),
            parts_map.get(m.spare_part_id, m.spare_part_id),
            "Entrada" if m.movement_type == "entrada" else "Salida",
            str(m.quantity),
            m.motive.replace("_", " ").title(),
            m.note or ""
        ])

    col_widths = [3.2*cm, 5*cm, 1.8*cm, 1.8*cm, 2.8*cm, '*']
    tbl = Table(rows, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('ALIGN', (5, 1), (5, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

    # Color por tipo
    for i, m in enumerate(movements, start=1):
        if m.movement_type == "entrada":
            tbl.setStyle(TableStyle([('TEXTCOLOR', (2, i), (2, i), colors.HexColor("#198754"))]))
        else:
            tbl.setStyle(TableStyle([('TEXTCOLOR', (2, i), (2, i), colors.HexColor("#dc3545"))]))

    story.append(tbl)
    doc.build(story)
    return buffer.getvalue()


def generate_work_order_pdf(order, client_name: str) -> bytes:
    buffer = io.BytesIO()
    doc = _build_doc(buffer)
    styles = getSampleStyleSheet()
    story = []

    status_display = order.canonical_status.replace('_', ' ').title() if hasattr(order, 'canonical_status') else order.status.replace('_', ' ').title()
    story.append(_header_table(f"Ingreso de Taller #{order.number}",
                               f"Estado: {status_display}"))
    story.append(Spacer(1, 0.5*cm))

    label_style = ParagraphStyle('lbl', parent=styles['Normal'],
                                 fontName='Helvetica-Bold', fontSize=9)
    val_style = ParagraphStyle('val', parent=styles['Normal'],
                               fontName='Helvetica', fontSize=9)

    # Datos generales
    info_data = [
        [Paragraph("Cliente:", label_style), Paragraph(client_name, val_style),
         Paragraph("Fecha:", label_style),
         Paragraph(order.created_at.strftime("%d/%m/%Y") if hasattr(order.created_at, 'strftime') else str(order.created_at), val_style)],
        [Paragraph("Marca:", label_style), Paragraph(order.vehicle_brand, val_style),
         Paragraph("Modelo:", label_style), Paragraph(order.vehicle_model, val_style)],
        [Paragraph("Placa:", label_style), Paragraph(order.vehicle_plate, val_style),
         Paragraph("Estado:", label_style), Paragraph(status_display, val_style)],
    ]
    info_tbl = Table(info_data, colWidths=[2.5*cm, 6*cm, 2.5*cm, 6*cm])
    info_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(info_tbl)
    story.append(Spacer(1, 0.4*cm))

    # Notas
    if order.notes:
        story.append(Paragraph("Notas:", label_style))
        story.append(Paragraph(order.notes, val_style))
        story.append(Spacer(1, 0.3*cm))

    # Repuestos
    story.append(Paragraph("Repuestos utilizados:", label_style))
    story.append(Spacer(1, 0.2*cm))

    part_headers = ["Código/Nombre", "Cantidad", "Precio Unit.", "Subtotal"]
    part_rows = [part_headers]
    for p in order.parts:
        part_rows.append([
            p.get("spare_part_name", "—"),
            str(p.get("quantity", 0)),
            f"${float(p.get('unit_price', 0)):.2f}",
            f"${float(p.get('subtotal', 0)):.2f}"
        ])

    part_tbl = Table(part_rows, colWidths=[8*cm, 2.5*cm, 3*cm, 3*cm], repeatRows=1)
    part_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(part_tbl)
    story.append(Spacer(1, 0.4*cm))

    # Totales
    total_style = ParagraphStyle('tot', parent=styles['Normal'],
                                 fontName='Helvetica-Bold', fontSize=10, alignment=TA_RIGHT)
    subtotal = order.total - order.labor_cost
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT_COLOR))
    story.append(Spacer(1, 0.2*cm))

    totals_data = [
        ["", "Subtotal repuestos:", f"${subtotal:.2f}"],
        ["", "Mano de obra:", f"${order.labor_cost:.2f}"],
        ["", "TOTAL:", f"${order.total:.2f}"],
    ]
    tot_tbl = Table(totals_data, colWidths=['*', 4*cm, 3*cm])
    tot_tbl.setStyle(TableStyle([
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 1), 'Helvetica'),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTSIZE', (0, 2), (-1, 2), 12),
        ('TEXTCOLOR', (0, 2), (-1, 2), ACCENT_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(tot_tbl)

    doc.build(story)
    return buffer.getvalue()


def generate_work_orders_list_pdf(orders: list, clients_map: dict,
                                  filter_search: str = "", filter_status: str = "") -> bytes:
    buffer = io.BytesIO()
    doc = _build_doc(buffer)
    styles = getSampleStyleSheet()
    story = []

    subtitle = f"Total: {len(orders)} ingreso(s)"
    if filter_search:
        subtitle += f" · Búsqueda: {filter_search}"
    if filter_status:
        subtitle += f" · Estado: {filter_status.replace('_', ' ').title()}"

    story.append(_header_table("Reporte de Ingresos de Taller", subtitle))
    story.append(Spacer(1, 0.4*cm))

    STATUS_LABELS = {
        "recepcion": "Recepción", "diagnostico": "Diagnóstico",
        "presupuesto": "Presupuesto", "aprobado": "Aprobado",
        "en_reparacion": "En Reparación", "pago_pendiente": "Pago Pendiente",
        "entregado": "Entregado",
    }

    label_style = ParagraphStyle('lbl', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8)
    val_style = ParagraphStyle('val', parent=styles['Normal'], fontName='Helvetica', fontSize=8)

    headers = ["N° Ingreso", "Vehículo", "Placa", "Cliente", "Estado", "Total", "Fecha"]
    rows = [headers]
    for o in orders:
        client_name = clients_map.get(o.client_id, "—")
        vehicle = f"{o.vehicle_brand} {o.vehicle_model}"
        if o.vehicle_year:
            vehicle += f" ({o.vehicle_year})"
        status = STATUS_LABELS.get(o.canonical_status, o.status.replace('_', ' ').title())
        date = o.created_at.strftime("%d/%m/%Y") if hasattr(o.created_at, 'strftime') else str(o.created_at)
        rows.append([
            o.number,
            vehicle,
            o.vehicle_plate,
            client_name,
            status,
            f"${o.total:.2f}",
            date
        ])

    col_widths = [2.2*cm, 4.5*cm, 2*cm, 4*cm, 2.8*cm, 2*cm, 2.2*cm]
    tbl = Table(rows, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('ALIGN', (3, 1), (3, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(tbl)

    doc.build(story)
    return buffer.getvalue()


def generate_reception_receipt(order, client_name: str, mechanic_name: str = "") -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=1.5*cm, rightMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    # ── Cabecera dual-columna ──────────────────────────────────────────────────
    brand_style = ParagraphStyle('brand', parent=styles['Normal'],
                                 fontName='Helvetica-Bold', fontSize=18,
                                 textColor=colors.white, alignment=TA_LEFT)
    title_style = ParagraphStyle('rtitle', parent=styles['Normal'],
                                 fontName='Helvetica-Bold', fontSize=13,
                                 textColor=colors.white, alignment=TA_RIGHT)
    hdr_data = [[Paragraph("Mechita", brand_style),
                 Paragraph("COMPROBANTE DE RECEPCIÓN", title_style)]]
    hdr_tbl = Table(hdr_data, colWidths=['*', 8*cm])
    hdr_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HEADER_COLOR),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, -1), 12),
        ('RIGHTPADDING', (-1, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(hdr_tbl)

    # ── Sub-cabecera: número de orden y fecha ─────────────────────────────────
    sub_l = ParagraphStyle('sl', parent=styles['Normal'],
                           fontName='Helvetica-Bold', fontSize=10,
                           textColor=colors.white, alignment=TA_LEFT)
    sub_r = ParagraphStyle('sr', parent=styles['Normal'],
                           fontName='Helvetica', fontSize=9,
                           textColor=colors.white, alignment=TA_RIGHT)
    entry_date = (order.created_at.strftime("%d/%m/%Y %H:%M")
                  if hasattr(order.created_at, 'strftime') else str(order.created_at))
    sub_data = [[Paragraph(f"Ingreso N° {order.number}", sub_l),
                 Paragraph(f"Fecha de ingreso: {entry_date}", sub_r)]]
    sub_tbl = Table(sub_data, colWidths=['*', 8*cm])
    sub_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), ACCENT_COLOR),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, -1), 12),
        ('RIGHTPADDING', (-1, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(sub_tbl)
    story.append(Spacer(1, 0.5*cm))

    def section_header(text):
        sh_style = ParagraphStyle('sh', parent=styles['Normal'],
                                  fontName='Helvetica-Bold', fontSize=9,
                                  textColor=colors.white, alignment=TA_LEFT)
        sh_data = [[Paragraph(text.upper(), sh_style)]]
        sh_tbl = Table(sh_data, colWidths=['*'])
        sh_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), DARK_GRAY),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        return sh_tbl

    lbl = ParagraphStyle('lbl', parent=styles['Normal'],
                         fontName='Helvetica-Bold', fontSize=9)
    val = ParagraphStyle('val', parent=styles['Normal'],
                         fontName='Helvetica', fontSize=9)

    # ── Datos del vehículo ────────────────────────────────────────────────────
    story.append(section_header("Datos del Vehículo"))
    story.append(Spacer(1, 0.15*cm))
    v_data = [
        [Paragraph("Marca:", lbl), Paragraph(order.vehicle_brand or "—", val),
         Paragraph("Modelo:", lbl), Paragraph(order.vehicle_model or "—", val)],
        [Paragraph("Placa:", lbl), Paragraph(order.vehicle_plate or "—", val),
         Paragraph("Estado al ingreso:", lbl), Paragraph(order.status_label, val)],
    ]
    v_tbl = Table(v_data, colWidths=[2.8*cm, 5.5*cm, 3.5*cm, 5.5*cm])
    v_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(v_tbl)
    story.append(Spacer(1, 0.4*cm))

    # ── Cliente y mecánico ────────────────────────────────────────────────────
    story.append(section_header("Cliente y Mecánico Asignado"))
    story.append(Spacer(1, 0.15*cm))
    cm_data = [
        [Paragraph("Cliente:", lbl), Paragraph(client_name or "—", val),
         Paragraph("Mecánico:", lbl), Paragraph(mechanic_name or "Sin asignar", val)],
    ]
    cm_tbl = Table(cm_data, colWidths=[2.8*cm, 5.5*cm, 3.5*cm, 5.5*cm])
    cm_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(cm_tbl)
    story.append(Spacer(1, 0.4*cm))

    # ── Observaciones ─────────────────────────────────────────────────────────
    story.append(section_header("Observaciones del Vehículo al Ingreso"))
    story.append(Spacer(1, 0.15*cm))
    obs_text = order.notes or "Sin observaciones registradas."
    obs_data = [[Paragraph(obs_text, val)]]
    obs_tbl = Table(obs_data, colWidths=['*'])
    obs_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(obs_tbl)
    story.append(Spacer(1, 0.4*cm))

    # ── Repuestos / trabajos ──────────────────────────────────────────────────
    story.append(section_header("Repuestos / Trabajos Registrados"))
    story.append(Spacer(1, 0.15*cm))

    if order.parts:
        ph = ["Descripción", "Cantidad", "Precio Unit.", "Subtotal"]
        p_rows = [ph]
        total_parts = 0.0
        for p in order.parts:
            sub = float(p.get('subtotal', 0))
            total_parts += sub
            p_rows.append([
                p.get("spare_part_name", "—"),
                str(p.get("quantity", 0)),
                f"${float(p.get('unit_price', 0)):.2f}",
                f"${sub:.2f}",
            ])
        p_tbl = Table(p_rows, colWidths=[8.5*cm, 2.2*cm, 3*cm, 3*cm], repeatRows=1)
        p_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), ACCENT_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(p_tbl)
        story.append(Spacer(1, 0.2*cm))

        tot_r_style = ParagraphStyle('trr', parent=styles['Normal'],
                                     fontName='Helvetica-Bold', fontSize=10,
                                     alignment=TA_RIGHT)
        tot_rows = [
            ["", "Subtotal repuestos:", f"${total_parts:.2f}"],
            ["", "Mano de obra:", f"${order.labor_cost:.2f}"],
            ["", "TOTAL:", f"${order.total:.2f}"],
        ]
        tot_tbl = Table(tot_rows, colWidths=['*', 4.5*cm, 3*cm])
        tot_tbl.setStyle(TableStyle([
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 1), 'Helvetica'),
            ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTSIZE', (0, 2), (-1, 2), 12),
            ('TEXTCOLOR', (0, 2), (-1, 2), ACCENT_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(tot_tbl)
    else:
        story.append(Paragraph("Sin repuestos registrados al momento de la recepción.", val))

    story.append(Spacer(1, 0.4*cm))

    # ── Aviso fotos ───────────────────────────────────────────────────────────
    if order.vehicle_photos:
        n = len(order.vehicle_photos)
        photo_data = [[Paragraph(
            f"📷  Se registraron {n} foto(s) del vehículo al ingreso. "
            "Las fotos están disponibles en el sistema.",
            ParagraphStyle('ph', parent=styles['Normal'],
                           fontName='Helvetica', fontSize=8,
                           textColor=colors.HexColor("#856404")))]]
        ph_tbl = Table(photo_data, colWidths=['*'])
        ph_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#fff3cd")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#ffc107")),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(ph_tbl)
        story.append(Spacer(1, 0.4*cm))

    # ── Firmas ────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=DARK_GRAY))
    story.append(Spacer(1, 1.2*cm))
    sig_lbl = ParagraphStyle('sig', parent=styles['Normal'],
                              fontName='Helvetica', fontSize=9,
                              alignment=TA_CENTER)
    sig_data = [[Paragraph("_______________________________", sig_lbl),
                 Paragraph("_______________________________", sig_lbl)],
                [Paragraph("Firma del Cliente", sig_lbl),
                 Paragraph("Firma del Operador / Recepcionista", sig_lbl)]]
    sig_tbl = Table(sig_data, colWidths=['*', '*'])
    sig_tbl.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(sig_tbl)
    story.append(Spacer(1, 0.6*cm))

    # ── Pie de página ─────────────────────────────────────────────────────────
    footer_style = ParagraphStyle('ft', parent=styles['Normal'],
                                  fontName='Helvetica', fontSize=7,
                                  textColor=DARK_GRAY, alignment=TA_CENTER)
    story.append(HRFlowable(width="100%", thickness=0.5, color=DARK_GRAY))
    story.append(Spacer(1, 0.15*cm))
    story.append(Paragraph(
        f"Generado por Mechita · {datetime.now().strftime('%d/%m/%Y %H:%M')} · "
        "Documento de recepción — conservar para seguimiento de la orden.",
        footer_style))

    doc.build(story)
    return buffer.getvalue()
