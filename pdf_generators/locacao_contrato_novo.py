"""
Gerador de PDF de Locação independente

Gera o PDF completo usando apenas ReportLab, sem depender de DOCX ou PDF base.
"""

from __future__ import annotations

import os
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm

from assets.filiais.filiais_config import obter_filial


def _as_decimal(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    try:
        if value is None:
            return default
        if isinstance(value, (int, float, Decimal)):
            return Decimal(str(value))
        # Strings como "R$ 1.234,56"
        s = str(value).replace('R$', '').replace('.', '').replace(',', '.')
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return default


def _format_currency(value: Decimal, currency: str = "BRL") -> str:
    quant = value.quantize(Decimal("0.01"))
    if currency.upper() == "BRL":
        return f"R$ {quant:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"{currency} {quant:,.2f}"


def _resolve_image_path(path: str | None) -> str | None:
    if not path:
        return None
    if os.path.isabs(path):
        return path if os.path.exists(path) else None
    p = os.path.join(os.getcwd(), path)
    return p if os.path.exists(p) else None


def _build_header_filial(dados: Dict[str, Any]):
    filial = obter_filial(dados.get('filial_id') or 2) or {}
    nome = filial.get('nome', '')
    endereco = filial.get('endereco', '')
    cnpj = filial.get('cnpj', '')
    telefones = filial.get('telefones', '')
    email = filial.get('email', '')
    logo_path = _resolve_image_path(filial.get('logo_path'))
    return nome, endereco, cnpj, telefones, email, logo_path


def _default_apresentacao(dados: Dict[str, Any]) -> str:
    equip = dados.get('equipamento_titulo') or (
        f"compressor {dados.get('marca') or ''} {dados.get('modelo') or ''}".strip()
    ) or "equipamento"
    cliente = dados.get('cliente_nome') or "CLIENTE"
    return (
        f"Prezados Senhores, referente à locação de {equip}.\n\n"
        f"Apresentamos nossa proposta de contrato de locação para {cliente}, com as condições e itens "
        f"detalhados a seguir. Estamos à disposição para quaisquer esclarecimentos."
    )


def gerar_pdf_locacao(dados: Dict[str, Any], output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleCenter", parent=styles['Title'], alignment=1))
    styles.add(ParagraphStyle(name="Header", parent=styles['Heading2'], spaceAfter=6))
    styles.add(ParagraphStyle(name="Small", parent=styles['Normal'], fontSize=9, leading=12))
    styles.add(ParagraphStyle(name="NormalJust", parent=styles['Normal'], alignment=4))

    nome, endereco, cnpj, telefones, email, logo_path = _build_header_filial(dados)

    story: List[Any] = []

    # Cabeçalho
    if logo_path:
        try:
            img = Image(logo_path, width=4.5*cm, height=2.0*cm)
            story.append(img)
        except Exception:
            pass
    story.append(Paragraph(nome or "", styles['Header']))
    if endereco:
        story.append(Paragraph(endereco, styles['Small']))
    linha2 = " ".join([f"CNPJ: {cnpj}" if cnpj else '', telefones or '', email or '']).strip()
    if linha2:
        story.append(Paragraph(linha2, styles['Small']))
    story.append(Spacer(1, 0.6*cm))

    # Título
    numero = dados.get('numero') or ''
    cliente_nome = (dados.get('cliente_nome') or '').replace('_', ' ')
    story.append(Paragraph("Contrato de Locação", styles['TitleCenter']))
    title_info = []
    if numero:
        title_info.append(f"Proposta Nº: {numero}")
    if cliente_nome:
        title_info.append(f"Cliente: {cliente_nome}")
    if title_info:
        story.append(Paragraph(" | ".join(title_info), styles['Normal']))
    story.append(Spacer(1, 0.4*cm))

    # Apresentação / Prezados
    prezados = dados.get('prezados_linha')
    apresentacao = (dados.get('apresentacao_texto') or '').strip()
    if not apresentacao:
        apresentacao = _default_apresentacao(dados)
    if prezados:
        story.append(Paragraph(prezados, styles['Normal']))
        story.append(Spacer(1, 0.2*cm))
    for para in apresentacao.split("\n\n"):
        story.append(Paragraph(para, styles['NormalJust']))
        story.append(Spacer(1, 0.2*cm))

    story.append(Spacer(1, 0.4*cm))

    # Dados do equipamento
    marca = dados.get('marca') or ''
    modelo = dados.get('modelo') or ''
    serie = dados.get('serie') or ''
    equip_title = dados.get('equipamento_titulo') or 'Equipamento'
    story.append(Paragraph(equip_title, styles['Heading3']))
    eq_lines = []
    if marca:
        eq_lines.append(f"Marca: {marca}")
    if modelo:
        eq_lines.append(f"Modelo: {modelo}")
    if serie:
        eq_lines.append(f"Nº de Série: {serie}")
    if eq_lines:
        story.append(Paragraph(" | ".join(eq_lines), styles['Normal']))

    img_comp = _resolve_image_path(dados.get('imagem_compressor')) or logo_path
    if img_comp and os.path.exists(img_comp):
        try:
            story.append(Spacer(1, 0.2*cm))
            story.append(Image(img_comp, width=12*cm, height=7*cm))
        except Exception:
            pass

    story.append(Spacer(1, 0.5*cm))

    # Tabela de itens
    itens: List[Dict[str, Any]] = list(dados.get('itens') or [])
    tabela_data: List[List[Any]] = [[
        'Quantidade', 'Descrição', 'Valor mensal', 'Início', 'Fim', 'Período'
    ]]
    total_mensal = Decimal('0')
    for it in itens:
        qtd = str(it.get('quantidade') or '')
        desc = str(it.get('descricao') or '')
        val_dec = _as_decimal(it.get('valor_unitario'))
        total_mensal += val_dec
        val = _format_currency(val_dec, dados.get('moeda') or 'BRL') if val_dec else ''
        di = str(it.get('inicio') or '')
        df = str(it.get('fim') or '')
        per = str(it.get('periodo') or '')
        tabela_data.append([qtd, desc, val, di, df, per])

    if len(tabela_data) > 1:
        tbl = Table(
            tabela_data,
            colWidths=[2*cm, 7*cm, 3*cm, 2.2*cm, 2.2*cm, 2.2*cm]
        )
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#efefef')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.black),
            ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
            ('ALIGN', (0,0), (0,-1), 'CENTER'),
            ('ALIGN', (2,1), (2,-1), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 0.2*cm))

    # Valor mensal total
    valor_mensal = dados.get('valor_mensal')
    if not valor_mensal:
        valor_mensal = total_mensal
    valor_mensal_dec = _as_decimal(valor_mensal)
    if valor_mensal_dec > 0:
        story.append(Paragraph(
            f"Valor mensal total: <b>{_format_currency(valor_mensal_dec, dados.get('moeda') or 'BRL')}</b>",
            styles['Normal']
        ))

    story.append(Spacer(1, 0.4*cm))

    # Condições de pagamento
    condicoes = dados.get('condicoes_pagamento')
    if not condicoes:
        dia = dados.get('vencimento_dia') or '10'
        condicoes = f"A vencimento de cada mensalidade, todo dia {dia}, conforme proposta acordada com o cliente."
    story.append(Paragraph("Condições de Pagamento", styles['Heading3']))
    story.append(Paragraph(condicoes, styles['NormalJust']))

    story.append(Spacer(1, 0.4*cm))

    # Termos finais / rodapé de identificação
    termos = [
        f"Filial: {nome}" if nome else '',
        f"Locatária: {cliente_nome}" if cliente_nome else '',
        f"Nº da Proposta: {numero}" if numero else '',
    ]
    story.append(Paragraph("Informações", styles['Heading3']))
    for t in termos:
        if t:
            story.append(Paragraph(t, styles['Normal']))

    story.append(Spacer(1, 0.6*cm))
    story.append(Paragraph(
        "Assinaturas:\n\n____________________________________\nLocadora\n\n\n____________________________________\nLocatária",
        styles['Normal']
    ))

    # Construir documento
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm,
        title=f"Contrato de Locação {numero}",
        author=nome or ""
    )
    doc.build(story)


__all__ = ["gerar_pdf_locacao"]

