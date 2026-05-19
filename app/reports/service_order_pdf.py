import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
from app.config import APP_NAME, LOGO_PATH, ESCRITORIO, COLORS

GOLD = colors.HexColor(COLORS["gold"])
NAVY = colors.HexColor(COLORS["navy"])
LIGHT_GRAY = colors.HexColor("#F4F6F8")
BORDER = colors.HexColor("#DDE1E7")


def _styles():
    base = getSampleStyleSheet()
    styles = {}
    styles["title"] = ParagraphStyle(
        "title", parent=base["Heading1"],
        fontSize=16, textColor=NAVY, spaceAfter=2, alignment=TA_CENTER, fontName="Helvetica-Bold",
    )
    styles["subtitle"] = ParagraphStyle(
        "subtitle", parent=base["Normal"],
        fontSize=10, textColor=colors.HexColor("#7F8C8D"), alignment=TA_CENTER, spaceAfter=12,
    )
    styles["heading"] = ParagraphStyle(
        "heading", parent=base["Normal"],
        fontSize=11, textColor=NAVY, fontName="Helvetica-Bold", spaceBefore=8, spaceAfter=4,
    )
    styles["body"] = ParagraphStyle(
        "body", parent=base["Normal"],
        fontSize=9, textColor=colors.HexColor("#2C3E50"), leading=14,
    )
    styles["small"] = ParagraphStyle(
        "small", parent=base["Normal"],
        fontSize=8, textColor=colors.HexColor("#7F8C8D"),
    )
    styles["right"] = ParagraphStyle(
        "right", parent=base["Normal"],
        fontSize=9, alignment=TA_RIGHT,
    )
    styles["center"] = ParagraphStyle(
        "center", parent=base["Normal"],
        fontSize=9, alignment=TA_CENTER,
    )
    styles["signature"] = ParagraphStyle(
        "signature", parent=base["Normal"],
        fontSize=9, alignment=TA_CENTER, textColor=colors.HexColor("#2C3E50"),
    )
    return styles


def generate_os_pdf(order, items, output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )
    S = _styles()
    story = []
    page_width = A4[0] - 4*cm

    # ── Header ──
    header_data = []
    logo_cell = ""
    if os.path.exists(LOGO_PATH):
        try:
            img = Image(LOGO_PATH, width=3*cm, height=3*cm)
            logo_cell = img
        except Exception:
            logo_cell = Paragraph(APP_NAME, S["title"])
    else:
        logo_cell = Paragraph(APP_NAME, S["title"])

    escritorio_info = [
        Paragraph(f"<b>{APP_NAME}</b>", S["heading"]),
        Paragraph(ESCRITORIO.get("endereco", ""), S["small"]),
        Paragraph(f"{ESCRITORIO.get('cidade', '')} - {ESCRITORIO.get('estado', '')}", S["small"]),
        Paragraph(f"Tel: {ESCRITORIO.get('telefone', '')}  |  {ESCRITORIO.get('email', '')}", S["small"]),
        Paragraph(f"CNPJ: {ESCRITORIO.get('cnpj', '')}  |  CRC: {ESCRITORIO.get('crc', '')}", S["small"]),
    ]

    os_info = [
        Paragraph("<b>ORDEM DE SERVIÇO</b>", ParagraphStyle(
            "os_header", fontSize=14, fontName="Helvetica-Bold",
            textColor=GOLD, alignment=TA_RIGHT,
        )),
        Paragraph(f"Nº <b>{order['number']}</b>", ParagraphStyle(
            "os_num", fontSize=18, fontName="Helvetica-Bold",
            textColor=NAVY, alignment=TA_RIGHT,
        )),
        Paragraph(f"Data: {_fmt_date(order['date'])}", S["right"]),
        Paragraph(f"Status: {order['status']}", S["right"]),
    ]

    header_table = Table(
        [[logo_cell, escritorio_info, os_info]],
        colWidths=[3.5*cm, None, 6*cm],
    )
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=2, color=GOLD, spaceAfter=12))

    # ── Client info ──
    story.append(Paragraph("DADOS DO CLIENTE", S["heading"]))

    client_data = [
        [
            Paragraph(f"<b>Cliente:</b> {order['client_name']}", S["body"]),
            Paragraph(f"<b>CNPJ/CPF:</b> {order['cnpj_cpf']}", S["body"]),
        ],
    ]
    if order.get("contact_person"):
        client_data.append([
            Paragraph(f"<b>Responsável:</b> {order['contact_person']}", S["body"]),
            Paragraph(f"<b>E-mail:</b> {order.get('email', '')}", S["body"]),
        ])
    addr = _fmt_address(order)
    if addr:
        client_data.append([
            Paragraph(f"<b>Endereço:</b> {addr}", S["body"]),
            Paragraph(f"<b>Telefone:</b> {order.get('phone', '')}", S["body"]),
        ])

    client_table = Table(client_data, colWidths=[page_width/2, page_width/2])
    client_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(client_table)
    story.append(Spacer(1, 12))

    # ── Description ──
    if order.get("description"):
        story.append(Paragraph("DESCRIÇÃO DO SERVIÇO", S["heading"]))
        story.append(Paragraph(order["description"], S["body"]))
        story.append(Spacer(1, 8))

    # ── Items table ──
    story.append(Paragraph("SERVIÇOS / ITENS", S["heading"]))

    item_header = [
        Paragraph("<b>Descrição</b>", S["body"]),
        Paragraph("<b>Qtd.</b>", S["center"]),
        Paragraph("<b>Valor Unit.</b>", S["right"]),
        Paragraph("<b>Total</b>", S["right"]),
    ]
    item_rows = [item_header]
    for it in items:
        item_rows.append([
            Paragraph(it["description"], S["body"]),
            Paragraph(str(it["quantity"]).replace(".", ","), S["center"]),
            Paragraph(_fmt_money(it["unit_price"]), S["right"]),
            Paragraph(_fmt_money(it["total"]), S["right"]),
        ])

    col_widths = [page_width - 5*cm, 2*cm, 2.5*cm, 2.5*cm]
    items_table = Table(item_rows, colWidths=col_widths, repeatRows=1)
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 8))

    # ── Totals ──
    subtotal = order.get("subtotal", 0) or 0
    discount = order.get("discount", 0) or 0
    total = order.get("total", 0) or 0

    totals_data = []
    if discount > 0:
        totals_data.append(["Subtotal:", _fmt_money(subtotal)])
        totals_data.append(["Desconto:", f"- {_fmt_money(discount)}"])
    totals_data.append(["TOTAL:", _fmt_money(total)])

    totals_table = Table(totals_data, colWidths=[page_width - 4*cm, 4*cm])
    totals_style = [
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, -1), (-1, -1), 12),
        ("TEXTCOLOR", (0, -1), (-1, -1), NAVY),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("BACKGROUND", (0, -1), (-1, -1), LIGHT_GRAY),
        ("BOX", (0, -1), (-1, -1), 1, GOLD),
    ]
    totals_table.setStyle(TableStyle(totals_style))
    story.append(totals_table)
    story.append(Spacer(1, 12))

    # ── Notes ──
    if order.get("notes"):
        story.append(Paragraph("OBSERVAÇÕES", S["heading"]))
        story.append(Paragraph(order["notes"], S["body"]))
        story.append(Spacer(1, 12))

    # ── Signature ──
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceBefore=20, spaceAfter=20))

    city = ESCRITORIO.get("cidade", "")
    date_str = _fmt_date(order["date"])
    story.append(Paragraph(
        f"{city}, {date_str}",
        ParagraphStyle("loc", fontSize=9, alignment=TA_CENTER, textColor=colors.HexColor("#7F8C8D")),
    ))
    story.append(Spacer(1, 24))

    sig_data = [
        [
            HRFlowable(width="85%", thickness=0.75, color=NAVY),
            HRFlowable(width="85%", thickness=0.75, color=NAVY),
        ],
        [
            Paragraph(f"<b>{ESCRITORIO.get('responsavel', APP_NAME)}</b><br/>{APP_NAME}<br/>CRC: {ESCRITORIO.get('crc', '')}", S["signature"]),
            Paragraph(f"<b>{order['client_name']}</b><br/>Cliente / Responsável<br/>Data: ___/___/______", S["signature"]),
        ],
    ]
    sig_table = Table(sig_data, colWidths=[page_width/2, page_width/2])
    sig_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(sig_table)

    # ── Footer ──
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GOLD))
    story.append(Paragraph(
        f"{APP_NAME}  |  {ESCRITORIO.get('endereco', '')}  |  {ESCRITORIO.get('telefone', '')}",
        ParagraphStyle("footer", fontSize=7, alignment=TA_CENTER, textColor=colors.HexColor("#7F8C8D")),
    ))

    doc.build(story)
    return output_path


def _fmt_date(d: str) -> str:
    if not d:
        return ""
    try:
        return datetime.strptime(d[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return d


def _fmt_money(v) -> str:
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def _fmt_address(order) -> str:
    parts = []
    if order.get("address"):
        parts.append(order["address"])
    if order.get("addr_number"):
        parts.append(f"nº {order['addr_number']}")
    if order.get("complement"):
        parts.append(order["complement"])
    if order.get("neighborhood"):
        parts.append(order["neighborhood"])
    if order.get("city"):
        parts.append(f"{order['city']}/{order.get('state', '')}")
    return ", ".join(parts)
