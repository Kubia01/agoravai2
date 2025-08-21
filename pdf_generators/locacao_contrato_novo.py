"""
Gerador de PDF de Locação independente

Gera o PDF completo usando apenas ReportLab, sem depender de DOCX ou PDF base.
Se houver um LAYOUT_SPEC extraído do PDF de exemplo, usa esse layout
para posicionar textos estáticos e campos dinâmicos por coordenadas.
"""

from __future__ import annotations

import os
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    BaseDocTemplate,
    PageTemplate,
    Frame,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    KeepTogether,
    PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm

from assets.filiais.filiais_config import obter_filial
try:
    from assets.layouts.locacao_layout_data import LAYOUT_SPEC  # auto-gerado
except Exception:
    LAYOUT_SPEC = None


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

    # Conteúdo programático (fallback)
    story: List[Any] = []

    header_block: List[Any] = []
    if logo_path:
        try:
            header_block.append(Image(logo_path, width=4.5*cm, height=2.0*cm))
        except Exception:
            pass
    header_block.append(Paragraph(nome or "", styles['Header']))
    if endereco:
        header_block.append(Paragraph(endereco, styles['Small']))
    linha2 = " ".join([f"CNPJ: {cnpj}" if cnpj else '', telefones or '', email or '']).strip()
    if linha2:
        header_block.append(Paragraph(linha2, styles['Small']))
    header_block.append(Spacer(1, 0.4*cm))
    story.extend(header_block)

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
        story.append(KeepTogether([tbl, Spacer(1, 0.2*cm)]))

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

    condicoes = dados.get('condicoes_pagamento')
    if not condicoes:
        dia = dados.get('vencimento_dia') or '10'
        condicoes = f"A vencimento de cada mensalidade, todo dia {dia}, conforme proposta acordada com o cliente."
    story.append(Paragraph("Condições de Pagamento", styles['Heading3']))
    story.append(Paragraph(condicoes, styles['NormalJust']))

    story.append(Spacer(1, 0.4*cm))

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

    # Construção com layout extraído se disponível; caso contrário, usar composição programática
    PAGE_WIDTH, PAGE_HEIGHT = A4

    if LAYOUT_SPEC and LAYOUT_SPEC.get('pages'):
        def _draw_layout_page(canvas, doc):
            page_index = (doc.page or 1) - 1
            # Cabeçalho e rodapé simples
            canvas.saveState()
            # Faixa azul do cabeçalho
            canvas.setFillColor(colors.HexColor('#005B99'))
            canvas.rect(0, PAGE_HEIGHT-40, PAGE_WIDTH, 40, stroke=0, fill=1)
            # Linha sutil
            canvas.setStrokeColor(colors.HexColor('#004A7A'))
            canvas.setLineWidth(0.6)
            canvas.line(0, PAGE_HEIGHT-40, PAGE_WIDTH, PAGE_HEIGHT-40)
            canvas.line(2*cm, 1.6*cm, PAGE_WIDTH-2*cm, 1.6*cm)
            canvas.setFont('Helvetica', 8)
            canvas.setFillColor(colors.white)
            # Número da página no topo à direita dentro da faixa
            canvas.drawRightString(PAGE_WIDTH-1.0*cm, PAGE_HEIGHT-27, f"Página {doc.page}")
            # Rodapé com linha e texto
            canvas.setFillColor(colors.HexColor('#666666'))
            canvas.setStrokeColor(colors.HexColor('#d0d0d0'))
            if nome:
                canvas.drawString(2*cm, 1.1*cm, nome)
            canvas.restoreState()

            # Desenhar textos estáticos do layout
            if 0 <= page_index < len(LAYOUT_SPEC.get('pages', [])):
                items = LAYOUT_SPEC['pages'][page_index].get('items', [])
                for it in items:
                    txt = it.get('text', '')
                    size = it.get('size') or 10
                    font = it.get('font') or 'Helvetica'
                    x0 = float(it.get('x0', 0))
                    y0 = float(it.get('y0', 0))
                    if not txt.strip():
                        continue
                    canvas.saveState()
                    try:
                        canvas.setFont(font, size)
                    except Exception:
                        canvas.setFont('Helvetica', size)
                    canvas.setFillColor(colors.black)
                    canvas.drawString(x0, y0, txt)
                    canvas.restoreState()

                # Campos dinâmicos posicionados logo após labels conhecidas
                def _write_after(label_prefixes, value, default_size=10, dx=4):
                    if not value:
                        return
                    for it in items:
                        raw = (it.get('text') or '').strip()
                        if any(raw.startswith(lp) for lp in label_prefixes):
                            size = it.get('size') or default_size
                            x1 = float(it.get('x1', it.get('x0', 0)))
                            y0 = float(it.get('y0', 0))
                            canvas.saveState()
                            canvas.setFont('Helvetica', size)
                            canvas.drawString(x1 + dx, y0, str(value))
                            canvas.restoreState()
                            break

                from datetime import date
                _write_after(["Cliente:"], dados.get('cliente_nome'))
                _write_after(["A/C", "A/C :"], dados.get('contato'))
                _write_after(["Data:"], dados.get('data_inicio') or date.today().strftime('%d/%m/%Y'))
                _write_after(["NÚMERO:", "NUMERO:"], dados.get('numero'))

                vm = _as_decimal(dados.get('valor_mensal') or 0)
                if vm > 0:
                    _write_after(["VALOR MENSAL", "VALOR TOTAL", "VALOR MENSAL TOTAL"], _format_currency(vm, dados.get('moeda') or 'BRL'))

                condicoes = dados.get('condicoes_pagamento')
                if not condicoes:
                    dia = dados.get('vencimento_dia') or '10'
                    condicoes = f"A vencimento de cada mensalidade, todo dia {dia}, conforme proposta acordada com o cliente."
                _write_after(["CONDIÇÕES DE PAGAMENTO", "CONDICOES DE PAGAMENTO"], condicoes, default_size=9, dx=6)

                _write_after(["MARCA", "Marca"], dados.get('marca'))
                _write_after(["MODELO", "Modelo"], dados.get('modelo'))
                _write_after(["SÉRIE", "SERIE"], dados.get('serie'))

        frame = Frame(1*cm, 1.8*cm, PAGE_WIDTH-2*cm, PAGE_HEIGHT-3.6*cm, id='layout_frame')
        template = PageTemplate(id='layout', frames=[frame], onPage=_draw_layout_page)
        doc = BaseDocTemplate(
            output_path,
            pagesize=A4,
            title=f"Contrato de Locação {numero}",
            author=nome or "",
            pageTemplates=[template]
        )
        # Cria tantas páginas quanto o layout, não usa story de conteúdo
        story_pages: List[Any] = []
        for _ in LAYOUT_SPEC['pages']:
            story_pages.append(Spacer(0, 0.1*cm))
            story_pages.append(PageBreak())
        if story_pages:
            story_pages.pop()
        doc.build(story_pages)
        return

    # Fallback programático
    def draw_header(canvas, doc):
        canvas.saveState()
        # Linha superior
        canvas.setStrokeColor(colors.HexColor('#d0d0d0'))
        canvas.setLineWidth(0.7)
        canvas.line(2*cm, PAGE_HEIGHT-1.2*cm, PAGE_WIDTH-2*cm, PAGE_HEIGHT-1.2*cm)
        # Título pequeno no topo à direita
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#666666'))
        canvas.drawRightString(PAGE_WIDTH-2*cm, PAGE_HEIGHT-1.0*cm, 'Contrato de Locação')
        canvas.restoreState()

    def draw_footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor('#d0d0d0'))
        canvas.setLineWidth(0.7)
        canvas.line(2*cm, 1.6*cm, PAGE_WIDTH-2*cm, 1.6*cm)
        # Numeração de páginas: Página X de Y
        page_num = doc.page
        try:
            total = doc.page_count  # set later by multi-pass build
        except Exception:
            total = None
        canvas.setFont('Helvetica', 9)
        txt = f"Página {page_num}"
        if total:
            txt += f" de {total}"
        canvas.drawRightString(PAGE_WIDTH-2*cm, 1.1*cm, txt)
        # Rodapé com empresa
        if nome:
            canvas.setFont('Helvetica', 8)
            canvas.setFillColor(colors.HexColor('#666666'))
            canvas.drawString(2*cm, 1.1*cm, nome)
        canvas.restoreState()

    frame = Frame(2*cm, 2.1*cm, PAGE_WIDTH-4*cm, PAGE_HEIGHT-4.2*cm, id='normal')
    template = PageTemplate(id='tpl', frames=[frame], onPage=draw_header, onPageEnd=draw_footer)
    doc = BaseDocTemplate(
        output_path,
        pagesize=A4,
        title=f"Contrato de Locação {numero}",
        author=nome or "",
        pageTemplates=[template]
    )

    doc.build(story)


__all__ = ["gerar_pdf_locacao"]