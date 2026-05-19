import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import Image
from app.config import APP_NAME, LOGO_PATH, ESCRITORIO, CONTRACT_TYPES, COLORS

GOLD = colors.HexColor(COLORS["gold"])
NAVY = colors.HexColor(COLORS["navy"])
LIGHT_GRAY = colors.HexColor("#F4F6F8")
BORDER = colors.HexColor("#DDE1E7")


def _styles():
    base = getSampleStyleSheet()
    styles = {}
    styles["title"] = ParagraphStyle(
        "c_title", fontSize=14, fontName="Helvetica-Bold",
        textColor=NAVY, alignment=TA_CENTER, spaceAfter=4,
    )
    styles["subtitle"] = ParagraphStyle(
        "c_subtitle", fontSize=10, alignment=TA_CENTER,
        textColor=colors.HexColor("#7F8C8D"), spaceAfter=12,
    )
    styles["clause_title"] = ParagraphStyle(
        "c_clause", fontSize=10, fontName="Helvetica-Bold",
        textColor=NAVY, spaceBefore=12, spaceAfter=4,
    )
    styles["body"] = ParagraphStyle(
        "c_body", fontSize=9, leading=14, alignment=TA_JUSTIFY,
        textColor=colors.HexColor("#2C3E50"),
    )
    styles["center"] = ParagraphStyle(
        "c_center", fontSize=9, alignment=TA_CENTER,
        textColor=colors.HexColor("#2C3E50"),
    )
    styles["right"] = ParagraphStyle(
        "c_right", fontSize=9, alignment=TA_RIGHT,
    )
    styles["small"] = ParagraphStyle(
        "c_small", fontSize=8, textColor=colors.HexColor("#7F8C8D"),
    )
    styles["signature"] = ParagraphStyle(
        "c_sig", fontSize=9, alignment=TA_CENTER, leading=14,
    )
    return styles


def generate_contract_pdf(contract, client, output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2.5*cm, rightMargin=2.5*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )
    S = _styles()
    story = []
    page_width = A4[0] - 5*cm

    # ── Header ──
    logo_cell = ""
    if os.path.exists(LOGO_PATH):
        try:
            logo_cell = Image(LOGO_PATH, width=2.5*cm, height=2.5*cm)
        except Exception:
            logo_cell = Paragraph(APP_NAME, S["title"])
    else:
        logo_cell = Paragraph(APP_NAME, S["title"])

    escritorio_block = [
        Paragraph(f"<b>{APP_NAME}</b>", ParagraphStyle(
            "esc_name", fontSize=11, fontName="Helvetica-Bold", textColor=NAVY,
        )),
        Paragraph(ESCRITORIO.get("endereco", ""), S["small"]),
        Paragraph(f"{ESCRITORIO.get('cidade', '')} - {ESCRITORIO.get('estado', '')}  CEP: {ESCRITORIO.get('cep', '')}", S["small"]),
        Paragraph(f"Tel: {ESCRITORIO.get('telefone', '')}  |  {ESCRITORIO.get('email', '')}", S["small"]),
        Paragraph(f"CNPJ: {ESCRITORIO.get('cnpj', '')}  |  CRC: {ESCRITORIO.get('crc', '')}", S["small"]),
    ]

    contract_block = [
        Paragraph(f"<b>CONTRATO Nº {contract['number']}</b>", ParagraphStyle(
            "ct_num", fontSize=12, fontName="Helvetica-Bold", textColor=GOLD, alignment=TA_RIGHT,
        )),
        Paragraph(f"Data: {_fmt_date(contract['date'])}", ParagraphStyle(
            "ct_date", fontSize=9, alignment=TA_RIGHT,
        )),
    ]

    hdr = Table([[logo_cell, escritorio_block, contract_block]], colWidths=[3*cm, None, 5*cm])
    hdr.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(hdr)
    story.append(HRFlowable(width="100%", thickness=2, color=GOLD, spaceBefore=8, spaceAfter=12))

    # ── Title ──
    ct_label = CONTRACT_TYPES.get(contract.get("type", "CONTABIL"), "Serviços Contábeis")
    story.append(Paragraph(f"CONTRATO DE PRESTAÇÃO DE {ct_label.upper()}", S["title"]))
    story.append(Spacer(1, 16))

    # ── Parties ──
    story.append(Paragraph("IDENTIFICAÇÃO DAS PARTES", S["clause_title"]))

    story.append(Paragraph(
        f"<b>1. CONTRATADO:</b> {ESCRITORIO.get('responsavel', APP_NAME)}, "
        f"Contador, CRC {ESCRITORIO.get('crc', '')}, com Escritório Contábil situado em "
        f"{ESCRITORIO.get('endereco', '')}, {ESCRITORIO.get('cidade', '')}/{ESCRITORIO.get('estado', '')}, "
        f"CEP {ESCRITORIO.get('cep', '')}.",
        S["body"],
    ))
    story.append(Spacer(1, 8))

    client_type = client.get("type", "PJ")
    if client_type == "PJ":
        party_desc = (
            f"<b>2. CONTRATANTE:</b> {client['name']}, inscrita no CNPJ sob nº "
            f"{client['cnpj_cpf']}, com sede na {_fmt_client_address(client)}, "
            f"neste ato representada pelo responsável <b>{client.get('contact_person', '') or 'qualificado(a) abaixo'}</b>."
        )
    else:
        party_desc = (
            f"<b>2. CONTRATANTE:</b> {client['name']}, portador(a) do CPF nº {client['cnpj_cpf']}, "
            f"residente e domiciliado(a) em {_fmt_client_address(client)}."
        )

    story.append(Paragraph(party_desc, S["body"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "As partes acima identificadas firmam o presente Contrato de Prestação de Serviços, "
        "conforme as cláusulas a seguir:",
        S["body"],
    ))

    # ── Contract content ──
    content = contract.get("content", "") or ""
    if content.strip():
        story.append(Spacer(1, 12))
        for line in content.split("\n"):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 6))
                continue
            if line.startswith("CLÁUSULA") or line.startswith("CLAUSULA") or line.upper().startswith("CLÁUSULA"):
                story.append(Paragraph(line, S["clause_title"]))
            else:
                story.append(Paragraph(line, S["body"]))
    else:
        # Default contract body
        story.extend(_default_contract_clauses(contract, client, S))

    # ── Signatures ──
    story.append(Spacer(1, 24))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    story.append(Spacer(1, 8))

    city = ESCRITORIO.get("cidade", "") or client.get("city", "")
    story.append(Paragraph(
        f"{city}, {_fmt_date(contract['date'])}.",
        ParagraphStyle("sig_date", fontSize=9, alignment=TA_CENTER,
                       textColor=colors.HexColor("#7F8C8D")),
    ))
    story.append(Spacer(1, 32))

    sig_data = [
        [
            HRFlowable(width="85%", thickness=0.75, color=NAVY),
            HRFlowable(width="85%", thickness=0.75, color=NAVY),
        ],
        [
            Paragraph(
                f"<b>CONTRATADO</b><br/>{ESCRITORIO.get('responsavel', '')}<br/>"
                f"Contador — CRC: {ESCRITORIO.get('crc', '')}",
                S["signature"],
            ),
            Paragraph(
                f"<b>CONTRATANTE</b><br/>{client['name']}<br/>"
                f"{'CNPJ: ' if client_type == 'PJ' else 'CPF: '}{client['cnpj_cpf']}",
                S["signature"],
            ),
        ],
    ]
    sig_table = Table(sig_data, colWidths=[page_width/2, page_width/2])
    sig_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(sig_table)

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GOLD))
    story.append(Paragraph(
        f"{APP_NAME}  |  {ESCRITORIO.get('telefone', '')}  |  {ESCRITORIO.get('email', '')}",
        ParagraphStyle("footer", fontSize=7, alignment=TA_CENTER,
                       textColor=colors.HexColor("#7F8C8D")),
    ))

    doc.build(story)
    return output_path


def _default_contract_clauses(contract, client, S):
    story = []
    monthly_fee = contract.get("monthly_fee", 0) or 0
    due_day = contract.get("due_day", 5) or 5
    start_date = _fmt_date(contract.get("start_date", "")) or _fmt_date(contract.get("date", ""))

    clauses = [
        ("CLÁUSULA 1 – DO PRAZO",
         f"O presente contrato é de prazo indeterminado, com início em {start_date}."),

        ("CLÁUSULA 2 – DOS SERVIÇOS CONTRATADOS",
         "O CONTRATADO prestará ao CONTRATANTE os serviços contábeis, fiscais e de departamento pessoal "
         "conforme a necessidade e modalidade específica contratada, incluindo escrituração contábil, "
         "apuração de impostos, elaboração e entrega de declarações fiscais, obrigações acessórias, "
         "admissão e rescisão de funcionários, emissão de recibos de pagamento e encargos sociais."),

        ("CLÁUSULA 3 – DOS HONORÁRIOS",
         f"Os honorários mensais pelos serviços contratados ficam estipulados no valor de "
         f"<b>R$ {monthly_fee:,.2f}</b>".replace(",", "X").replace(".", ",").replace("X", ".") +
         f", com vencimento todo dia <b>{due_day:02d}</b> do mês subsequente ao da prestação dos serviços. "
         "O não pagamento na data do vencimento sujeitará o CONTRATANTE a multa moratória de 2% "
         "sobre o valor devido, acrescido de juros de 1% ao mês e correção monetária pelo índice oficial aplicável. "
         "Os honorários serão reajustados anualmente no mês de abril, com base na variação acumulada do INPC/IBGE."),

        ("CLÁUSULA 4 – DA INADIMPLÊNCIA",
         "O não pagamento de qualquer parcela dos honorários autoriza o CONTRATADO a suspender a prestação dos "
         "serviços e ingressar com ação judicial cabível para rescisão do contrato, cobrança dos valores devidos "
         "e reparação por perdas e danos, acrescidos dos encargos previstos."),

        ("CLÁUSULA 5 – DA ENTREGA DE DOCUMENTOS E INFORMAÇÕES",
         "A execução dos serviços dependerá da entrega, pelo CONTRATANTE, de todos os documentos, extratos "
         "bancários (PDF e OFX) e informações necessárias, até o dia 10 do mês subsequente. Penalidades, multas "
         "ou prejuízos decorrentes da omissão ou negligência do CONTRATANTE serão de sua exclusiva responsabilidade."),

        ("CLÁUSULA 6 – DA PARALISAÇÃO DAS ATIVIDADES",
         "Caso a empresa CONTRATANTE permaneça paralisada por mais de 3 (três) meses, será cobrada taxa "
         "equivalente a 50% dos honorários mensais, para manutenção das obrigações acessórias."),

        ("CLÁUSULA 7 – DOS ENCARGOS ANUAIS",
         "O CONTRATANTE pagará anualmente uma mensalidade extra referente à elaboração da DIRPJ/DEFIS, "
         "ressarcimento de despesas com impressos e encerramento do balanço anual."),

        ("CLÁUSULA 8 – DA RESCISÃO",
         "No caso de rescisão imotivada por qualquer das partes, será devida multa equivalente a 2 (duas) "
         "mensalidades. Após o aviso prévio, o CONTRATADO terá 30 dias para entrega de documentos fiscais e "
         "60 dias para entrega dos livros contábeis. O prazo de aviso prévio é de 60 (sessenta) dias."),

        ("CLÁUSULA 9 – DA PROTEÇÃO DE DADOS (LGPD)",
         "Em cumprimento à Lei nº 13.709/2018 (LGPD), as partes comprometem-se a tratar os dados pessoais "
         "obtidos em razão deste contrato com responsabilidade, segurança e finalidade específica, não "
         "compartilhando-os com terceiros, salvo nos casos exigidos por lei ou por órgãos fiscalizadores."),

        ("CLÁUSULA 10 – DO FORO",
         f"Fica eleito o foro da Comarca de {ESCRITORIO.get('cidade', '')}/{ESCRITORIO.get('estado', '')}, "
         "domicílio do CONTRATADO, para dirimir quaisquer controvérsias oriundas do presente contrato, "
         "com renúncia expressa a qualquer outro, por mais privilegiado que seja."),
    ]

    for title, text in clauses:
        story.append(Paragraph(title, S["clause_title"]))
        story.append(Paragraph(text, S["body"]))
        story.append(Spacer(1, 4))

    return story


def _fmt_date(d: str) -> str:
    if not d:
        return ""
    try:
        return datetime.strptime(d[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return d


def _fmt_client_address(client) -> str:
    parts = []
    if client.get("address"):
        addr = client["address"]
        if client.get("number"):
            addr += f", nº {client['number']}"
        if client.get("complement"):
            addr += f", {client['complement']}"
        parts.append(addr)
    if client.get("neighborhood"):
        parts.append(client["neighborhood"])
    if client.get("city"):
        parts.append(f"{client['city']}/{client.get('state', '')}")
    if client.get("zip_code"):
        parts.append(f"CEP {client['zip_code']}")
    return ", ".join(parts) if parts else "endereço não informado"
