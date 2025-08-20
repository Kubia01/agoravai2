"""
Gerador de PDF para contratos de locação seguindo o modelo exemplo-locação.pdf
Implementa sobreposição de dados dinâmicos no template original
"""

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
        '–': '-', '—': '-', ''': "'", ''': "'", '"': '"', '"': '"',
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


def parse_currency_to_float(value):
    try:
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        s = str(value)
        s = s.replace('R$', '').replace(' ', '')
        s = s.replace('.', '').replace(',', '.')
        return float(s)
    except Exception:
        return 0.0

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
        # Margens em mm aproximando layout Word
        self.set_margins(15, 20, 15)
        self.set_auto_page_break(auto=True, margin=20)
        # Paleta e fontes padrão
        self.primary_font = ('Times', '', 12)
        self.primary_font_b = ('Times', 'B', 14)

    # Utilitário: tenta desenhar imagem de fundo se existir
    def _draw_background(self, page_no):
        try:
            # Prioridade: assets/backgrounds/locacao_pg{n}.jpg -> assets/backgrounds/locacao.jpg -> imgfundo.jpg
            import os
            base_dir = os.path.join(os.getcwd(), 'assets', 'backgrounds')
            candidates = []
            candidates.append(os.path.join(base_dir, f'locacao_pg{page_no}.jpg'))
            candidates.append(os.path.join(base_dir, f'locacao_pg{page_no}.png'))
            candidates.append(os.path.join(base_dir, 'locacao.jpg'))
            candidates.append(os.path.join(base_dir, 'locacao.png'))
            candidates.append(os.path.join(os.getcwd(), 'imgfundo.jpg'))
            for bg in candidates:
                if os.path.exists(bg):
                    try:
                        # Página A4: 210x297mm
                        self.image(bg, x=0, y=0, w=210, h=297)
                        break
                    except Exception:
                        continue
        except Exception:
            pass

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font('Times', 'B', 11)
        self.cell(0, 7, clean_text(self.filial.get('nome', '')), 0, 1, 'L')
        # Linha separadora
        self.set_draw_color(150, 150, 150)
        self.set_line_width(0.2)
        self.line(10, 20, 190, 20)
        self.ln(2)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-20)
        self.set_draw_color(150, 150, 150)
        self.line(10, self.get_y(), 190, self.get_y())
        self.ln(2)
        self.set_font('Times', '', 9)
        endereco = self.filial.get('endereco', '')
        cep = self.filial.get('cep', '')
        cnpj = self.filial.get('cnpj', 'N/A')
        email = self.filial.get('email', '')
        fones = self.filial.get('telefones', '')
        self.cell(0, 4, clean_text(f"{endereco} - CEP {cep}"), 0, 1, 'C')
        self.cell(0, 4, clean_text(f"CNPJ: {cnpj} | E-mail: {email} | Fone: {fones}"), 0, 1, 'C')
        self.cell(0, 4, f"Pagina {self.page_no()}", 0, 0, 'R')

    def write_paragraph(self, text, line_height=5, width=0, align='J'):
        content = clean_text(text)
        if not content:
            return
        # multi_cell garante quebra de linha natural próxima ao layout Word
        self.multi_cell(width or 0, line_height, content, 0, align)

    # Páginas
    def page_1_capa(self):
        self.add_page()
        self._draw_background(1)
        # Logo
        logo = self.filial.get('logo_path')
        if logo and os.path.exists(logo):
            try:
                self.image(logo, x=15, y=12, w=32)
            except Exception:
                pass
        # Titulo centralizado
        self.set_y(60)
        self.set_font('Times', 'B', 22)
        self.cell(0, 12, 'PROPOSTA DE LOCACAO', 0, 1, 'C')
        self.set_font('Times', 'B', 18)
        self.cell(0, 10, 'DE COMPRESSOR DE AR', 0, 1, 'C')
        self.ln(10)
        self.set_font('Times', 'B', 14)
        numero = clean_text(self.dados.get('numero', ''))
        self.cell(0, 10, f'Proposta No {numero}', 0, 1, 'C')
        self.ln(4)
        self.set_font('Times', '', 12)
        data_txt = clean_text(self.dados.get('data') or datetime.now().strftime('%d/%m/%Y'))

        self.cell(0, 8, f'Data: {data_txt}', 0, 1, 'C')

    def page_2_proposta(self):
        self.add_page()
        self._draw_background(2)
        self.set_font('Times', 'B', 16)
        self.cell(0, 10, 'PROPOSTA COMERCIAL', 0, 1, 'L')
        self.set_font('Times', '', 12)
        self.cell(0, 6, 'REF:  CONTRATO DE LOCACAO', 0, 1, 'L')
        self.cell(0, 6, f"NUMERO: {clean_text(self.dados.get('numero',''))}", 0, 1, 'L')

        self.cell(0, 6, f"DATA: {clean_text(self.dados.get('data') or datetime.now().strftime('%d/%m/%Y'))}", 0, 1, 'L')

        self.ln(6)
        # A/C | De
        y = self.get_y()
        self.set_font('Times', 'B', 11)
        self.set_xy(15, y)
        self.cell(85, 6, 'A/C:', 0, 0, 'L')
        self.set_xy(110, y)
        self.cell(85, 6, 'De:', 0, 1, 'L')
        cliente_nome = self.dados.get('cliente_nome')
        if not cliente_nome and self.cliente:
            cliente_nome = self.cliente[1] or self.cliente[0]
        self.set_font('Times', '', 11)
        self.set_xy(15, y + 8)
        self.cell(85, 6, clean_text(cliente_nome or ''), 0, 0, 'L')
        self.set_xy(110, y + 8)
        self.cell(85, 6, 'WORLD COMP DO BRASIL', 0, 1, 'L')
        contato = self.dados.get('contato') or 'Srta'
        self.set_xy(15, y + 16)
        self.cell(85, 6, clean_text(contato), 0, 0, 'L')
        resp_nome = 'Rogerio Cerqueira | Valdir Bernardes'
        if self.responsavel and self.responsavel[0]:
            resp_nome = clean_text(self.responsavel[0])
        self.set_xy(110, y + 16)
        self.cell(85, 6, resp_nome, 0, 1, 'L')
        self.set_xy(15, y + 24)
        self.cell(85, 6, 'Compras', 0, 0, 'L')
        resp_email = 'rogerio@worldcompressores.com.br'
        if self.responsavel and self.responsavel[1]:
            resp_email = clean_text(self.responsavel[1])
        self.set_xy(110, y + 24)
        self.cell(85, 6, resp_email, 0, 1, 'L')
        cli_tel = ''
        if self.cliente and self.cliente[7]:
            cli_tel = self.cliente[7]
        self.set_xy(15, y + 32)
        self.cell(85, 6, clean_text(cli_tel), 0, 0, 'L')
        resp_email2 = 'valdir@worldcompressores.com.br'
        self.set_xy(110, y + 32)
        self.cell(85, 6, resp_email2, 0, 1, 'L')
        if self.cliente and self.cliente[8]:
            self.set_xy(15, y + 40)
            self.cell(85, 6, clean_text(self.cliente[8]), 0, 1, 'L')
        self.set_y(y + 56)
        # Saudação dinâmica
        tipo = (self.dados.get('equipamento_tipo') or 'compressor').strip()
        marca = self.dados.get('marca') or ''
        modelo = self.dados.get('modelo') or ''
        primeira_linha = f"Prezados Senhores: Apresentamos proposta para locacao de {tipo} {marca} {modelo}.".strip()

        self.set_font('Times', '', 12)
        self.cell(0, 6, clean_text(primeira_linha), 0, 1, 'L')
        self.ln(2)
        texto = (
            "Agradecemos por nos conceder a oportunidade de apresentarmos nossa proposta para fornecimento de LOCACAO DE COMPRESSOR DE AR.\n\n"

            "A World Comp Compressores e especializada em manutencao de compressores de parafuso das principais marcas do mercado, como Atlas Copco, Ingersoll Rand, Chicago. Atuamos tambem com revisao de equipamentos e unidades compressoras, venda de pecas, bem como venda e locacao de compressores de parafuso isentos de oleo e lubrificados.\n\n"

            "Com profissionais altamente qualificados e atendimento especializado, colocamo-nos a disposicao para analisar, corrigir e prestar os devidos esclarecimentos, sempre buscando atender as especificacoes e necessidades dos nossos clientes."

        )
        self.set_font('Times', '', 12)
        self.write_paragraph(texto, line_height=6)
        self.ln(4)
        self.cell(0, 6, 'Atenciosamente,', 0, 1, 'L')
        self.set_font('Times', 'B', 12)
        self.cell(0, 6, 'WORLD COMP DO BRASIL COMPRESSORES EIRELI', 0, 1, 'L')

    def page_3_sobre(self):
        self.add_page()
        self._draw_background(3)
        self.set_font('Times', 'B', 14)
        self.cell(0, 8, 'SOBRE A WORLD COMP', 0, 1, 'L')
        self.ln(2)
        self.set_font('Times', '', 12)
        self.write_paragraph(
            'A World Comp Compressores e uma empresa com mais de uma decada de atuacao no mercado nacional, especializada na manutencao de compressores de ar do tipo parafuso. Seu atendimento abrange todo o territorio brasileiro, oferecendo solucoes tecnicas e comerciais voltadas a maximizacao do desempenho e da confiabilidade dos sistemas de ar comprimido utilizados por seus clientes.'

        )
        self.ln(4)
        self.set_font('Times', 'B', 14)
        self.cell(0, 8, 'NOSSOS SERVICOS', 0, 1, 'L')
        self.set_font('Times', '', 12)
        self.write_paragraph(
            'A empresa oferece um portfolio completo de servicos, que contempla a manutencao preventiva e corretiva de compressores e unidades compressoras, a venda de pecas de reposicao para diversas marcas, a locacao de compressores de parafuso — incluindo modelos lubrificados e isentos de oleo —, alem da recuperacao de unidades compressoras e trocadores de calor.\nA World Comp tambem disponibiliza contratos de manutencao personalizados, adaptados as necessidades operacionais especificas de cada cliente. Dentre os principais fabricantes atendidos, destacam-se marcas reconhecidas como Atlas Copco, Ingersoll Rand e Chicago Pneumatic.'

        )
        self.ln(4)
        self.set_font('Times', 'B', 14)
        self.cell(0, 8, 'QUALIDADE DOS SERVICOS & MELHORIA CONTINUA', 0, 1, 'L')
        self.set_font('Times', '', 12)
        self.write_paragraph(
            'A empresa investe continuamente na capacitacao de sua equipe, na modernizacao de processos e no aprimoramento da estrutura de atendimento, assegurando alto padrao de qualidade, agilidade e eficacia nos servicos. Mantem ainda uma politica ativa de melhoria continua, com avaliacoes periodicas que visam atualizar tecnologias, aperfeicoar metodos e garantir excelencia tecnica.'

        )
        self.ln(4)
        self.set_font('Times', 'B', 14)
        self.cell(0, 8, 'CONTE CONOSCO PARA UMA PARCERIA!', 0, 1, 'L')
        self.set_font('Times', '', 12)
        self.cell(0, 6, 'Nossa missao e ser sua melhor parceria com sinonimo de qualidade, garantia e o melhor custo beneficio.', 0, 1, 'L')


    def page_4_equipamento(self):
        self.add_page()
        self._draw_background(4)
        self.set_font('Times', 'B', 16)
        self.cell(0, 8, 'COBERTURA TOTAL', 0, 1, 'L')
        self.set_font('Times', '', 12)
        self.write_paragraph(
            'O Contrato de Locacao cobre todos os servicos e manutencoes, isso significa que nao existe custos inesperados com o seu sistema de ar comprimido. O cronograma de manutencoes preventivas e seguido a risca e gerenciado por um time de engenheiros especializados para garantir o mais alto nivel de eficiencia. Alem de voce contar com a cobertura completa para reparos, intervencoes emergenciais e atendimento proativo.'

        )
        self.ln(4)
        self.set_font('Times', 'B', 14)
        self.cell(0, 8, 'EQUIPAMENTO A SER OFERTADO:', 0, 1, 'L')
        self.set_font('Times', '', 12)
        tipo = (self.dados.get('equipamento_tipo') or 'COMPRESSOR DE PARAFUSO LUBRIFICADO REFRIGERADO A AR').upper()

        self.cell(0, 6, clean_text(tipo), 0, 1, 'L')
        self.ln(3)
        # Imagem
        img = resolve_imagem_compressor(self.dados)
        if img and os.path.exists(img):
            try:
                self.image(img, x=25, y=self.get_y(), w=150)
                self.ln(90)
            except Exception:
                self.set_font('Times', 'I', 11)
                self.cell(0, 6, 'Imagem nao disponivel.', 0, 1, 'L')

    def page_5_tabela(self):
        self.add_page()
        self._draw_background(5)
        self.set_font('Times', 'B', 16)
        self.cell(0, 8, 'CONDICOES COMERCIAIS - EQUIPAMENTOS OFERTADOS', 0, 1, 'L')

        self.ln(2)
        # Cabeçalhos - Ajustando larguras para caber na página
        self.set_font('Times', 'B', 11)
        self.cell(15, 8, 'Item', 1, 0, 'C')
        self.cell(20, 8, 'Qtd.', 1, 0, 'C')
        self.cell(85, 8, 'Descricao', 1, 0, 'C')
        self.cell(25, 8, 'Vlr Unit.', 1, 0, 'C')
        self.cell(25, 8, 'Periodo', 1, 1, 'C')
        self.set_font('Times', '', 12)
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
        total_mensal = 0.0
        for idx, it in enumerate(itens, start=1):
            # item index
            item_label = clean_text(str(it.get('item'))) if it.get('item') not in (None, '') else f"{idx:02d}"
            self.cell(15, 8, item_label, 1, 0, 'C')
            self.cell(20, 8, clean_text(str(it.get('quantidade', ''))), 1, 0, 'C')

            self.cell(85, 8, clean_text(str(it.get('descricao', ''))), 1, 0, 'L')

            self.cell(25, 8, clean_text(format_currency(it.get('valor_unitario'))), 1, 0, 'R')

            self.cell(25, 8, clean_text(str(it.get('periodo', ''))), 1, 1, 'C')
            try:
                qtdf = parse_currency_to_float(it.get('quantidade')) or 1.0
            except Exception:
                qtdf = 1.0
            valf = parse_currency_to_float(it.get('valor_unitario'))
            total_mensal += qtdf * valf
        self.ln(4)
        self.set_font('Times', 'B', 13)
        self.cell(40, 8, 'VALOR MENSAL', 0, 0, 'L')
        self.set_font('Times', '', 12)
        valor_exibicao = self.dados.get('valor_mensal')
        if not valor_exibicao:
            valor_exibicao = total_mensal
        self.cell(0, 8, clean_text(format_currency(valor_exibicao)), 0, 1, 'L')


    def page_6_pagamento(self):
        self.add_page()
        self._draw_background(6)
        self.set_font('Times', 'B', 16)
        self.cell(0, 8, 'CONDICOES DE PAGAMENTO', 0, 1, 'L')
        self.ln(2)
        valor = format_currency(self.dados.get('valor_mensal'))
        condicoes = self.dados.get('condicoes_pagamento') or (
            f"O preco inclui: Uso do equipamento listado no Resumo da Proposta Preco, partida tecnica, servicos preventivos e corretivos, pecas, deslocamento e acomodacao dos tecnicos, quando necessario.\n"

            f"Pelos servicos objeto desta proposta, apos a entrega do(s) equipamento(s) previsto neste contrato, o CONTRATANTE devera iniciar os respectivos pagamentos mensais referentes a locacao no valor de {valor} (__________ reais) taxa fixa mensal, com vencimento a 30 DDL, Data esta que contara a partir da entrega do equipamento nas dependencias da contratante, (COM FATURAMENTO ATRAVES DE RECIBO DE LOCACAO)."

        )
        self.set_font('Times', '', 12)
        self.write_paragraph(condicoes, line_height=6)
        self.ln(3)
        self.set_font('Times', 'B', 14)
        self.cell(0, 8, 'CONDICOES COMERCIAIS', 0, 1, 'L')
        self.set_font('Times', '', 12)
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
            self.cell(0, 6, f"- {clean_text(b)}", 0, 1, 'L')

    def page_7_termos(self):
        self.add_page()
        self._draw_background(7)
        self.set_font('Times', 'B', 16)
        self.cell(0, 8, 'TERMOS E CONDICOES GERAIS DE LOCACAO DE EQUIPAMENTO', 0, 1, 'L')

        self.ln(2)
        # Dinâmicos: Filial, Locataria, Nº Proposta
        filial_nome = self.filial.get('nome', '')
        locataria = self.dados.get('cliente_nome') or (self.cliente[1] if self.cliente else '') or (self.cliente[0] if self.cliente else '')

        proposta = self.dados.get('numero', '')
        self.set_font('Times', '', 12)
        self.cell(0, 5, clean_text(f"Filial: {filial_nome}"), 0, 1, 'L')
        self.cell(0, 5, clean_text(f"Locataria: {locataria}"), 0, 1, 'L')
        self.cell(0, 5, clean_text(f"No da Proposta: {proposta}"), 0, 1, 'L')
        self.ln(2)
        # Imagem pequena
        img = resolve_imagem_compressor(self.dados)
        if img and os.path.exists(img):
            try:
                self.image(img, x=25, y=self.get_y(), w=60)
                self.ln(50)
            except Exception:
                pass
        # Texto introdutório (resumo; restante segue nas próximas páginas)
        intro = (
            'Pelo presente instrumento particular, as partes qualificadas tem entre si justo e acertado os presentes Termos e Condicoes Gerais de Locacao de Equipamento, que se regerao pelas clausulas seguintes.'

        )
        self.write_paragraph(intro, line_height=6)

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
        for idx, text in enumerate(textos, start=8):
            self.add_page()
            self._draw_background(idx)
            self.set_font('Times', '', 12)
            self.write_paragraph(text, line_height=6)


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

