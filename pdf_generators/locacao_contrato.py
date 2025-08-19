import os
import sqlite3
from datetime import datetime

from assets.filiais.filiais_config import obter_filial
from database import DB_NAME

try:
    from fpdf import FPDF
except ImportError as e:
    raise RuntimeError("FPDF não está disponível. Instale com: pip install fpdf2") from e


def clean_text(text):
    if text is None:
        return ""
    s = str(text).replace("\t", "    ")
    replacements = {
        '–': '-', '—': '-', '’': "'", '‘': "'", '“': '"', '”': '"',
        '…': '...', '®': '(R)', '©': '(C)', '™': '(TM)', 'º': 'o', 'ª': 'a',
        'é': 'e', 'ê': 'e', 'è': 'e', 'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a',
        'í': 'i', 'ì': 'i', 'î': 'i', 'ó': 'o', 'ò': 'o', 'õ': 'o', 'ô': 'o',
        'ú': 'u', 'ù': 'u', 'û': 'u', 'ç': 'c',
        'É': 'E', 'Ê': 'E', 'È': 'E', 'Á': 'A', 'À': 'A', 'Ã': 'A', 'Â': 'A',
        'Í': 'I', 'Ì': 'I', 'Î': 'I', 'Ó': 'O', 'Ò': 'O', 'Õ': 'O', 'Ô': 'O',
        'Ú': 'U', 'Ù': 'U', 'Û': 'U', 'Ç': 'C',
    }
    for a, b in replacements.items():
        s = s.replace(a, b)
    return s


def format_currency(value):
    if value is None or value == "":
        return "R$ 0,00"
    try:
        if isinstance(value, str):
            value = value.replace('R$', '').replace('.', '').replace(',', '.').strip()
        val = float(value)
        return f"R$ {val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except Exception:
        return f"R$ {value}"


def fetch_cliente(cliente_id):
    if not cliente_id:
        return None
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT nome, nome_fantasia, endereco, cidade, estado, cep, cnpj, telefone, email FROM clientes WHERE id = ?", (cliente_id,))
        row = c.fetchone()
        conn.close()
        return row
    except Exception:
        return None


def fetch_responsavel(responsavel_id):
    if not responsavel_id:
        return None
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT nome_completo, email, telefone, username FROM usuarios WHERE id = ?", (responsavel_id,))
        row = c.fetchone()
        conn.close()
        return row
    except Exception:
        return None


def resolve_imagem_compressor(dados):
    # 1) Caminho explícito
    explicit = dados.get('imagem_compressor')
    if explicit and os.path.exists(explicit):
        return explicit
    # 2) Buscar por marca/modelo em pastas padrão
    def slug(s):
        if not s:
            return ""
        return ''.join(ch for ch in s.lower().replace(' ', '-') if ch.isalnum() or ch in ['-', '_'])
    brand = slug(dados.get('marca'))
    model = slug(dados.get('modelo'))
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
        if not os.path.isdir(d):
            continue
        try:
            files = set(os.listdir(d))
            for base in names:
                for ext in exts:
                    p = os.path.join(d, base + ext)
                    if os.path.exists(p):
                        return p
            for f in files:
                lf = f.lower()
                if not any(lf.endswith(ext) for ext in exts):
                    continue
                if (brand and brand in lf) or (model and model in lf):
                    return os.path.join(d, f)
        except Exception:
            pass
    # 3) Fallback para logo da filial
    filial = obter_filial(dados.get('filial_id') or 2) or {}
    fallback = filial.get('logo_path')
    if fallback and os.path.exists(fallback):
        return fallback
    return ""


class LocacaoPDF(FPDF):
    def __init__(self, dados):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.dados = dados
        self.filial = obter_filial(dados.get('filial_id') or 2) or {}
        self.cliente = fetch_cliente(dados.get('cliente_id'))
        self.responsavel = fetch_responsavel(dados.get('responsavel_id'))
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font('Arial', 'B', 10)
        self.cell(0, 7, clean_text(self.filial.get('nome', '')), 0, 1, 'L')
        # Linha separadora
        self.set_draw_color(150, 150, 150)
        self.set_line_width(0.2)
        self.line(10, 20, 200, 20)
        self.ln(2)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-20)
        self.set_draw_color(150, 150, 150)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)
        self.set_font('Arial', '', 8)
        endereco = self.filial.get('endereco', '')
        cep = self.filial.get('cep', '')
        cnpj = self.filial.get('cnpj', 'N/A')
        email = self.filial.get('email', '')
        fones = self.filial.get('telefones', '')
        self.cell(0, 4, clean_text(f"{endereco} - CEP {cep}"), 0, 1, 'C')
        self.cell(0, 4, clean_text(f"CNPJ: {cnpj} | E-mail: {email} | Fone: {fones}"), 0, 1, 'C')
        self.cell(0, 4, f"Pagina {self.page_no()}", 0, 0, 'R')

    def write_paragraph(self, text, line_height=5):
        for line in clean_text(text).split('\n'):
            if line.strip():
                self.multi_cell(0, line_height, clean_text(line))
            else:
                self.ln(line_height)

    # Páginas
    def page_1_capa(self):
        self.add_page()
        # Logo
        logo = self.filial.get('logo_path')
        if logo and os.path.exists(logo):
            try:
                self.image(logo, x=10, y=10, w=35)
            except Exception:
                pass
        self.ln(30)
        self.set_font('Arial', 'B', 20)
        self.cell(0, 12, 'PROPOSTA DE LOCACAO', 0, 1, 'C')
        self.cell(0, 10, 'DE COMPRESSOR DE AR', 0, 1, 'C')
        self.ln(12)
        self.set_font('Arial', 'B', 14)
        numero = clean_text(self.dados.get('numero', ''))
        self.cell(0, 10, f'Proposta No {numero}', 0, 1, 'C')
        self.ln(6)
        self.set_font('Arial', '', 12)
        data_txt = clean_text(self.dados.get('data') or datetime.now().strftime('%d/%m/%Y'))
        self.cell(0, 8, f'Data: {data_txt}', 0, 1, 'C')

    def page_2_proposta(self):
        self.add_page()
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'PROPOSTA COMERCIAL', 0, 1, 'L')
        self.set_font('Arial', '', 11)
        self.cell(0, 6, 'REF:  CONTRATO DE LOCACAO', 0, 1, 'L')
        self.cell(0, 6, f"NUMERO: {clean_text(self.dados.get('numero',''))}", 0, 1, 'L')
        self.cell(0, 6, f"DATA: {clean_text(self.dados.get('data') or datetime.now().strftime('%d/%m/%Y'))}", 0, 1, 'L')
        self.ln(6)
        # A/C | De
        y = self.get_y()
        self.set_font('Arial', 'B', 10)
        self.set_xy(10, y)
        self.cell(90, 6, 'A/C:', 0, 0, 'L')
        self.set_xy(110, y)
        self.cell(90, 6, 'De:', 0, 1, 'L')
        cliente_nome = self.dados.get('cliente_nome')
        if not cliente_nome and self.cliente:
            cliente_nome = self.cliente[1] or self.cliente[0]
        self.set_font('Arial', '', 10)
        self.set_xy(10, y + 8)
        self.cell(90, 6, clean_text(cliente_nome or ''), 0, 0, 'L')
        self.set_xy(110, y + 8)
        self.cell(90, 6, 'WORLD COMP DO BRASIL', 0, 1, 'L')
        contato = self.dados.get('contato') or 'Srta'
        self.set_xy(10, y + 16)
        self.cell(90, 6, clean_text(contato), 0, 0, 'L')
        resp_nome = 'Rogerio Cerqueira | Valdir Bernardes'
        if self.responsavel and self.responsavel[0]:
            resp_nome = clean_text(self.responsavel[0])
        self.set_xy(110, y + 16)
        self.cell(90, 6, resp_nome, 0, 1, 'L')
        self.set_xy(10, y + 24)
        self.cell(90, 6, 'Compras', 0, 0, 'L')
        resp_email = 'rogerio@worldcompressores.com.br'
        if self.responsavel and self.responsavel[1]:
            resp_email = clean_text(self.responsavel[1])
        self.set_xy(110, y + 24)
        self.cell(90, 6, resp_email, 0, 1, 'L')
        cli_tel = ''
        if self.cliente and self.cliente[7]:
            cli_tel = self.cliente[7]
        self.set_xy(10, y + 32)
        self.cell(90, 6, clean_text(cli_tel), 0, 0, 'L')
        resp_email2 = 'valdir@worldcompressores.com.br'
        self.set_xy(110, y + 32)
        self.cell(90, 6, resp_email2, 0, 1, 'L')
        if self.cliente and self.cliente[8]:
            self.set_xy(10, y + 40)
            self.cell(90, 6, clean_text(self.cliente[8]), 0, 1, 'L')
        self.set_y(y + 54)
        # Saudação dinâmica
        tipo = (self.dados.get('equipamento_tipo') or 'compressor').strip()
        marca = self.dados.get('marca') or ''
        modelo = self.dados.get('modelo') or ''
        primeira_linha = f"Prezados Senhores: Apresentamos proposta para locacao de {tipo} {marca} {modelo}.".strip()
        self.set_font('Arial', '', 11)
        self.multi_cell(0, 5, clean_text(primeira_linha))
        self.ln(2)
        texto = (
            "Agradecemos por nos conceder a oportunidade de apresentarmos nossa proposta para fornecimento de LOCACAO DE COMPRESSOR DE AR.\n\n"
            "A World Comp Compressores e especializada em manutencao de compressores de parafuso das principais marcas do mercado, como Atlas Copco, Ingersoll Rand, Chicago. Atuamos tambem com revisao de equipamentos e unidades compressoras, venda de pecas, bem como venda e locacao de compressores de parafuso isentos de oleo e lubrificados.\n\n"
            "Com profissionais altamente qualificados e atendimento especializado, colocamo-nos a disposicao para analisar, corrigir e prestar os devidos esclarecimentos, sempre buscando atender as especificacoes e necessidades dos nossos clientes."
        )
        self.set_font('Arial', '', 10)
        self.write_paragraph(texto)
        self.ln(6)
        self.cell(0, 6, 'Atenciosamente,', 0, 1, 'L')
        self.set_font('Arial', 'B', 10)
        self.cell(0, 6, 'WORLD COMP DO BRASIL COMPRESSORES EIRELI', 0, 1, 'L')

    def page_3_sobre(self):
        self.add_page()
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, 'SOBRE A WORLD COMP', 0, 1, 'L')
        self.ln(2)
        self.set_font('Arial', '', 10)
        self.write_paragraph(
            'A World Comp Compressores e uma empresa com mais de uma decada de atuacao no mercado nacional, especializada na manutencao de compressores de ar do tipo parafuso. Seu atendimento abrange todo o territorio brasileiro, oferecendo solucoes tecnicas e comerciais voltadas a maximizacao do desempenho e da confiabilidade dos sistemas de ar comprimido utilizados por seus clientes.'
        )
        self.ln(4)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, 'NOSSOS SERVICOS', 0, 1, 'L')
        self.set_font('Arial', '', 10)
        self.write_paragraph(
            'A empresa oferece um portfolio completo de servicos, que contempla a manutencao preventiva e corretiva de compressores e unidades compressoras, a venda de pecas de reposicao para diversas marcas, a locacao de compressores de parafuso — incluindo modelos lubrificados e isentos de oleo —, alem da recuperacao de unidades compressoras e trocadores de calor.\nA World Comp tambem disponibiliza contratos de manutencao personalizados, adaptados as necessidades operacionais especificas de cada cliente. Dentre os principais fabricantes atendidos, destacam-se marcas reconhecidas como Atlas Copco, Ingersoll Rand e Chicago Pneumatic.'
        )
        self.ln(4)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, 'QUALIDADE DOS SERVICOS & MELHORIA CONTINUA', 0, 1, 'L')
        self.set_font('Arial', '', 10)
        self.write_paragraph(
            'A empresa investe continuamente na capacitacao de sua equipe, na modernizacao de processos e no aprimoramento da estrutura de atendimento, assegurando alto padrao de qualidade, agilidade e eficacia nos servicos. Mantem ainda uma politica ativa de melhoria continua, com avaliacoes periodicas que visam atualizar tecnologias, aperfeicoar metodos e garantir excelencia tecnica.'
        )
        self.ln(4)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, 'CONTE CONOSCO PARA UMA PARCERIA!', 0, 1, 'L')
        self.set_font('Arial', '', 10)
        self.cell(0, 6, 'Nossa missao e ser sua melhor parceria com sinonimo de qualidade, garantia e o melhor custo beneficio.', 0, 1, 'L')

    def page_4_equipamento(self):
        self.add_page()
        self.set_font('Arial', 'B', 14)
        self.cell(0, 8, 'COBERTURA TOTAL', 0, 1, 'L')
        self.set_font('Arial', '', 10)
        self.write_paragraph(
            'O Contrato de Locacao cobre todos os servicos e manutencoes, isso significa que nao existe custos inesperados com o seu sistema de ar comprimido. O cronograma de manutencoes preventivas e seguido a risca e gerenciado por um time de engenheiros especializados para garantir o mais alto nivel de eficiencia. Alem de voce contar com a cobertura completa para reparos, intervencoes emergenciais e atendimento proativo.'
        )
        self.ln(4)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, 'EQUIPAMENTO A SER OFERTADO:', 0, 1, 'L')
        self.set_font('Arial', '', 11)
        tipo = (self.dados.get('equipamento_tipo') or 'COMPRESSOR DE PARAFUSO LUBRIFICADO REFRIGERADO A AR').upper()
        self.multi_cell(0, 6, clean_text(tipo))
        self.ln(3)
        # Imagem
        img = resolve_imagem_compressor(self.dados)
        if img and os.path.exists(img):
            try:
                self.image(img, x=25, y=self.get_y(), w=160)
                self.ln(90)
            except Exception:
                self.set_font('Arial', 'I', 10)
                self.cell(0, 6, 'Imagem nao disponivel.', 0, 1, 'L')

    def page_5_tabela(self):
        self.add_page()
        self.set_font('Arial', 'B', 14)
        self.cell(0, 8, 'CONDICOES COMERCIAIS - EQUIPAMENTOS OFERTADOS', 0, 1, 'L')
        self.ln(2)
        # Cabeçalhos
        self.set_font('Arial', 'B', 10)
        self.cell(15, 8, 'Item', 1, 0, 'C')
        self.cell(20, 8, 'Qtd.', 1, 0, 'C')
        self.cell(90, 8, 'Descricao', 1, 0, 'C')
        self.cell(30, 8, 'Vlr Unit.', 1, 0, 'C')
        self.cell(35, 8, 'Periodo', 1, 1, 'C')
        self.set_font('Arial', '', 10)
        itens = self.dados.get('itens') or []
        if not itens:
            # Montar item base a partir dos campos
            desc = f"Compressor de Ar {clean_text(self.dados.get('marca',''))} Modelo {clean_text(self.dados.get('modelo',''))}"
            itens = [{
                'item': '01',
                'quantidade': self.dados.get('quantidade') or 1,
                'descricao': desc.strip(),
                'valor_unitario': self.dados.get('valor_mensal') or 0,
                'periodo': self.dados.get('periodo') or '5 anos'
            }]
        for it in itens:
            self.cell(15, 8, clean_text(str(it.get('item', ''))), 1, 0, 'C')
            self.cell(20, 8, clean_text(str(it.get('quantidade', ''))), 1, 0, 'C')
            self.cell(90, 8, clean_text(str(it.get('descricao', ''))), 1, 0, 'L')
            self.cell(30, 8, clean_text(format_currency(it.get('valor_unitario'))), 1, 0, 'R')
            self.cell(35, 8, clean_text(str(it.get('periodo', ''))), 1, 1, 'C')
        self.ln(4)
        self.set_font('Arial', 'B', 12)
        self.cell(40, 8, 'VALOR MENSAL', 0, 0, 'L')
        self.set_font('Arial', '', 12)
        self.cell(0, 8, clean_text(format_currency(self.dados.get('valor_mensal'))), 0, 1, 'L')

    def page_6_pagamento(self):
        self.add_page()
        self.set_font('Arial', 'B', 14)
        self.cell(0, 8, 'CONDICOES DE PAGAMENTO', 0, 1, 'L')
        self.ln(2)
        valor = format_currency(self.dados.get('valor_mensal'))
        condicoes = self.dados.get('condicoes_pagamento') or (
            f"O preco inclui: Uso do equipamento listado no Resumo da Proposta Preco, partida tecnica, servicos preventivos e corretivos, pecas, deslocamento e acomodacao dos tecnicos, quando necessario.\n"
            f"Pelos servicos objeto desta proposta, apos a entrega do(s) equipamento(s) previsto neste contrato, o CONTRATANTE devera iniciar os respectivos pagamentos mensais referentes a locacao no valor de {valor} (__________ reais) taxa fixa mensal, com vencimento a 30 DDL, Data esta que contara a partir da entrega do equipamento nas dependencias da contratante, (COM FATURAMENTO ATRAVES DE RECIBO DE LOCACAO)."
        )
        self.set_font('Arial', '', 10)
        self.write_paragraph(condicoes)
        self.ln(3)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, 'CONDICOES COMERCIAIS', 0, 1, 'L')
        self.set_font('Arial', '', 10)
        bullets = [
            'Os equipamentos objetos desta proposta serao fornecidos em caracter de Locacao, cujas regras estao descritas nos Termos e Condicoes Gerais de Locacao.',
            'Assim que V. Sa. receber os equipamentos e materiais, entrar em contato para agendar a(s) partida(s) tecnica(s).',
            'Validade do Contrato 5 anos.',
            'Informar sobre a necessidade de envio de documentos necessarios para integracao de tecnicos.',
            'Antes da compra do servico, o cliente deve informar a World Comp sobre quaisquer riscos na operacao que possam provocar acidentes, assim como medidas de protecao necessarias.',
            'E de responsabilidade do cliente fornecer todas as condicoes necessarias para execucao das manutencoes.',
            'Os residuos gerados pelas atividades da World Comp sao de responsabilidade do cliente.',
            'Todos os precos sao para horario comercial, de segunda a sexta, 8h as 17h.',
            'A World Comp nao se responsabiliza por perdas ou danos indiretos decorrentes dos servicos ou dos equipamentos.'
        ]
        for b in bullets:
            self.multi_cell(0, 5, f"- {clean_text(b)}")

    def page_7_termos(self):
        self.add_page()
        self.set_font('Arial', 'B', 14)
        self.cell(0, 8, 'TERMOS E CONDICOES GERAIS DE LOCACAO DE EQUIPAMENTO', 0, 1, 'L')
        self.ln(2)
        # Dinâmicos: Filial, Locataria, Nº Proposta
        filial_nome = self.filial.get('nome', '')
        locataria = self.dados.get('cliente_nome') or (self.cliente[1] if self.cliente else '') or (self.cliente[0] if self.cliente else '')
        proposta = self.dados.get('numero', '')
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 5, clean_text(f"Filial: {filial_nome}"))
        self.multi_cell(0, 5, clean_text(f"Locataria: {locataria}"))
        self.multi_cell(0, 5, clean_text(f"No da Proposta: {proposta}"))
        self.ln(2)
        # Imagem pequena
        img = resolve_imagem_compressor(self.dados)
        if img and os.path.exists(img):
            try:
                self.image(img, x=25, y=self.get_y(), w=70)
                self.ln(50)
            except Exception:
                pass
        # Texto introdutório (resumo; restante segue nas próximas páginas)
        intro = (
            'Pelo presente instrumento particular, as partes qualificadas tem entre si justo e acertado os presentes Termos e Condicoes Gerais de Locacao de Equipamento, que se regerao pelas clausulas seguintes.'
        )
        self.write_paragraph(intro)

    # Páginas 8 a 13 - conteúdo jurídico resumido conforme diretrizes
    def page_8_a_13_clausulas(self):
        textos = [
            # 8
            'Clausula Primeira – Do Objeto: O presente Contrato consiste na locacao do(s) Equipamento(s) mencionado(s) na Proposta Comercial anexa...\n\nO CONTRATANTE devera manter o(s) Equipamento(s) em suas dependencias e comunicar mudancas de local previamente.',
            # 9
            'Clausula Terceira – Das Condicoes de Pagamento: O CONTRATANTE pagara a World Comp o valor descrito na Proposta Comercial... Inadimplencia sujeita a multa de 2% e juros de 1% a.m.; reajuste anual a cada 12 meses.',
            # 10
            'Clausula Quarta – Das Responsabilidades da World Comp: Partida tecnica; contato previo; entrega de ordem de servico; EPIs; informacoes sobre manutencoes corretivas; observacoes sobre disponibilidade de pecas; cobranca por morosidade do CONTRATANTE.',
            # 11
            'Clausula Quinta – Das Responsabilidades do Contratante: Solicitar partida tecnica; uso adequado; guarda e conservacao; devolucao ao fim; indenizacoes por danos; manutencoes diarias; uso de pecas adequadas; ventilacao adequada; comunicacoes de mudancas; acesso aos tecnicos; medidas de reparo; assistencia em caso de acidente; condicoes para manutencoes; instalacoes eletricas e de sala; instalacoes de tubulacao; nao intervir sem autorizacao; registros; solicitacoes formais; pagamentos.',
            # 12
            'Clausula Sexta – Seguro: O CONTRATANTE devera providenciar seguro do(s) Equipamento(s) cobrindo todos os riscos; incluir na apolice coletiva se houver; responsabilidade total se nao houver seguro; vigencia desde a liberacao do(s) Equipamento(s).\n\nClausula Setima – Rescisao: Multas e prazos de aviso conforme prazos contratuais; hipoteses de rescindir de pleno direito.',
            # 13
            'Clausula Oitava – Caso Fortuito ou Forca Maior: As Partes nao responderao por descumprimentos decorrentes de caso fortuito/forca maior.\n\nClausula Nona – Responsabilidade Trabalhista: Cada Parte e responsavel por seus empregados.\n\nClausula Decima – Disposicoes Gerais: Comunicacoes, cessoes, tolerancia, foro de Sao Bernardo do Campo.\n\nAssinaturas e Testemunhas.'
        ]
        for text in textos:
            self.add_page()
            self.set_font('Arial', '', 10)
            self.write_paragraph(text)


def gerar_pdf_locacao(dados: dict, output_path: str):
    out_dir = os.path.dirname(output_path)
    if out_dir and out_dir != '.':
        os.makedirs(out_dir, exist_ok=True)
    pdf = LocacaoPDF(dados)
    pdf.page_1_capa()
    pdf.page_2_proposta()
    pdf.page_3_sobre()
    pdf.page_4_equipamento()
    pdf.page_5_tabela()
    pdf.page_6_pagamento()
    pdf.page_7_termos()
    pdf.page_8_a_13_clausulas()
    pdf.output(output_path)
    return True, output_path

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

