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

    story.append(_header_table(f"Orden de Trabajo #{order.number}",
                               f"Estado: {order.status.upper()}"))
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
         Paragraph("Estado:", label_style), Paragraph(order.status.title(), val_style)],
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
