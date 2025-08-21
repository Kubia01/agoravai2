"""
Gerador de PDF de Locação independente

- Desenha cabeçalho e rodapé com faixa azul, logo e dados dinâmicos da filial
- Reproduz o layout do PDF de exemplo usando LAYOUT_SPEC extraído (sem depender do PDF em runtime)
- Sobrepõe campos dinâmicos por página (ex.: pág. 2 prezados, pág. 4/7 imagem, pág. 6 condições, pág. 7 termos)
- Fallback para gerador programático caso LAYOUT_SPEC não esteja disponível
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
from reportlab.pdfbase import pdfmetrics

from assets.filiais.filiais_config import obter_filial
try:
    from assets.layouts.locacao_layout_data import LAYOUT_SPEC  # auto-gerado
except Exception:
    LAYOUT_SPEC = None


# ========= Helpers =========

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


def _build_filial(dados: Dict[str, Any]) -> Dict[str, Any]:
    filial = obter_filial(dados.get('filial_id') or 2) or {}
    return {
        'nome': filial.get('nome', ''),
        'endereco': filial.get('endereco', ''),
        'cnpj': filial.get('cnpj', ''),
        'telefones': filial.get('telefones', ''),
        'email': filial.get('email', ''),
        'logo_path': _resolve_image_path(filial.get('logo_path')),
    }


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


def _draw_wrapped_text(canvas, text: str, x: float, y: float, max_width: float, line_height: float, font: str = 'Helvetica', size: float = 11):
    if not text:
        return
    canvas.saveState()
    try:
        canvas.setFont(font, size)
    except Exception:
        canvas.setFont('Helvetica', size)
    words = text.split()
    line = ''
    lines: List[str] = []
    for w in words:
        candidate = (line + ' ' + w).strip()
        if pdfmetrics.stringWidth(candidate, font, size) <= max_width or not line:
            line = candidate
        else:
            lines.append(line)
            line = w
    if line:
        lines.append(line)
    ty = y
    for ln in lines:
        canvas.drawString(x, ty, ln)
        ty -= line_height
    canvas.restoreState()


# ========= Gerador =========

def gerar_pdf_locacao(dados: Dict[str, Any], output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleCenter", parent=styles['Title'], alignment=1))
    styles.add(ParagraphStyle(name="Header", parent=styles['Heading2'], spaceAfter=6))
    styles.add(ParagraphStyle(name="Small", parent=styles['Normal'], fontSize=9, leading=12))
    styles.add(ParagraphStyle(name="NormalJust", parent=styles['Normal'], alignment=4))

    filial = _build_filial(dados)

    # Fallback content (se LAYOUT_SPEC não existir)
    story: List[Any] = []

    header_block: List[Any] = []
    if filial['logo_path']:
        try:
            header_block.append(Image(filial['logo_path'], width=4.5*cm, height=2.0*cm))
        except Exception:
            pass
    header_block.append(Paragraph(filial['nome'] or "", styles['Header']))
    if filial['endereco']:
        header_block.append(Paragraph(filial['endereco'], styles['Small']))
    linha2 = " ".join([
        f"CNPJ: {filial['cnpj']}" if filial['cnpj'] else '',
        filial['telefones'] or '',
        filial['email'] or '',
    ]).strip()
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
    apresentacao = (dados.get('apresentacao_texto') or '').strip() or _default_apresentacao(dados)
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

    img_comp = _resolve_image_path(dados.get('imagem_compressor')) or filial['logo_path']
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

    valor_mensal = dados.get('valor_mensal') or total_mensal
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
        f"Filial: {filial['nome']}" if filial['nome'] else '',
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

    # ========== Layout-based rendering ==========
    PAGE_WIDTH, PAGE_HEIGHT = A4

    if LAYOUT_SPEC and LAYOUT_SPEC.get('pages'):
        header_h = 40
        footer_h = 30

        def _draw_header_footer(canvas, page_num: int):
            # Header: faixa azul, logo, nome, cnpj
            canvas.saveState()
            # Faixa
            canvas.setFillColor(colors.HexColor('#005B99'))
            canvas.rect(0, PAGE_HEIGHT - header_h, PAGE_WIDTH, header_h, stroke=0, fill=1)
            # Linha base da faixa
            canvas.setStrokeColor(colors.HexColor('#004A7A'))
            canvas.setLineWidth(0.6)
            canvas.line(0, PAGE_HEIGHT - header_h, PAGE_WIDTH, PAGE_HEIGHT - header_h)
            # Logo
            if filial['logo_path'] and os.path.exists(filial['logo_path']):
                try:
                    logo_w, logo_h = 90, 26
                    canvas.drawImage(filial['logo_path'], 1.0*cm, PAGE_HEIGHT - header_h + (header_h-logo_h)/2, width=logo_w, height=logo_h, preserveAspectRatio=True, mask='auto')
                except Exception:
                    pass
            # Título/nome
            canvas.setFillColor(colors.white)
            try:
                canvas.setFont('Helvetica-Bold', 11)
            except Exception:
                canvas.setFont('Helvetica', 11)
            canvas.drawString(4.5*cm, PAGE_HEIGHT - 26, filial['nome'] or ' ')
            # Número da página (topo à direita)
            canvas.setFont('Helvetica', 8)
            canvas.drawRightString(PAGE_WIDTH - 1.0*cm, PAGE_HEIGHT - 24, f"Página {page_num}")

            # Footer: linha e dados de contato
            canvas.setStrokeColor(colors.HexColor('#d0d0d0'))
            canvas.setLineWidth(0.7)
            canvas.line(1.5*cm, footer_h, PAGE_WIDTH - 1.5*cm, footer_h)
            canvas.setFillColor(colors.HexColor('#666666'))
            canvas.setFont('Helvetica', 8)
            footer_left = filial['endereco'] or ''
            footer_right = " | ".join([p for p in [filial['telefones'] or '', filial['email'] or ''] if p])
            if footer_left:
                canvas.drawString(1.5*cm, footer_h - 12, footer_left)
            if footer_right:
                canvas.drawRightString(PAGE_WIDTH - 1.5*cm, footer_h - 12, footer_right)
            canvas.restoreState()

        def _draw_layout_page(canvas, doc):
            page_index = (doc.page or 1) - 1
            _draw_header_footer(canvas, doc.page)
            # Desenhar textos estáticos do layout
            items = LAYOUT_SPEC['pages'][page_index].get('items', []) if 0 <= page_index < len(LAYOUT_SPEC.get('pages', [])) else []
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

            # Dynamic overlays per page
            from datetime import date
            # Comuns
            _write_after(["Cliente:"], dados.get('cliente_nome'))
            _write_after(["A/C", "A/C :"], dados.get('contato'))
            _write_after(["Data:"], dados.get('data_inicio') or date.today().strftime('%d/%m/%Y'))
            _write_after(["NÚMERO:", "NUMERO:"], dados.get('numero'))

            # Página 2 (index 1): Prezados + apresentação texto
            if page_index == 1:
                prez = (dados.get('prezados_linha') or 'Prezados Senhores:')
                ap = (dados.get('apresentacao_texto') or '').strip() or _default_apresentacao(dados)
                # Encontrar base após REF ou usar coordenadas padrão
                base_y = 660.0
                for it in items:
                    if (it.get('text') or '').strip().upper().startswith('REF'):
                        base_y = float(it.get('y0', base_y)) - 16
                        break
                _draw_wrapped_text(canvas, prez, 72, base_y, max_width=PAGE_WIDTH-144, line_height=14, font='Helvetica-Bold', size=11)
                _draw_wrapped_text(canvas, ap, 72, base_y-18, max_width=PAGE_WIDTH-144, line_height=13, font='Helvetica', size=10)

            # Página 4 (index 3): desenho do compressor (por marca/logo)
            if page_index == 3:
                img_path = _resolve_image_path(dados.get('imagem_compressor')) or filial['logo_path']
                if img_path and os.path.exists(img_path):
                    try:
                        canvas.drawImage(img_path, 60, 420, width=470, height=300, preserveAspectRatio=True, mask='auto')
                    except Exception:
                        pass

            # Página 6 (index 5): condições de pagamento
            if page_index == 5:
                cond = (dados.get('condicoes_pagamento') or '').strip()
                if not cond:
                    dia = dados.get('vencimento_dia') or '10'
                    cond = f"A vencimento de cada mensalidade, todo dia {dia}, conforme proposta acordada com o cliente."
                _draw_wrapped_text(canvas, cond, 72, 700, max_width=PAGE_WIDTH-144, line_height=13, font='Helvetica', size=10)

            # Página 7 (index 6): termos finais + imagem por marca
            if page_index == 6:
                # Termos
                termos_lines = [
                    f"Filial: {filial['nome']}" if filial['nome'] else '',
                    f"Locatária: {(dados.get('cliente_nome') or '').replace('_',' ')}" if dados.get('cliente_nome') else '',
                    f"Nº da Proposta: {dados.get('numero') or ''}",
                ]
                yy = 700
                for line in termos_lines:
                    if line:
                        _draw_wrapped_text(canvas, line, 72, yy, max_width=PAGE_WIDTH-144, line_height=14, font='Helvetica', size=11)
                        yy -= 16
                # Imagem
                img_path = _resolve_image_path(dados.get('imagem_compressor')) or filial['logo_path']
                if img_path and os.path.exists(img_path):
                    try:
                        canvas.drawImage(img_path, 60, 420, width=200, height=130, preserveAspectRatio=True, mask='auto')
                    except Exception:
                        pass

        # Template que só usa páginas vazias para acionar o onPage
        frame = Frame(1*cm, 1.8*cm, PAGE_WIDTH-2*cm, PAGE_HEIGHT-3.6*cm, id='layout_frame')
        template = PageTemplate(id='layout', frames=[frame], onPage=_draw_layout_page)
        doc = BaseDocTemplate(
            output_path,
            pagesize=A4,
            title=f"Contrato de Locação {numero}",
            author=filial['nome'] or "",
            pageTemplates=[template]
        )
        # Cria tantas páginas quanto o layout
        story_pages: List[Any] = []
        for _ in LAYOUT_SPEC['pages']:
            story_pages.append(Spacer(0, 0.1*cm))
            story_pages.append(PageBreak())
        if story_pages:
            story_pages.pop()
        doc.build(story_pages)
        return

    # ========== Fallback programático (sem LAYOUT_SPEC) ==========
    def draw_header(canvas, doc):
        canvas.saveState()
        # Faixa azul
        canvas.setFillColor(colors.HexColor('#005B99'))
        canvas.rect(0, PAGE_HEIGHT-40, PAGE_WIDTH, 40, stroke=0, fill=1)
        canvas.setFillColor(colors.white)
        try:
            canvas.setFont('Helvetica-Bold', 11)
        except Exception:
            canvas.setFont('Helvetica', 11)
        canvas.drawString(2*cm, PAGE_HEIGHT-26, filial['nome'] or '')
        canvas.setFont('Helvetica', 8)
        canvas.drawRightString(PAGE_WIDTH-1.0*cm, PAGE_HEIGHT-24, f"Página {doc.page}")
        canvas.restoreState()

    def draw_footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor('#d0d0d0'))
        canvas.setLineWidth(0.7)
        canvas.line(1.5*cm, 1.6*cm, PAGE_WIDTH-1.5*cm, 1.6*cm)
        canvas.setFillColor(colors.HexColor('#666666'))
        canvas.setFont('Helvetica', 8)
        footer_left = filial['endereco'] or ''
        footer_right = " | ".join([p for p in [filial['telefones'] or '', filial['email'] or ''] if p])
        if footer_left:
            canvas.drawString(1.5*cm, 1.1*cm, footer_left)
        if footer_right:
            canvas.drawRightString(PAGE_WIDTH-1.5*cm, 1.1*cm, footer_right)
        canvas.restoreState()

    frame = Frame(2*cm, 2.1*cm, PAGE_WIDTH-4*cm, PAGE_HEIGHT-4.2*cm, id='normal')
    template = PageTemplate(id='tpl', frames=[frame], onPage=draw_header, onPageEnd=draw_footer)
    doc = BaseDocTemplate(
        output_path,
        pagesize=A4,
        title=f"Contrato de Locação {numero}",
        author=filial['nome'] or "",
        pageTemplates=[template]
    )

    doc.build(story)


__all__ = ["gerar_pdf_locacao"]