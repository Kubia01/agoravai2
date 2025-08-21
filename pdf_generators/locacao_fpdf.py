import os
import sqlite3
from datetime import datetime
from fpdf import FPDF
from database import DB_NAME
from utils.formatters import format_cnpj, format_date
from assets.filiais.filiais_config import obter_filial


def clean_text(text):
    if text is None:
        return ""
    text = str(text)
    # Simple sanitization similar to cotacao
    replacements = {
        '\t': '    ',
        '•': '- ', '●': '- ', '◦': '- ', '–': '-', '—': '-', '…': '...',
        '®': '(R)', '™': '(TM)', '©': '(C)', '_': ' ',
    }
    for a, b in replacements.items():
        text = text.replace(a, b)
    try:
        text = text.encode('latin-1', 'ignore').decode('latin-1')
    except Exception:
        text = ''.join(ch for ch in text if ord(ch) < 128)
    return text


class PDFLocacao(FPDF):
    def __init__(self, dados_filial, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.baby_blue = (137, 207, 240)
        self.dados_filial = dados_filial or {}
        self.numero_proposta = ''
        self.data_proposta = ''
        self.set_doc_option('core_fonts_encoding', 'latin-1')
        self._default_top = 10
        self._default_bottom = 25

    def header(self):
        if self.page_no() == 1:
            return
        # Borda
        self.set_line_width(0.5)
        self.rect(5, 5, 200, 287)

        # Cabeçalho dinâmico pela filial
        self.set_font("Arial", 'B', 11)
        self.set_y(10)
        self.cell(0, 5, clean_text(self.dados_filial.get('nome', '')), 0, 1)
        self.cell(0, 5, clean_text("PROPOSTA COMERCIAL"), 0, 1)
        self.cell(0, 5, clean_text(f"NÚMERO: {self.numero_proposta}"), 0, 1)
        self.cell(0, 5, clean_text(f"DATA: {self.data_proposta}"), 0, 1)
        self.line(10, 35, 200, 35)
        self.ln(5)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-25)
        self.line(10, self.get_y() - 5, 200, self.get_y() - 5)
        self.set_font("Arial", '', 10)
        self.set_text_color(*self.baby_blue)
        endereco = f"{self.dados_filial.get('endereco', '')} - CEP: {self.dados_filial.get('cep', '')}"
        cnpj = f"CNPJ: {self.dados_filial.get('cnpj', '')}"
        contato = f"E-mail: {self.dados_filial.get('email', '')} | Fone: {self.dados_filial.get('telefones', '')}"
        self.cell(0, 5, clean_text(endereco), 0, 1, 'C')
        self.cell(0, 5, clean_text(cnpj), 0, 1, 'C')
        self.cell(0, 5, clean_text(contato), 0, 1, 'C')
        self.set_text_color(0, 0, 0)


def _pt_date_portuguese(dt: datetime) -> str:
    meses = [
        'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
        'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'
    ]
    return f"{dt.day} de {meses[dt.month-1]} de {dt.year}"


def _get_cliente_info(cliente_id):
    if not cliente_id:
        return {}
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("SELECT nome, nome_fantasia, cnpj, telefone, email, endereco FROM clientes WHERE id = ?", (cliente_id,))
        row = c.fetchone()
        if not row:
            return {}
        nome, nome_fantasia, cnpj, telefone, email, endereco = row
        return {
            'nome': nome_fantasia or nome,
            'cnpj': cnpj or '',
            'telefone': telefone or '',
            'email': email or '',
            'endereco': endereco or '',
        }
    finally:
        try:
            conn.close()
        except Exception:
            pass


def gerar_pdf_locacao_fpdf(dados: dict, output_path: str) -> (bool, str):
    try:
        filial_id = int(dados.get('filial_id') or 2)
        filial = obter_filial(filial_id) or {}
        cliente = _get_cliente_info(dados.get('cliente_id'))

        pdf = PDFLocacao(filial, orientation='P', unit='mm', format='A4')
        pdf.set_auto_page_break(auto=True, margin=25)
        pdf.numero_proposta = dados.get('numero') or ''
        pdf.data_proposta = format_date(datetime.now().strftime('%Y-%m-%d'))

        # PÁGINA 1 - CAPA SIMPLES
        pdf.add_page()
        pdf.set_y(80)
        pdf.set_font("Arial", 'B', 20)
        pdf.cell(0, 10, clean_text("PROPOSTA COMERCIAL"), 0, 1, 'C')
        pdf.ln(4)
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 8, clean_text("REF: CONTRATO DE LOCAÇÃO"), 0, 1, 'C')
        pdf.ln(10)
        # Logo (se existir)
        logo_path = filial.get('logo_path')
        if logo_path and os.path.exists(logo_path):
            try:
                pdf.image(logo_path, x=(210-80)/2, y=120, w=80)
            except Exception:
                pass

        # PÁGINA 2 - APRESENTAÇÃO
        pdf.add_page()
        pdf.set_y(45)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, clean_text("PROPOSTA COMERCIAL REF: CONTRATO DE LOCAÇÃO"), 0, 1, 'L')
        pdf.set_font("Arial", '', 11)
        pdf.cell(0, 6, clean_text(f"NÚMERO: {pdf.numero_proposta}    DATA: {pdf.data_proposta}"), 0, 1, 'L')
        pdf.ln(5)

        # A/C (Cliente)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 6, clean_text("A/C:"), 0, 1, 'L')
        pdf.set_font("Arial", '', 11)
        ac_lines = [
            cliente.get('nome', ''),
            cliente.get('telefone', ''),
            cliente.get('email', ''),
        ]
        for line in ac_lines:
            if line:
                pdf.cell(0, 6, clean_text(line), 0, 1, 'L')

        pdf.ln(2)
        # De (Filial)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 6, clean_text("De:"), 0, 1, 'L')
        pdf.set_font("Arial", '', 11)
        de_lines = [
            filial.get('nome', ''),
            filial.get('email', ''),
            filial.get('telefones', ''),
        ]
        for line in de_lines:
            if line:
                pdf.cell(0, 6, clean_text(line), 0, 1, 'L')

        pdf.ln(4)
        # Texto de apresentação (editável pelo usuário; se vazio, usar padrão)
        texto_apresentacao = dados.get('apresentacao_texto') or (
            "Prezados Senhores: Agradecemos por nos conceder a oportunidade de apresentarmos nossa proposta para fornecimento de LOCAÇÃO DE COMPRESSOR DE AR. "
            "A World Comp Compressores é especializada em manutenção de compressores de parafuso das principais marcas do mercado, como Atlas Copco, Ingersoll Rand, Chicago. "
            "Atuamos também com revisão de equipamentos e unidades compressoras, venda de peças, bem como venda e locação de compressores de parafuso isentos de óleo e lubrificados. "
            "Com profissionais altamente qualificados e atendimento especializado, colocamo-nos à disposição para analisar, corrigir e prestar os devidos esclarecimentos, sempre buscando atender às especificações e necessidades dos nossos clientes."
        )
        pdf.multi_cell(0, 6, clean_text(texto_apresentacao))

        # PÁGINA 3 - SOBRE/QUALIDADE (texto fixo)
        pdf.add_page()
        pdf.set_y(45)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, clean_text("SOBRE A WORLD COMP"), 0, 1, 'L')
        pdf.set_font("Arial", '', 11)
        sobre_text = (
            "A World Comp Compressores é uma empresa com mais de uma década de atuação no mercado nacional, especializada na manutenção de compressores de ar do tipo parafuso."
        )
        pdf.multi_cell(0, 6, clean_text(sobre_text))
        pdf.ln(4)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, clean_text("NOSSOS SERVIÇOS"), 0, 1, 'L')
        pdf.set_font("Arial", '', 11)
        servicos_text = (
            "A empresa oferece um portfólio completo de serviços, que contempla a manutenção preventiva e corretiva de compressores e unidades compressoras, a venda de peças de reposição para diversas marcas, a locação de compressores de parafuso — incluindo modelos lubrificados e isentos de óleo —, além da recuperação de unidades compressoras e trocadores de calor. A World Comp também disponibiliza contratos de manutenção personalizados, adaptados às necessidades operacionais específicas de cada cliente. Dentre os principais fabricantes atendidos, destacam-se marcas reconhecidas como Atlas Copco, Ingersoll Rand e Chicago Pneumatic."
        )
        pdf.multi_cell(0, 6, clean_text(servicos_text))
        pdf.ln(4)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, clean_text("QUALIDADE DOS SERVIÇOS & MELHORIA CONTÍNUA"), 0, 1, 'L')
        pdf.set_font("Arial", '', 11)
        qualidade_text = (
            "A empresa investe continuamente na capacitação de sua equipe, na modernização de processos e no aprimoramento da estrutura de atendimento, assegurando alto padrão de qualidade, agilidade e eficácia nos serviços. Mantém ainda uma política ativa de melhoria contínua, com avaliações periódicas que visam atualizar tecnologias, aperfeiçoar métodos e garantir excelência técnica."
        )
        pdf.multi_cell(0, 6, clean_text(qualidade_text))
        pdf.ln(4)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, clean_text("CONTE CONOSCO PARA UMA PARCERIA!"), 0, 1, 'L')
        pdf.set_font("Arial", '', 11)
        pdf.multi_cell(0, 6, clean_text("Nossa missão é ser sua melhor parceria com sinônimo de qualidade, garantia e o melhor custo benefício."))

        # PÁGINA 4 - COBERTURA + EQUIPAMENTO (dinâmico compressor + imagem)
        pdf.add_page()
        pdf.set_y(45)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, clean_text("COBERTURA TOTAL"), 0, 1, 'L')
        pdf.set_font("Arial", '', 11)
        cobertura_text = (
            "O Contrato de Locação cobre todos os serviços e manutenções, isso significa que não existem custos inesperados com o seu sistema de ar comprimido. O cronograma de manutenções preventivas é seguido à risca e gerenciado por um time de engenheiros especializados para garantir o mais alto nível de eficiência. Além de você contar com a cobertura completa para reparos, intervenções emergenciais e atendimento proativo."
        )
        pdf.multi_cell(0, 6, clean_text(cobertura_text))
        pdf.ln(4)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, clean_text("EQUIPAMENTO A SER OFERTADO:"), 0, 1, 'L')
        pdf.set_font("Arial", '', 11)
        equip_titulo = dados.get('equipamento_titulo') or dados.get('modelo') or "COMPRESSOR DE PARAFUSO LUBRIFICADO REFRIGERADO À AR"
        pdf.multi_cell(0, 6, clean_text(equip_titulo))
        pdf.ln(6)
        img_path = (dados.get('imagem_compressor') or '').strip()
        if img_path and os.path.exists(img_path):
            try:
                pdf.image(img_path, x=10, y=pdf.get_y(), w=120)
            except Exception:
                pass

        # PÁGINA 5 - COMERCIAIS (tabela de itens)
        pdf.add_page()
        pdf.set_y(45)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, clean_text("COMERCIAIS:"), 0, 1, 'L')
        pdf.ln(2)
        # Cabeçalhos da tabela
        col_widths = [20, 100, 20, 25, 25]
        pdf.set_fill_color(50, 100, 150)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", 'B', 11)
        headers = ["Item", "Descrição", "Qtd.", "Valor Unitário", "Período"]
        for i, head in enumerate(headers):
            pdf.cell(col_widths[i], 8, clean_text(head), 1, 0, 'C', 1)
        pdf.ln(8)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", '', 11)
        itens = dados.get('itens') or []
        for idx, it in enumerate(itens, start=1):
            descricao = it.get('descricao', '')
            quantidade = it.get('quantidade', '')
            valor_unit = it.get('valor_unitario', '')
            periodo = it.get('periodo', '')
            y_start = pdf.get_y()
            pdf.cell(col_widths[0], 8, str(idx), 1, 0, 'C')
            x_desc = pdf.get_x()
            y_desc = pdf.get_y()
            pdf.multi_cell(col_widths[1], 8, clean_text(descricao), 1, 'L')
            y_after = pdf.get_y()
            altura = y_after - y_start
            pdf.set_xy(x_desc + col_widths[1], y_desc)
            pdf.cell(col_widths[2], altura, clean_text(str(quantidade)), 1, 0, 'C')
            pdf.cell(col_widths[3], altura, clean_text(str(valor_unit)), 1, 0, 'R')
            pdf.cell(col_widths[4], altura, clean_text(str(periodo)), 1, 1, 'C')

        # PÁGINA 6 - CONDIÇÕES DE PAGAMENTO
        pdf.add_page()
        pdf.set_y(45)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, clean_text("CONDIÇÕES DE PAGAMENTO:"), 0, 1, 'L')
        pdf.set_font("Arial", '', 11)
        cond = (dados.get('condicoes_pagamento') or '').strip()
        if not cond:
            cond = "A vencimento de cada mensalidade, vai depender da proposta que vai ser feita com o cliente."
        pdf.multi_cell(0, 6, clean_text(cond))

        # PÁGINA 7 - Termos dinâmicos + imagem
        pdf.add_page()
        pdf.set_y(45)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, clean_text("TERMOS E CONDIÇÕES GERAIS DE LOCAÇÃO DE EQUIPAMENTO"), 0, 1, 'L')
        pdf.set_font("Arial", '', 11)
        termo_intro = (
            f"Pelo presente instrumento particular, LOCADORA: {filial.get('nome','')}, inscrita no CNPJ sob nº {filial.get('cnpj','')}. "
            f"LOCATÁRIA: {cliente.get('nome','')}. As partes têm entre si justo e acertado os presentes Termos e Condições Gerais de Locação de Equipamento, com efeitos a partir da Proposta Comercial nº {pdf.numero_proposta}."
        )
        pdf.multi_cell(0, 6, clean_text(termo_intro))
        pdf.ln(4)
        if img_path and os.path.exists(img_path):
            try:
                pdf.image(img_path, x=10, y=pdf.get_y(), w=120)
            except Exception:
                pass

        # PÁGINAS 8-12 - Conteúdo fixo (resumo do texto original)
        paginas_8_12 = [
            (
                "Cláusula Primeira – Do Objeto",
                "O presente Contrato consiste na locação do(s) Equipamento(s) mencionado(s) na Proposta Comercial, de propriedade da World Comp, para uso em atividades industriais, sendo vedado o uso para outros fins."
            ),
            (
                "Incluídos e Excluídos",
                "Inclui: partida técnica, manutenções preventivas/corretivas e insumos específicos. Exclui: atendimentos fora do horário comercial e danos por mau uso."
            ),
            (
                "Responsabilidades & Vigência",
                "As responsabilidades de cada parte e condições de vigência seguem as normas descritas no contrato e na proposta comercial."
            ),
            (
                "Condições Adicionais",
                "Condições adicionais, caso fortuito ou força maior e demais disposições gerais conforme documento padrão de locação."
            ),
            (
                "Penalidades & Rescisão",
                "Previstas multas e mecanismos de rescisão conforme as hipóteses contratuais estabelecidas."
            ),
        ]
        for titulo, texto in paginas_8_12:
            pdf.add_page()
            pdf.set_y(45)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 8, clean_text(titulo), 0, 1, 'L')
            pdf.set_font("Arial", '', 11)
            pdf.multi_cell(0, 6, clean_text(texto))

        # PÁGINA 13 - Assinaturas
        pdf.add_page()
        pdf.set_y(45)
        cidade = 'São Bernardo do Campo'
        data_pt = _pt_date_portuguese(datetime.now())
        pdf.set_font("Arial", '', 11)
        pdf.multi_cell(0, 6, clean_text(f"{cidade}, {data_pt}."))
        pdf.ln(12)
        # Linhas e textos de assinatura
        pdf.cell(0, 6, clean_text("______________________________________"), 0, 1, 'L')
        pdf.cell(0, 6, clean_text(f"Contratada: {filial.get('nome','')}") , 0, 1, 'L')
        pdf.cell(0, 6, clean_text(f"CNPJ: {filial.get('cnpj','')}") , 0, 1, 'L')

        # Salvar
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        pdf.output(output_path)
        return True, output_path
    except Exception as e:
        return False, str(e)

