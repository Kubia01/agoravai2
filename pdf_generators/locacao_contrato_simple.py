from __future__ import annotations

import os
from typing import Any, Dict, List

from reportlab.lib.pagesizes import A4
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm

from assets.filiais.filiais_config import obter_filial


def _resolve_image_path(path: str | None) -> str | None:
    if not path:
        return None
    if os.path.isabs(path):
        return path if os.path.exists(path) else None
    p = os.path.join(os.getcwd(), path)
    return p if os.path.exists(p) else None


def _build_filial(dados: Dict[str, Any]) -> Dict[str, Any]:
    filial = obter_filial(dados.get('filial_id') or 2) or {}
    return {
        'nome': filial.get('nome', ''),
        'endereco': filial.get('endereco', ''),
        'cep': filial.get('cep', ''),
        'cnpj': filial.get('cnpj', ''),
        'ie': filial.get('inscricao_estadual', ''),
        'telefones': filial.get('telefones', ''),
        'email': filial.get('email', ''),
        'site': filial.get('site', ''),
        'logo_path': _resolve_image_path(filial.get('logo_path')),
    }


def _draw_header(canvas, doc, filial):
    PAGE_WIDTH, PAGE_HEIGHT = A4
    canvas.saveState()
    # Barra azul topo
    canvas.setFillColor(colors.HexColor('#005B99'))
    canvas.rect(0, PAGE_HEIGHT - 72, PAGE_WIDTH, 72, stroke=0, fill=1)
    # Logo
    if filial['logo_path'] and os.path.exists(filial['logo_path']):
        try:
            canvas.drawImage(filial['logo_path'], 1.2*cm, PAGE_HEIGHT - 62, width=110, height=36, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
    # Textos
    canvas.setFillColor(colors.white)
    try:
        canvas.setFont('Helvetica-Bold', 10.5)
    except Exception:
        canvas.setFont('Helvetica', 10.5)
    canvas.drawString(4.8*cm, PAGE_HEIGHT - 24, filial['nome'] or ' ')
    if filial['endereco']:
        canvas.setFont('Helvetica', 8.5)
        endereco_completo = filial['endereco'] + (f" - CEP {filial['cep']}" if filial.get('cep') else '')
        canvas.drawString(4.8*cm, PAGE_HEIGHT - 38, endereco_completo)
    canvas.setFont('Helvetica', 8)
    canvas.drawRightString(PAGE_WIDTH - 1.0*cm, PAGE_HEIGHT - 24, f"Página {doc.page}")
    canvas.restoreState()


def _draw_footer(canvas, doc, filial):
    PAGE_WIDTH, PAGE_HEIGHT = A4
    canvas.saveState()
    # Barra azul inferior
    canvas.setFillColor(colors.HexColor('#005B99'))
    canvas.rect(0, 0, PAGE_WIDTH, 60, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont('Helvetica', 8.5)
    left = " | ".join([p for p in [f"CNPJ: {filial['cnpj']}" if filial['cnpj'] else '', f"IE: {filial['ie']}" if filial['ie'] else ''] if p])
    right_parts = [filial['telefones'] or '', filial['email'] or '']
    if filial['site']:
        right_parts.append(filial['site'])
    right = " | ".join([p for p in right_parts if p])
    if left:
        canvas.drawString(1.5*cm, 16, left)
    if right:
        canvas.drawRightString(PAGE_WIDTH - 1.5*cm, 16, right)
    canvas.restoreState()


def gerar_pdf_locacao(dados: Dict[str, Any], output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    filial = _build_filial(dados)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleCenter", parent=styles['Title'], alignment=1))
    styles.add(ParagraphStyle(name="Small", parent=styles['Normal'], fontSize=9, leading=12))
    styles.add(ParagraphStyle(name="NormalJust", parent=styles['Normal'], alignment=4))
    styles.add(ParagraphStyle(name="Header", parent=styles['Heading2'], spaceAfter=6))

    PAGE_WIDTH, PAGE_HEIGHT = A4
    frame = Frame(2*cm, 2.6*cm, PAGE_WIDTH-4*cm, PAGE_HEIGHT-6.2*cm, id='frame')

    def on_page(canvas, doc):
        # primeira página sem header/footer conforme instrução; demais com header/footer
        if doc.page == 1:
            return
        _draw_header(canvas, doc, filial)
        _draw_footer(canvas, doc, filial)

    template = PageTemplate(id='tpl', frames=[frame], onPage=on_page)

    doc = BaseDocTemplate(
        output_path,
        pagesize=A4,
        title=f"Locação {dados.get('numero') or ''}",
        author=filial['nome'] or "",
        pageTemplates=[template]
    )

    story: List[Any] = []

    # Página 1 (capa simplificada apenas para placeholder)
    if filial['logo_path']:
        try:
            story.append(Image(filial['logo_path'], width=6*cm, height=3*cm))
        except Exception:
            pass
    story.append(Spacer(1, 1.0*cm))
    story.append(Paragraph("Proposta de Locação", styles['TitleCenter']))
    story.append(Spacer(1, 0.5*cm))
    numero = dados.get('numero') or ''
    cliente_nome = (dados.get('cliente_nome') or 'CLIENTE')
    story.append(Paragraph(f"Número: {numero}", styles['Normal']))
    story.append(Paragraph(f"Cliente: {cliente_nome}", styles['Normal']))

    # Página 2: bloco superior e apresentação
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph("PROPOSTA COMERCIAL", styles['Normal']))
    story.append(Paragraph("REF: CONTRATO DE LOCAÇÃO", styles['Normal']))
    story.append(Paragraph(f"NÚMERO: {numero}", styles['Normal']))
    from datetime import date
    story.append(Paragraph(f"DATA: {dados.get('data_inicio') or date.today().strftime('%d/%m/%Y')}", styles['Normal']))
    story.append(Spacer(1, 0.6*cm))
    prez = (dados.get('prezados_linha') or 'Prezados Senhores:')
    ap = (dados.get('apresentacao_texto') or '').strip() or (
        "Agradecemos por nos conceder a oportunidade de apresentarmos nossa proposta para fornecimento de LOCAÇÃO DE COMPRESSOR DE AR.\n"
        "A World Comp Compressores é especializada em manutenção de compressores de parafuso das principais marcas do mercado, como Atlas Copco, Ingersoll Rand, Chicago.\n"
        "Atuamos também com revisão de equipamentos e unidades compressoras, venda de peças, bem como venda e locação de compressores de parafuso isentos de óleo e lubrificados.\n"
        "Com profissionais altamente qualificados e atendimento especializado, colocamo-nos à disposição para analisar, corrigir e prestar os devidos esclarecimentos, sempre buscando atender às especificações e necessidades dos nossos clientes."
    )
    story.append(Paragraph(prez, styles['Normal']))
    for para in ap.split("\n"):
        if para.strip():
            story.append(Paragraph(para, styles['NormalJust']))
            story.append(Spacer(1, 0.2*cm))

    # Página 3: placeholder texto fixo
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("Página 3 - Conteúdo fixo conforme modelo (placeholder)", styles['Normal']))

    # Página 4: título do compressor e imagem
    equip_title = (dados.get('equipamento_titulo') or 'COMPRESSOR DE PARAFUSO LUBRIFICADO REFRIGERADO À AR').upper()
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(equip_title, styles['Header']))
    img_path = _resolve_image_path(dados.get('imagem_compressor')) or filial['logo_path']
    if img_path and os.path.exists(img_path):
        try:
            story.append(Image(img_path, width=15*cm, height=9*cm))
        except Exception:
            pass

    doc.build(story)


__all__ = ["gerar_pdf_locacao"]

