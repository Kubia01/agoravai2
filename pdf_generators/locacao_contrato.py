import os
from fpdf import FPDF
from datetime import datetime
from assets.filiais.filiais_config import obter_filial


def _clean(text):
    if text is None:
        return ""
    s = str(text).replace('\t', '    ')
    replacements = {
        '–': '-',
        '—': '-',
        '’': "'",
        '‘': "'",
        '“': '"',
        '”': '"',
        '…': '...',
        '®': '(R)',
        '©': '(C)',
        '™': '(TM)',
        'º': 'o',
        'ª': 'a',
    }
    for a, b in replacements.items():
        s = s.replace(a, b)
    try:
        s.encode('latin-1')
    except Exception:
        s = s.encode('latin-1', 'ignore').decode('latin-1')
    return s


class PDFLocacao(FPDF):
    def __init__(self, dados_filial, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dados_filial = dados_filial or {}
        self.set_auto_page_break(auto=True, margin=20)
        self.set_doc_option('core_fonts_encoding', 'latin-1')

    def header(self):
        # Borda simples
        self.set_line_width(0.5)
        self.rect(5, 5, 200, 287)

    def footer(self):
        self.set_y(-20)
        self.set_font('Arial', '', 9)
        endereco = self.dados_filial.get('endereco', '')
        cep = self.dados_filial.get('cep', '')
        cnpj = self.dados_filial.get('cnpj', 'N/A')
        email = self.dados_filial.get('email', '')
        telefones = self.dados_filial.get('telefones', '')
        self.cell(0, 5, _clean(f"{endereco} - CEP: {cep}"), 0, 1, 'C')
        self.cell(0, 5, _clean(f"CNPJ: {cnpj} | E-mail: {email} | Fone: {telefones}"), 0, 0, 'C')


def _page_title(pdf: PDFLocacao, title: str):
    pdf.set_font('Arial', 'B', 14)
    pdf.ln(5)
    pdf.cell(0, 8, _clean(title), 0, 1, 'L')
    pdf.ln(2)


def _label_value(pdf: PDFLocacao, label: str, value: str):
    # Ensure we start at left margin and compute explicit width to avoid width=0 issues
    left_margin = getattr(pdf, 'l_margin', 10)
    right_margin = getattr(pdf, 'r_margin', 10)
    page_w = getattr(pdf, 'w', 210)
    effective_w = page_w - left_margin - right_margin
    label_w = 55
    value_w = max(10, effective_w - label_w)

    pdf.set_x(left_margin)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(label_w, 7, _clean(label + ':'), 0, 0)
    pdf.set_font('Arial', '', 11)
    pdf.multi_cell(value_w, 7, _clean(value or ''))


def gerar_pdf_locacao(dados: dict, output_path: str):
    filial = obter_filial(dados.get('filial_id') or 2) or {}
    pdf = PDFLocacao(filial, orientation='P', unit='mm', format='A4')

    # Página 1: Capa simples (pode ser ajustada conforme modelo)
    pdf.add_page()
    _page_title(pdf, 'Contrato de Locação de Compressores')
    pdf.set_font('Arial', '', 12)
    pdf.ln(10)
    _label_value(pdf, 'Proposta', dados.get('numero'))
    _label_value(pdf, 'Cliente', dados.get('cliente_nome'))
    _label_value(pdf, 'Filial', filial.get('nome', ''))
    _label_value(pdf, 'Data', datetime.today().strftime('%d/%m/%Y'))

    # Página 2: Saudação personalizada
    pdf.add_page()
    _page_title(pdf, 'Correspondência')
    pdf.set_font('Arial', '', 12)
    saudacao_base = 'Prezados Senhores'
    # Ajuste "de acordo com que vamos locar": usar marca/modelo quando houver
    equip = 'compressor'
    if dados.get('marca') or dados.get('modelo'):
        equip = f"compressor {dados.get('marca') or ''} {dados.get('modelo') or ''}".strip()
    saudacao = f"{saudacao_base}, referente à locação de {equip}."
    pdf.multi_cell(0, 7, _clean(saudacao))

    # Página 3: Dados do equipamento
    pdf.add_page()
    _page_title(pdf, 'Dados do Equipamento')
    _label_value(pdf, 'Marca', dados.get('marca'))
    _label_value(pdf, 'Modelo', dados.get('modelo'))
    _label_value(pdf, 'Número de Série', dados.get('serie'))
    _label_value(pdf, 'Período', f"{dados.get('data_inicio') or ''} a {dados.get('data_fim') or ''}")

    # Página 4: Desenho do compressor por marca/logo
    pdf.add_page()
    _page_title(pdf, 'Imagem do Equipamento')
    img_path = dados.get('imagem_compressor')
    if not img_path or not os.path.exists(img_path):
        # opcional: usar logo da filial como fallback
        fallback = filial.get('logo_path')
        if fallback and os.path.exists(fallback):
            img_path = fallback
    if img_path and os.path.exists(img_path):
        pdf.image(img_path, x=25, y=40, w=160)
    else:
        pdf.set_font('Arial', 'I', 11)
        pdf.multi_cell(0, 7, 'Imagem do compressor não fornecida.')

    # Página 5: Condições gerais básicas
    pdf.add_page()
    _page_title(pdf, 'Condições Gerais')
    texto = (
        "Contrato de locação sujeito às condições gerais da empresa. "
        "O equipamento deverá ser utilizado conforme as instruções do fabricante."
    )
    pdf.set_font('Arial', '', 11)
    pdf.multi_cell(0, 7, _clean(texto))

    # Página 6: Condições de pagamento dinâmicas
    pdf.add_page()
    _page_title(pdf, 'Condições de Pagamento')
    condicoes = dados.get('condicoes_pagamento')
    if not condicoes:
        # fallback com vencimento mensal
        dia = dados.get('vencimento_dia') or '10'
        condicoes = f"A vencimento de cada mensalidade, todo dia {dia}, conforme proposta acordada com o cliente."
    pdf.set_font('Arial', '', 11)
    pdf.multi_cell(0, 7, _clean(condicoes))

    # Página 7: Termos & condições gerais com filial/locatária/nº proposta
    pdf.add_page()
    _page_title(pdf, 'Termos e Condições Gerais')
    filial_nome = filial.get('nome', '')
    locataria = dados.get('cliente_nome', '')
    proposta = dados.get('numero', '')
    termos = (
        f"Filial: {filial_nome}\n"
        f"Locatária: {locataria}\n"
        f"Nº da Proposta: {proposta}\n\n"
        "As demais cláusulas e responsabilidades permanecem conforme as normas de locação da empresa."
    )
    pdf.set_font('Arial', '', 11)
    pdf.multi_cell(0, 7, _clean(termos))

    # Inserir novamente imagem por marca na página 7 (conforme requisito)
    img_path2 = dados.get('imagem_compressor')
    if not img_path2 or not os.path.exists(img_path2):
        fallback = filial.get('logo_path')
        if fallback and os.path.exists(fallback):
            img_path2 = fallback
    if img_path2 and os.path.exists(img_path2):
        y = pdf.get_y() + 5
        pdf.image(img_path2, x=25, y=y, w=70)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pdf.output(output_path)

