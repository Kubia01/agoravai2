import os
import unicodedata
from datetime import datetime

# Dependências de PDF
from assets.filiais.filiais_config import obter_filial

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from PyPDF2 import PdfReader, PdfWriter
    ADVANCED_PDF_AVAILABLE = True
except Exception:
    ADVANCED_PDF_AVAILABLE = False

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except Exception:
    FPDF_AVAILABLE = False


def _clean_text(text: object) -> str:
    if text is None:
        return ""
    return str(text).replace("\t", "    ")


def _slugify(value: object) -> str:
    if not value:
        return ""
    value = unicodedata.normalize('NFKD', str(value))
    value = ''.join(c for c in value if not unicodedata.combining(c))
    value = value.lower().replace(' ', '-')
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789-_"
    return ''.join(c for c in value if c in allowed)


def _string_width(text: str, font_name: str, font_size: int) -> float:
    try:
        return pdfmetrics.stringWidth(text, font_name, font_size)
    except Exception:
        # Fallback aproximado caso fonte não registrada
        return len(text) * font_size * 0.5


def _wrap_lines(text: str, font_name: str, font_size: int, max_width: float) -> list:
    lines = []
    for raw_line in (text or "").splitlines() or [""]:
        words = raw_line.split(' ')
        current = []
        while words:
            current.append(words.pop(0))
            trial = ' '.join(current)
            if _string_width(trial, font_name, font_size) > max_width:
                if len(current) > 1:
                    last = current.pop()
                    lines.append(' '.join(current))
                    current = [last]
                else:
                    # palavra sozinha maior que a largura, força quebra
                    lines.append(trial)
                    current = []
        if current:
            lines.append(' '.join(current))
    return lines


def _resolve_template_path() -> str:
    """Encontra o arquivo de modelo 'exemplo-locação.pdf' (ou variantes) no projeto."""
    project_dir = os.getcwd()
    candidates = [
        "exemplo-locação.pdf",
        "exemplo_locacao.pdf",
        "exemplo-locacao.pdf",
        "exemplolocacao.pdf",
        "exemplolocação.pdf",
        "modelo_locacao.pdf",
        "contrato_exemplo.pdf",
        "exemplo_contrato.pdf",
    ]
    for name in candidates:
        path = os.path.join(project_dir, name)
        if os.path.exists(path):
            return path
    # Busca por nomes semelhantes
    for fname in os.listdir(project_dir):
        if not fname.lower().endswith('.pdf'):
            continue
        norm = _slugify(fname)
        if "exemplo" in norm and ("loca" in norm or "contrato" in norm):
            return os.path.join(project_dir, fname)
    raise FileNotFoundError("Arquivo de modelo 'exemplo-locação.pdf' não encontrado no diretório do projeto.")


def _resolve_imagem_compressor(dados: dict) -> str:
    """Escolhe a melhor imagem do compressor baseado em marca/modelo, com fallbacks."""
    explicit = dados.get('imagem_compressor')
    if explicit and os.path.exists(explicit):
        return explicit

    brand = _slugify(dados.get('marca'))
    model = _slugify(dados.get('modelo'))
    names = []
    if brand and model:
        names += [f"compressor-{brand}-{model}", f"{brand}-{model}"]
    if brand:
        names += [f"compressor-{brand}", brand]
    if model:
        names += [f"compressor-{model}", model]

    search_dirs = [
        os.path.join(os.getcwd(), 'assets', 'compressors'),
        os.path.join(os.getcwd(), 'assets', 'logos'),
        os.path.join(os.getcwd(), 'assets', 'images'),
    ]
    exts = ['.png', '.jpg', '.jpeg']
    for d in search_dirs:
        try:
            if not os.path.isdir(d):
                continue
            files = set(os.listdir(d))
            # match exato
            for base in names:
                for ext in exts:
                    candidate = os.path.join(d, base + ext)
                    if os.path.exists(candidate):
                        return candidate
            # match parcial
            for f in files:
                lower = f.lower()
                if not any(lower.endswith(ext) for ext in exts):
                    continue
                if (brand and brand in lower) or (model and model in lower):
                    return os.path.join(d, f)
        except Exception:
            pass

    filial = obter_filial(dados.get('filial_id') or 2) or {}
    fallback = filial.get('logo_path')
    if fallback and os.path.exists(fallback):
        return fallback
    return ""


def _draw_multiline(c: canvas.Canvas, text: str, x: float, y: float, font: str, size: int, max_width: float, leading: float = 14):
    text = _clean_text(text)
    lines = _wrap_lines(text, font, size, max_width)
    c.setFont(font, size)
    ty = y
    for line in lines:
        c.drawString(x, ty, line)
        ty -= leading


def _fit_and_draw_image(c: canvas.Canvas, image_path: str, x: float, y: float, w: float, h: float):
    try:
        img = ImageReader(image_path)
        iw, ih = img.getSize()
        if iw <= 0 or ih <= 0:
            return
        ratio = min(w / iw, h / ih)
        dw, dh = iw * ratio, ih * ratio
        # centraliza dentro da área destino
        dx = x + (w - dw) / 2
        dy = y + (h - dh) / 2
        c.drawImage(img, dx, dy, width=dw, height=dh, preserveAspectRatio=True, mask='auto')
    except Exception:
        pass


# Coordenadas padrão (ajustáveis) para campos dinâmicos no template
COORDS = {
    2: {
        # Linha de saudação
        'saudacao': {
            'x': 70,
            'y': 700,
            'font': 'Helvetica',
            'size': 11
        },
        # Bloco PROPOSTA COMERCIAL + REF/NÚMERO/DATA
        'pc_title': {
            'x': 70,
            'y': 760,
            'font': 'Helvetica-Bold',
            'size': 16
        },
        'pc_labels': {
            'x': 70,
            'y': 740,
            'font': 'Helvetica',
            'size': 12,
            'leading': 16
        },
        # Bloco A/C e De
        'ac_de': {
            'ac_x': 70,
            'de_x': 360,
            'y': 710,
            'font': 'Helvetica',
            'size': 10,
            'leading': 14
        }
    },
    4: {
        # Área para a imagem principal do compressor
        'image': {
            'x': 60,
            'y': 420,
            'w': 470,
            'h': 300
        }
    },
    6: {
        # Parágrafo de condições de pagamento
        'condicoes': {
            'x': 70,
            'y': 700,
            'font': 'Helvetica',
            'size': 11,
            'max_width': 470,
            'leading': 14
        }
    },
    7: {
        # Bloco com Filial / Locatária / Nº Proposta
        'termos': {
            'x': 70,
            'y': 700,
            'font': 'Helvetica',
            'size': 11,
            'leading': 14
        },
        # Imagem pequena adicional
        'image_small': {
            'x': 60,
            'y': 420,
            'w': 200,
            'h': 130
        }
    }
}


def _overlay_on_template(template_pdf: str, output_pdf: str, dados: dict):
    reader = PdfReader(template_pdf)
    writer = PdfWriter()

    # Registrar fontes com suporte a acentuação (DejaVu)
    try:
        pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
        pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
    except Exception:
        pass

    for index in range(len(reader.pages)):
        page = reader.pages[index]
        page_no = index + 1

        from tempfile import NamedTemporaryFile
        try:
            with NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
                c = canvas.Canvas(temp_pdf.name, pagesize=A4)

            # Cabeçalho/Rodapé (todas as páginas exceto capa)
            if page_no >= 2:
                filial = obter_filial(dados.get('filial_id') or 2) or {}
                # Cabeçalho
                try:
                    c.setFont('Helvetica-Bold', 11)
                    c.drawString(40, 810, _clean_text(filial.get('nome', '')))
                except Exception:
                    pass
                # Rodapé (3 linhas centralizadas)
                try:
                    c.setFont('Helvetica', 9)
                    endereco = filial.get('endereco', '')
                    cep = filial.get('cep', '')
                    cnpj = filial.get('cnpj', 'N/A')
                    email = filial.get('email', '')
                    fones = filial.get('telefones', '')
                    c.drawCentredString(297.5, 40, _clean_text(f"{endereco} - CEP: {cep}"))
                    c.drawCentredString(297.5, 28, _clean_text(f"CNPJ: {cnpj}"))
                    c.drawCentredString(297.5, 16, _clean_text(f"E-mail: {email} | Fone: {fones}"))
                except Exception:
                    pass

            # Página 2: PROPOSTA + Saudação
            if page_no == 2 and 'saudacao' in COORDS.get(2, {}):
                # PROPOSTA COMERCIAL + REF/NÚMERO/DATA
                if 'pc_title' in COORDS[2]:
                    cfg = COORDS[2]['pc_title']
                    c.setFont(cfg['font'], cfg['size'])
                    c.drawString(cfg['x'], cfg['y'], 'PROPOSTA COMERCIAL')
                if 'pc_labels' in COORDS[2]:
                    cfg = COORDS[2]['pc_labels']
                    c.setFont(cfg['font'], cfg['size'])
                    y = cfg['y']
                    num = _clean_text(dados.get('numero') or '')
                    data_val = dados.get('data') or datetime.today().strftime('%d/%m/%Y')
                    c.drawString(cfg['x'], y, 'REF:  CONTRATO DE LOCAÇÃO')
                    y -= cfg['leading']
                    c.drawString(cfg['x'], y, f'NÚMERO: {num}')
                    y -= cfg['leading']
                    c.drawString(cfg['x'], y, f'DATA: {data_val}')

                # Bloco A/C | De
                if 'ac_de' in COORDS[2]:
                    cfg = COORDS[2]['ac_de']
                    c.setFont(cfg['font'], cfg['size'])
                    y = cfg['y']
                    ac_nome = _clean_text(dados.get('cliente_nome') or dados.get('ac_cliente') or '')
                    de_empresa = obter_filial(dados.get('filial_id') or 2).get('nome', 'WORLD COMP DO BRASIL')
                    de_nomes = dados.get('de_nomes') or 'Rogério Cerqueira | Valdir Bernardes'
                    de_emails = dados.get('de_emails') or 'rogerio@worldcompressores.com.br    valdir@worldcompressores.com.br'
                    de_fones = dados.get('de_telefones') or '11 97283-8255'
                    ac_email = dados.get('ac_email') or ''

                    # A/C
                    c.drawString(cfg['ac_x'], y, 'A/C:')
                    c.drawString(cfg['ac_x'] + 40, y, ac_nome)

                    # De
                    c.drawString(cfg['de_x'], y, 'De:')
                    c.drawString(cfg['de_x'] + 30, y, _clean_text(de_empresa))
                    y -= cfg['leading']
                    c.drawString(cfg['ac_x'], y, 'Srta')
                    c.drawString(cfg['de_x'], y, _clean_text(de_nomes))
                    y -= cfg['leading']
                    c.drawString(cfg['ac_x'], y, 'Compras')
                    c.drawString(cfg['de_x'], y, _clean_text(de_emails))
                    y -= cfg['leading']
                    if de_fones:
                        c.drawString(cfg['de_x'], y, _clean_text(de_fones))
                    if ac_email:
                        c.drawString(cfg['ac_x'], y, _clean_text(ac_email))

                cfg = COORDS[2]['saudacao']
                tipo = (dados.get('equipamento_tipo') or 'compressor').strip()
                equip = tipo
                if dados.get('marca') or dados.get('modelo'):
                    equip = f"{tipo} {dados.get('marca') or ''} {dados.get('modelo') or ''}".strip()
                saudacao = f"Prezados Senhores, referente à locação de {equip}."
                c.setFont(cfg['font'], cfg['size'])
                c.drawString(cfg['x'], cfg['y'], _clean_text(saudacao))

            # Página 4: Imagem principal
            if page_no == 4 and 'image' in COORDS.get(4, {}):
                cfg = COORDS[4]['image']
                img_path = _resolve_imagem_compressor(dados)
                if img_path:
                    _fit_and_draw_image(c, img_path, cfg['x'], cfg['y'], cfg['w'], cfg['h'])

            # Página 6: Condições de pagamento
            if page_no == 6 and 'condicoes' in COORDS.get(6, {}):
                cfg = COORDS[6]['condicoes']
                condicoes = dados.get('condicoes_pagamento')
                if not condicoes:
                    condicoes = "A vencimento de cada mensalidade, vai depender da proposta que vai ser feita com o cliente."
                _draw_multiline(
                    c,
                    condicoes,
                    cfg['x'], cfg['y'],
                    cfg['font'], cfg['size'],
                    cfg['max_width'], cfg['leading']
                )

            # Página 7: Termos / Imagem pequena
            if page_no == 7:
                filial = obter_filial(dados.get('filial_id') or 2) or {}
                filial_nome = filial.get('nome', '')
                locataria = dados.get('cliente_nome', '')
                proposta = dados.get('numero', '')

                if 'termos' in COORDS.get(7, {}):
                    cfg = COORDS[7]['termos']
                    termos = [
                        f"Filial: {filial_nome}",
                        f"Locatária: {locataria}",
                        f"Nº da Proposta: {proposta}",
                    ]
                    c.setFont(cfg['font'], cfg['size'])
                    ty = cfg['y']
                    for line in termos:
                        c.drawString(cfg['x'], ty, _clean_text(line))
                        ty -= cfg['leading']

                if 'image_small' in COORDS.get(7, {}):
                    cfg = COORDS[7]['image_small']
                    img_path = _resolve_imagem_compressor(dados)
                    if img_path:
                        _fit_and_draw_image(c, img_path, cfg['x'], cfg['y'], cfg['w'], cfg['h'])

                c.save()

                overlay_reader = PdfReader(temp_pdf.name)
                page.merge_page(overlay_reader.pages[0])

            writer.add_page(page)
        except Exception as e:
            # Se ocorrer qualquer erro ao sobrepor, incluir a página original para não interromper o processo
            print(f"Aviso: falha ao sobrepor na página {page_no}: {e}")
            writer.add_page(page)

    with open(output_pdf, 'wb') as f:
        writer.write(f)


def gerar_pdf_locacao(dados: dict, output_path: str):
    """Gera o PDF de locação idêntico ao modelo 'exemplo-locação.pdf',
    sobrepondo somente os campos dinâmicos solicitados.

    Importante: para manter o formato idêntico, este gerador exige ReportLab e PyPDF2
    e o arquivo de modelo presente. Não realiza fallback automático silencioso.

    Campos dinâmicos implementados:
      - Página 2: PROPOSTA (título, REF, NÚMERO, DATA), Bloco A/C e De, Saudação
      - Página 4: Imagem do compressor (por marca)
      - Página 6: Condições de pagamento (texto parametrizável)
      - Página 7: Filial, Locatária e Nº da Proposta + imagem por marca
    """
    # Garante diretório de saída
    out_dir = os.path.dirname(output_path)
    if out_dir and out_dir != '.':
        os.makedirs(out_dir, exist_ok=True)

    if not ADVANCED_PDF_AVAILABLE:
        raise RuntimeError(
            "Dependências de PDF não disponíveis (reportlab/PyPDF2). Instale conforme requirements.txt para gerar idêntico ao modelo."
        )

    template = _resolve_template_path()
    # Verifica número de páginas para assegurar 13 como o modelo informado
    reader = PdfReader(template)
    if len(reader.pages) < 13:
        raise ValueError("O template localizado não possui 13 páginas. Verifique se 'exemplo-locação.pdf' é o arquivo correto.")
    _overlay_on_template(template, output_path, dados)

