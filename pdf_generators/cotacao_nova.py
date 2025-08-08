import sqlite3
import os
import datetime
import sys
from fpdf import FPDF
from database import DB_NAME
from utils.formatters import format_cep, format_phone, format_currency, format_date, format_cnpj

# Adicionar o diretório assets ao path para importar os templates
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from assets.filiais.filiais_config import obter_filial, obter_usuario_cotacao, obter_template_capa_jpeg

def clean_text(text):
    """Substitui tabs por espaços e remove caracteres problemáticos"""
    if text is None:
        return ""
    
    # Converter para string se não for
    text = str(text)
    
    # Substitui tabs por 4 espaços
    text = text.replace('\t', '    ')
    
    # Substituir caracteres especiais problemáticos
    replacements = {
        # Bullets e símbolos especiais
        '•': '- ',
        '●': '- ',
        '◦': '- ',
        '◆': '- ',
        '▪': '- ',
        '▫': '- ',
        '★': '* ',
        '☆': '* ',
        
        # Aspas especiais
        '"': '"',
        '"': '"',
        ''': "'",
        ''': "'",
        
        # Travessões
        '–': '-',
        '—': '-',
        
        # Outros símbolos
        '…': '...',
        '®': '(R)',
        '™': '(TM)',
        '©': '(C)',
        '°': ' graus',
        '€': 'EUR',
        '£': 'GBP',
        '¥': 'JPY',
        
        # Acentos problemáticos (fallback)
        'À': 'A', 'Á': 'A', 'Â': 'A', 'Ã': 'A', 'Ä': 'A',
        'È': 'E', 'É': 'E', 'Ê': 'E', 'Ë': 'E',
        'Ì': 'I', 'Í': 'I', 'Î': 'I', 'Ï': 'I',
        'Ò': 'O', 'Ó': 'O', 'Ô': 'O', 'Õ': 'O', 'Ö': 'O',
        'Ù': 'U', 'Ú': 'U', 'Û': 'U', 'Ü': 'U',
        'Ç': 'C', 'Ñ': 'N',
        'à': 'a', 'á': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a',
        'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e',
        'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i',
        'ò': 'o', 'ó': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o',
        'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u',
        'ç': 'c', 'ñ': 'n',
    }
    
    # Aplicar substituições
    for old_char, new_char in replacements.items():
        text = text.replace(old_char, new_char)
    
    # Remover caracteres não ASCII restantes
    try:
        # Tentar encoding/decoding para limpar caracteres problemáticos
        text = text.encode('ascii', 'ignore').decode('ascii')
    except:
        # Se falhar, usar apenas caracteres básicos
        text = ''.join(char for char in text if ord(char) < 128)
    
    return text

class PDFCotacao(FPDF):
    def __init__(self, dados_filial, dados_usuario, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.baby_blue = (137, 207, 240)  # Azul bebê #89CFF0
        self.dados_filial = dados_filial
        self.dados_usuario = dados_usuario
        
        # Configurar encoding para suportar mais caracteres
        self.set_doc_option('core_fonts_encoding', 'latin-1')

        # Controle de seções com margens diferenciadas
        self._section_mode = None
        self._section_top_first = None
        self._section_bottom_first = None
        self._section_top_cont = None
        self._section_bottom_cont = None
        self._default_top = 10
        self._default_bottom = 25

    def begin_section(self, name, top_first, bottom_first, top_cont, bottom_cont):
        self._section_mode = name
        self._section_top_first = top_first
        self._section_bottom_first = bottom_first
        self._section_top_cont = top_cont
        self._section_bottom_cont = bottom_cont
        # Aplicar margens da primeira página da seção
        self.set_top_margin(top_first)
        self.set_auto_page_break(auto=True, margin=bottom_first)

    def end_section(self):
        # Restaurar margens padrão e limpar estado
        self.set_top_margin(self._default_top)
        self.set_auto_page_break(auto=True, margin=self._default_bottom)
        self._section_mode = None
        self._section_top_first = None
        self._section_bottom_first = None
        self._section_top_cont = None
        self._section_bottom_cont = None

    def accept_page_break(self):
        # Em páginas complementares de uma seção, usar margens de continuação
        if self._section_mode:
            if self._section_top_cont is not None:
                self.set_top_margin(self._section_top_cont)
            if self._section_bottom_cont is not None:
                self.set_auto_page_break(auto=True, margin=self._section_bottom_cont)
        return True

    def header(self):
        # NÃO exibir header na página 1 (capa JPEG)
        if self.page_no() == 1:
            return
            
        # Na página 2, exibir apenas bordas (sem logo e dados, pois são manuais)
        if self.page_no() == 2:
            # Desenha apenas a borda
            self.set_line_width(0.5)
            self.rect(5, 5, 200, 287)  # A4: 210x297, então 5mm de margem
            return
            
        # Desenha a borda em todas as páginas (exceto capa)
        self.set_line_width(0.5)
        self.rect(5, 5, 200, 287)  # A4: 210x297, então 5mm de margem

        # Usar fonte padrão em negrito
        self.set_font("Arial", 'B', 11)
        
        # Dados da proposta no canto superior esquerdo
        self.set_y(10)
        self.cell(0, 5, clean_text(self.dados_filial.get('nome', '')), 0, 1)
        self.cell(0, 5, clean_text("PROPOSTA COMERCIAL:"), 0, 1)
        self.cell(0, 5, clean_text(f"NÚMERO: {self.numero_proposta}"), 0, 1)
        self.cell(0, 5, clean_text(f"DATA: {self.data_proposta}"), 0, 1)
        
        # Linha de separação
        self.line(10, 35, 200, 35)
        self.ln(5)

    def footer(self):
        # NÃO exibir footer na página da capa JPEG (primeira página)
        if self.page_no() == 1:
            return
            
        # Posiciona o rodapé a 1.5 cm do fundo
        self.set_y(-25)  # Aumentou um pouco para acomodar mais uma linha
        
        # Linha divisória acima do rodapé
        self.line(10, self.get_y() - 5, 200, self.get_y() - 5)
        
        # Usar fonte padrão e cor azul bebê - RODAPÉ MINIMALISTA
        self.set_font("Arial", '', 10)  # Fonte menor
        self.set_text_color(*self.baby_blue)  # Cor azul bebê
        
        # Informações do rodapé centralizadas - 3 linhas com CNPJ
        endereco_completo = f"{self.dados_filial.get('endereco', '')} - CEP: {self.dados_filial.get('cep', '')}"
        cnpj_completo = f"CNPJ: {self.dados_filial.get('cnpj', 'N/A')}"
        contato_completo = f"E-mail: {self.dados_filial.get('email', '')} | Fone: {self.dados_filial.get('telefones', '')}"
        
        self.cell(0, 5, clean_text(endereco_completo), 0, 1, 'C')
        self.cell(0, 5, clean_text(cnpj_completo), 0, 1, 'C')
        self.cell(0, 5, clean_text(contato_completo), 0, 1, 'C')
        
        # Resetar cor para preto para o conteúdo principal
        self.set_text_color(0, 0, 0)
    
    @staticmethod
    def obter_composicao_kit(kit_id):
        """Obtém a composição de um kit a partir do banco de dados"""
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        composicao = []
        
        try:
            c.execute("""
                SELECT p.nome, kc.quantidade 
                FROM kit_items kc
                JOIN produtos p ON kc.produto_id = p.id
                WHERE kc.kit_id = ?
            """, (kit_id,))
            
            for row in c.fetchall():
                nome, quantidade = row
                composicao.append(f"{quantidade} x {nome}")
                
        except sqlite3.Error:
            composicao = ["Erro ao carregar composição"]
        finally:
            conn.close()
        
        return composicao

def gerar_pdf_cotacao_nova(cotacao_id, db_name, current_user=None, contato_nome=None):
    """
    Versão melhorada do gerador de PDF de cotações
    - Corrige problemas de logo
    - Adiciona capa personalizada por usuário
    - Corrige problemas de descrição e valores
    - Inclui CNPJ da filial no rodapé
    """
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        c = conn.cursor()   

        # Obter dados da cotação (incluindo filial_id)
        c.execute("""
            SELECT 
                cot.id, cot.numero_proposta, cot.modelo_compressor, cot.numero_serie_compressor, 
                cot.descricao_atividade, cot.observacoes, cot.data_criacao,
                cot.valor_total, cot.tipo_frete, cot.condicao_pagamento, cot.prazo_entrega,
                cli.id AS cliente_id, cli.nome AS cliente_nome, cli.nome_fantasia, cli.endereco, cli.email, 
                cli.telefone, cli.site, cli.cnpj, cli.cidade, cli.estado, cli.cep,
                usr.id AS responsavel_id, usr.nome_completo, usr.email AS usr_email, usr.telefone AS usr_telefone, usr.username,
                cot.moeda, cot.relacao_pecas, cot.filial_id, cot.esboco_servico, cot.relacao_pecas_substituir
            FROM cotacoes AS cot
            JOIN clientes AS cli ON cot.cliente_id = cli.id
            JOIN usuarios AS usr ON cot.responsavel_id = usr.id
            WHERE cot.id = ?
        """, (cotacao_id,))
        cotacao_data = c.fetchone()

        if not cotacao_data:
            return False, "Cotação não encontrada para gerar PDF."

        (
            cot_id, numero_proposta, modelo_compressor, numero_serie_compressor,
            descricao_atividade, observacoes, data_criacao,
            valor_total, tipo_frete, condicao_pagamento, prazo_entrega,
            cliente_id, cliente_nome, cliente_nome_fantasia, cliente_endereco, cliente_email, 
            cliente_telefone, cliente_site, cliente_cnpj, cliente_cidade, 
            cliente_estado, cliente_cep,
            responsavel_id, responsavel_nome, responsavel_email, responsavel_telefone, responsavel_username,
            moeda, relacao_pecas, filial_id, esboco_servico, relacao_pecas_substituir
        ) = cotacao_data

        # Obter dados da filial
        dados_filial = obter_filial(filial_id or 2)  # Default para filial 2
        if not dados_filial:
            return False, "Dados da filial não encontrados."

        # Obter configurações do usuário
        dados_usuario = obter_usuario_cotacao(responsavel_username)
        if not dados_usuario:
            dados_usuario = {
                'nome_completo': responsavel_nome,
                'assinatura': f"{responsavel_nome}\nVendas"
            }
        
        # Usar email do usuário que já vem da query principal
        if responsavel_email:
            dados_usuario['email'] = responsavel_email

        # Obter contato do parâmetro ou buscar principal
        if not contato_nome:
            c.execute("""
                SELECT nome FROM contatos 
                WHERE cliente_id = ? 
                LIMIT 1
            """, (cliente_id,))
            contato_principal = c.fetchone()
            contato_nome = contato_principal[0] if contato_principal else "Não informado"

        # Obter itens da cotação - QUERY SIMPLIFICADA (como modelo antigo)
        c.execute("""
            SELECT 
                id, tipo, item_nome, quantidade, descricao, 
                valor_unitario, valor_total_item, 
                mao_obra, deslocamento, estadia, produto_id, tipo_operacao
            FROM itens_cotacao 
            WHERE cotacao_id=?
        """, (cotacao_id,))
        itens_cotacao = c.fetchall()

        # Criar o PDF
        pdf = PDFCotacao(dados_filial, dados_usuario, orientation='P', unit='mm', format='A4')
        pdf.set_auto_page_break(auto=True, margin=25)  # Aumenta margem inferior para evitar sobreposição
        
        # Configurar dados para cabeçalho/footer (como modelo antigo)
        pdf.numero_proposta = numero_proposta
        pdf.data_proposta = format_date(data_criacao)
        pdf.cliente_nome = cliente_nome_fantasia if cliente_nome_fantasia else cliente_nome
        pdf.cliente_cnpj = cliente_cnpj
        pdf.cliente_telefone = cliente_telefone
        pdf.contato_nome = contato_nome
        pdf.responsavel_nome = responsavel_nome

        # PÁGINA 1: NOVA CAPA COM FUNDO E SOBREPOSIÇÃO
        # ============================================
        pdf.add_page()
        
        # 1. IMAGEM DE FUNDO PADRÃO (nova imagem para capa)
        fundo_padrao = os.path.join(os.path.dirname(__file__), '..', 'imgfundo.jpg')
        if os.path.exists(fundo_padrao):
            pdf.image(fundo_padrao, x=0, y=0, w=210, h=297)
        else:
            # fallback para fundo antigo da capa se existir
            fundo_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'backgrounds', 'capa_fundo.jpg')
            if os.path.exists(fundo_path):
                pdf.image(fundo_path, x=0, y=0, w=210, h=297)
        
        # 2. CAPA PERSONALIZADA SOBREPOSTA (se disponível)
        # 2.1 Tentar template do banco (template_image_path) do usuário
        template_jpeg_path = None
        c.execute("SELECT template_personalizado, template_image_path FROM usuarios WHERE username = ?", (responsavel_username,))
        tu = c.fetchone()
        if tu and tu[0] and tu[1] and os.path.exists(tu[1]):
            template_jpeg_path = tu[1]
        else:
            # fallback para mapeamento estático
            template_jpeg_path = obter_template_capa_jpeg(responsavel_username)
        if template_jpeg_path and os.path.exists(template_jpeg_path):
            # Adicionar capa personalizada reduzida e posicionada
            capa_width = 120  # Largura reduzida
            capa_height = 120  # Altura reduzida  
            x_pos = (210 - capa_width) / 2  # Centralizada
            y_pos = 105  # Posição Y no terço superior
            
            pdf.image(template_jpeg_path, x=x_pos, y=y_pos, w=capa_width, h=capa_height)
        # Não exibir nenhum texto na capa
        pdf.set_text_color(0, 0, 0)

        # PÁGINA 2: APRESENTAÇÃO COM LOGO E DADOS (COMO ESTAVA ANTES)
        # ===========================================================
        pdf.add_page()
        # (Sem fundo padrão nas páginas subsequentes)
        
        # Logo centralizado (como estava antes)
        logo_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'logos', 'world_comp_brasil.jpg')
        if os.path.exists(logo_path):
            logo_height = 30
            logo_width = logo_height * 1.5
            pdf.image(logo_path, x=(210 - logo_width) / 2, y=20, w=logo_width)
        
        # Posição para dados do cliente e empresa
        pdf.set_y(80)  # Aumentado para 80 para dar espaço ao logo maior
        
        # Dados do cliente (lado esquerdo) e empresa (lado direito)
        pdf.set_font("Arial", 'B', 10)  # Fonte menor para acomodar mais texto
        pdf.cell(95, 7, clean_text("APRESENTADO PARA:"), 0, 0, 'L')
        pdf.set_x(105)  # Reduzido ainda mais para dar espaço
        pdf.cell(95, 7, clean_text("APRESENTADO POR:"), 0, 1, 'L')
        
        # Nome do cliente/empresa
        pdf.set_font("Arial", 'B', 10)
        cliente_nome_display = getattr(pdf, 'cliente_nome', 'N/A')
        pdf.cell(95, 5, clean_text(cliente_nome_display), 0, 0, 'L')
        
        pdf.set_x(105)
        nome_filial = dados_filial.get('nome', 'N/A')
        pdf.cell(95, 5, clean_text(nome_filial), 0, 1, 'L')
        
        # CNPJ
        pdf.set_font("Arial", '', 10)
        cliente_cnpj = getattr(pdf, 'cliente_cnpj', '')
        if cliente_cnpj:
            cnpj_texto = f"CNPJ: {format_cnpj(cliente_cnpj)}"
        else:
            cnpj_texto = "CNPJ: N/A"
        pdf.cell(95, 5, clean_text(cnpj_texto), 0, 0, 'L')
        
        pdf.set_x(105)
        cnpj_filial = dados_filial.get('cnpj', 'N/A')
        pdf.cell(95, 5, clean_text(f"CNPJ: {cnpj_filial}"), 0, 1, 'L')
        
        # Telefone
        cliente_telefone = getattr(pdf, 'cliente_telefone', '')
        if cliente_telefone:
            telefone_texto = f"FONE: {format_phone(cliente_telefone)}"
        else:
            telefone_texto = "FONE: N/A"
        pdf.cell(95, 5, clean_text(telefone_texto), 0, 0, 'L')
        
        pdf.set_x(105)
        telefones_filial = dados_filial.get('telefones', 'N/A')
        pdf.cell(95, 5, clean_text(f"FONE: {telefones_filial}"), 0, 1, 'L')
        
        # Contato/Email
        contato_nome = getattr(pdf, 'contato_nome', '')
        if contato_nome:
            contato_texto = f"Sr(a). {contato_nome}"
        else:
            contato_texto = "Contato: N/A"
        pdf.cell(95, 5, clean_text(contato_texto), 0, 0, 'L')
        
        pdf.set_x(105)
        # Buscar e-mail do responsável da cotação
        email_responsavel = dados_usuario.get('email', dados_filial.get('email', 'N/A'))
        pdf.cell(95, 5, clean_text(f"E-mail: {email_responsavel}"), 0, 1, 'L')
        
        # Linha adicional - Responsável
        pdf.cell(95, 5, "", 0, 0, 'L')  # Espaço vazio no lado esquerdo
        pdf.set_x(105)
        responsavel_nome = getattr(pdf, 'responsavel_nome', 'N/A')
        pdf.cell(95, 5, clean_text(f"Responsável: {responsavel_nome}"), 0, 1, 'L')
        
        pdf.ln(10)  # Espaço antes do conteúdo
        
        # Texto de apresentação (como estava antes)
        pdf.set_font("Arial", size=11)
        modelo_text = f" {modelo_compressor}" if modelo_compressor else ""
        
        texto_apresentacao = clean_text(f"""
Prezados Senhores,

Agradecemos a sua solicitação e apresentamos nossas condições comerciais para fornecimento de peças para o compressor{modelo_text}.

A World Comp coloca-se a disposição para analisar, corrigir, prestar esclarecimentos para adequação das especificações e necessidades dos clientes, para tanto basta informar o número da proposta e revisão.


Atenciosamente,
        """)
        pdf.multi_cell(0, 5, texto_apresentacao)
        
        # Assinatura na parte inferior da página 2
        pdf.set_y(240)  # Posiciona mais baixo para garantir que fique na página 2
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 6, clean_text(responsavel_nome.upper()), 0, 1, 'L')
        pdf.set_font("Arial", '', 11)
        pdf.cell(0, 5, clean_text("Vendas"), 0, 1, 'L')
        pdf.cell(0, 5, clean_text(f"Fone: {dados_filial.get('telefones', '')}"), 0, 1, 'L')
        pdf.cell(0, 5, clean_text(dados_filial.get('nome', '')), 0, 1, 'L')

        # PÁGINA 3: SOBRE A EMPRESA (mantendo conteúdo original)
        # =====================================================
        pdf.add_page()
        pdf.set_y(45)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, clean_text("SOBRE A WORLD COMP"), 0, 1, 'L')
        pdf.set_font("Arial", '', 11)
        
        sobre_empresa = clean_text("Há mais de uma década no mercado de manutenção de compressores de ar de parafuso, de diversas marcas, atendemos clientes em todo território brasileiro.")
        pdf.multi_cell(0, 5, sobre_empresa)
        pdf.ln(5)
        
        # Seções sobre a empresa
        secoes = [
            ("FORNECIMENTO, SERVIÇO E LOCAÇÃO", """
A World Comp oferece os serviços de Manutenção Preventiva e Corretiva em Compressores e Unidades Compressoras, Venda de peças, Locação de compressores, Recuperação de Unidades Compressoras, Recuperação de Trocadores de Calor e Contrato de Manutenção em compressores de marcas como: Atlas Copco, Ingersoll Rand, Chicago Pneumatic entre outros.
            """),
            ("CONTE CONOSCO PARA UMA PARCERIA", """
Adaptamos nossa oferta para suas necessidades, objetivos e planejamento. Trabalhamos para que seu processo seja eficiente.
            """),
            ("MELHORIA CONTÍNUA", """
Continuamente investindo em comprometimento, competência e eficiência de nossos serviços, produtos e estrutura para garantirmos a máxima eficiência de sua produtividade.
            """),
            ("QUALIDADE DE SERVIÇOS", """
Com uma equipe de técnicos altamente qualificados e constantemente treinados para atendimentos em todos os modelos de compressores de ar, a World Comp oferece garantia de excelente atendimento e produtividade superior com rapidez e eficácia.
            """)
        ]
        
        for titulo, texto in secoes:
            pdf.set_text_color(*pdf.baby_blue)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 8, clean_text(titulo), 0, 1, 'L')
            
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", '', 11)
            pdf.multi_cell(0, 5, clean_text(texto))
            pdf.ln(3)
        
        texto_final = clean_text("Nossa missão é ser sua melhor parceria com sinônimo de qualidade, garantia e o melhor custo benefício.")
        pdf.multi_cell(0, 5, texto_final)
        pdf.ln(10)
        
        # =====================================================
        # PÁGINA 4: ESBOÇO DO SERVIÇO A SER EXECUTADO
        # =====================================================
        if esboco_servico:
            pdf.add_page()
            # Primeira página da seção: mais alto; complementares: afastar ainda mais do cabeçalho
            pdf.begin_section('esboco', top_first=50, bottom_first=40, top_cont=90, bottom_cont=40)
            pdf.set_y(pdf.t_margin)
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 8, clean_text("ESBOÇO DO SERVIÇO A SER EXECUTADO"), 0, 1, 'L')
            pdf.ln(5)
            pdf.set_font("Arial", '', 11)
            pdf.multi_cell(0, 6, clean_text(esboco_servico))
            # Restaurar margens padrão
            pdf.end_section()
        
        # =====================================================
        # PÁGINA 5: RELAÇÃO DE PEÇAS A SEREM SUBSTITUÍDAS
        # =====================================================
        if relacao_pecas_substituir:
            pdf.add_page()
            pdf.begin_section('relacao', top_first=50, bottom_first=40, top_cont=90, bottom_cont=40)
            pdf.set_y(pdf.t_margin)
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 8, clean_text("RELAÇÃO DE PEÇAS A SEREM SUBSTITUÍDAS"), 0, 1, 'L')
            pdf.ln(5)
            pdf.set_font("Arial", '', 11)
            pdf.multi_cell(0, 6, clean_text(relacao_pecas_substituir))
            pdf.end_section()

        # =====================================================
        # PÁGINAS SEGUINTES: DETALHES DA PROPOSTA
        # =====================================================
        pdf.add_page()
        
        # Dados da proposta
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, clean_text(f"PROPOSTA Nº {numero_proposta}"), 0, 1, 'L')
        pdf.set_font("Arial", '', 11)
        pdf.cell(0, 6, clean_text(f"Data: {format_date(data_criacao)}"), 0, 1, 'L')
        pdf.cell(0, 6, clean_text(f"Responsável: {responsavel_nome}"), 0, 1, 'L')
        pdf.cell(0, 6, clean_text(f"Telefone Responsável: {format_phone(responsavel_telefone)}"), 0, 1, 'L')
        pdf.ln(10)

        # Dados do cliente
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 6, clean_text("DADOS DO CLIENTE:"), 0, 1, 'L')
        pdf.set_font("Arial", '', 11)
        
        cliente_nome_display = cliente_nome_fantasia if cliente_nome_fantasia else cliente_nome
        pdf.cell(0, 5, clean_text(f"Empresa: {cliente_nome_display}"), 0, 1, 'L')
        if cliente_cnpj:
            pdf.cell(0, 5, clean_text(f"CNPJ: {format_cnpj(cliente_cnpj)}"), 0, 1, 'L')
        if contato_nome and contato_nome != "Não informado":
            pdf.cell(0, 5, clean_text(f"Contato: {contato_nome}"), 0, 1, 'L')
        pdf.ln(5)

        # Dados do compressor
        if modelo_compressor or numero_serie_compressor:
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(0, 6, clean_text("DADOS DO COMPRESSOR:"), 0, 1, 'L')
            pdf.set_font("Arial", '', 11)
            if modelo_compressor:
                pdf.cell(0, 5, clean_text(f"Modelo: {modelo_compressor}"), 0, 1, 'L')
            if numero_serie_compressor:
                pdf.cell(0, 5, clean_text(f"Nº de Série: {numero_serie_compressor}"), 0, 1, 'L')
            pdf.ln(5)

        # Descrição - GARANTIR que não seja vazia
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 6, clean_text("DESCRIÇÃO DO SERVIÇO:"), 0, 1, 'L')
        pdf.set_font("Arial", '', 11)
        descricao_final = descricao_atividade if descricao_atividade and descricao_atividade.strip() else "Fornecimento de peças e serviços para compressor"
        pdf.multi_cell(0, 5, clean_text(descricao_final))
        pdf.ln(10)

        # Relação de Peças - GARANTIR que seja exibida corretamente
        if relacao_pecas and relacao_pecas.strip():
            relacao_sem_prefixo = relacao_pecas.replace("Serviço: ", "").replace("Produto: ", "").replace("Kit: ", "")
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(0, 6, clean_text("RELAÇÃO DE PEÇAS A SEREM SUBSTITUÍDAS:"), 0, 1, 'L')
            pdf.set_font("Arial", '', 11)
            pdf.multi_cell(0, 5, clean_text(relacao_sem_prefixo))
            pdf.ln(5)

        # ITENS DA PROPOSTA - CORRIGIDO
        # =============================
        if itens_cotacao:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 8, clean_text("ITENS DA PROPOSTA"), 0, 1, 'C')
            pdf.ln(5)

            # Configurar larguras das colunas para ocupar toda a largura da página
            # Largura total disponível: ~195 (210 - 10 - 5) para margens
            page_width = 195
            col_widths = [20, 85, 25, 35, 30]  # Total: 195
            
            # Cabeçalho da tabela - posicionando nas bordas
            pdf.set_x(10)  # Margem esquerda
            pdf.set_fill_color(50, 100, 150)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(col_widths[0], 8, clean_text("Item"), 1, 0, 'C', 1)
            pdf.cell(col_widths[1], 8, clean_text("Descrição"), 1, 0, 'L', 1)
            pdf.cell(col_widths[2], 8, clean_text("Qtd."), 1, 0, 'C', 1)
            pdf.cell(col_widths[3], 8, clean_text("Valor Unitário"), 1, 0, 'R', 1)
            pdf.cell(col_widths[4], 8, clean_text("Valor Total"), 1, 1, 'R', 1)

            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", '', 11)
            item_counter = 1
            
            for item in itens_cotacao:
                (item_id, item_tipo, item_nome, quantidade, descricao, 
                 valor_unitario, valor_total_item, 
                 mao_obra, deslocamento, estadia, produto_id, tipo_operacao) = item
                
                # DEBUG: Verificar valores vindos do banco
                print(f"DEBUG Item {item_counter}:")
                print(f"  - ID: {item_id}")
                print(f"  - Tipo: {item_tipo}")
                print(f"  - Nome: {item_nome}")
                print(f"  - Quantidade: {quantidade}")
                print(f"  - Descrição: '{descricao}'")
                print(f"  - Valor Unitário: {valor_unitario}")
                print(f"  - Valor Total: {valor_total_item}")
                print(f"  - Produto ID: {produto_id}")
                
                # GARANTIR que descrição não seja vazia ou None
                if not descricao or str(descricao).strip() == '' or str(descricao).lower() in ['none', 'null']:
                    descricao = item_nome if item_nome else "Descrição não informada"
                    print(f"  - Descrição corrigida para: '{descricao}'")
                
                # TRATAMENTO ESPECIAL PARA KITS E SERVIÇOS (como modelo antigo)
                descricao_final = descricao
                
                # Adicionar prefixo baseado no tipo de operação
                if tipo_operacao == "Locação":
                    prefixo = "Locação - "
                else:
                    prefixo = ""
                
                if item_tipo == "Kit" and produto_id:
                    # Obter composição do kit
                    composicao = PDFCotacao.obter_composicao_kit(produto_id)
                    descricao_final = f"{prefixo}Kit: {item_nome}\nComposição:\n" + "\n".join(composicao)
                
                elif item_tipo == "Serviço":
                    descricao_final = f"{prefixo}Serviço: {item_nome}"
                    if mao_obra or deslocamento or estadia:
                        descricao_final += "\nDetalhes:"
                        if mao_obra:
                            descricao_final += f"\n- Mão de obra: R${mao_obra:.2f}"
                        if deslocamento:
                            descricao_final += f"\n- Deslocamento: R${deslocamento:.2f}"
                        if estadia:
                            descricao_final += f"\n- Estadia: R${estadia:.2f}"
                
                else:  # Produto
                    descricao_final = f"{prefixo}{item_nome}"
                
                # Calcular altura baseada no número de linhas
                num_linhas = descricao_final.count('\n') + 1
                altura_total = max(num_linhas * 6, 6)

                # Primeira linha - nome principal do item
                pdf.set_x(10)
                pdf.cell(col_widths[0], altura_total, str(item_counter), 1, 0, 'C')

                # Descrição principal - usar multi_cell para quebrar texto
                x_pos = pdf.get_x()
                y_pos = pdf.get_y()

                # Usar multi_cell para quebrar texto automaticamente
                pdf.multi_cell(col_widths[1], 6, clean_text(descricao_final), 1, 'L')

                # Calcular nova posição Y após o texto
                new_y = pdf.get_y()
                altura_real = new_y - y_pos

                # Voltar para posição original das outras colunas
                pdf.set_xy(x_pos + col_widths[1], y_pos)

                # Quantidade
                pdf.cell(col_widths[2], altura_real, str(int(quantidade)), 1, 0, 'C')

                # Valor Unitário
                pdf.cell(col_widths[3], altura_real, clean_text(f"R$ {valor_unitario:.2f}"), 1, 0, 'R')

                # Valor Total
                pdf.cell(col_widths[4], altura_real, clean_text(f"R$ {valor_total_item:.2f}"), 1, 1, 'R')
                
                item_counter += 1

            # Linha do valor total - alinhada com a tabela
            pdf.set_x(10)  # Mesma margem esquerda da tabela
            pdf.set_font("Arial", 'B', 12)
            pdf.set_fill_color(200, 200, 200)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(sum(col_widths[0:4]), 10, clean_text("VALOR TOTAL DA PROPOSTA:"), 1, 0, 'R', 1)
            pdf.cell(col_widths[4], 10, clean_text(f"R$ {valor_total:.2f}"), 1, 1, 'R', 1)
            pdf.ln(10)

        # Condições comerciais
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 6, clean_text("CONDIÇÕES COMERCIAIS:"), 0, 1, 'L')
        pdf.set_font("Arial", '', 11)
        pdf.cell(0, 5, clean_text(f"Tipo de Frete: {tipo_frete if tipo_frete else 'FOB'}"), 0, 1, 'L')
        pdf.cell(0, 5, clean_text(f"Condição de Pagamento: {condicao_pagamento if condicao_pagamento else 'A combinar'}"), 0, 1, 'L')
        pdf.cell(0, 5, clean_text(f"Prazo de Entrega: {prazo_entrega if prazo_entrega else 'A combinar'}"), 0, 1, 'L')
        pdf.cell(0, 5, clean_text(f"Moeda: {moeda if moeda else 'BRL (Real Brasileiro)'}"), 0, 1, 'L')
        pdf.ln(5)

        # Observações se houver
        if observacoes and observacoes.strip():
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(0, 6, clean_text("OBSERVAÇÕES:"), 0, 1, 'L')
            pdf.set_font("Arial", '', 11)
            pdf.multi_cell(0, 5, clean_text(observacoes))

        # Salvar PDF
        output_dir = os.path.join("data", "cotacoes", "arquivos")
        os.makedirs(output_dir, exist_ok=True)
        file_name = f"Proposta_{numero_proposta.replace('/', '_').replace(' ', '')}.pdf"
        pdf_path = os.path.join(output_dir, file_name)
        pdf.output(pdf_path)

        # Atualizar caminho do PDF no banco de dados
        c.execute("UPDATE cotacoes SET caminho_arquivo_pdf=? WHERE id=?", (pdf_path, cot_id))
        conn.commit()

        return True, pdf_path

    except Exception as e:
        return False, f"Erro ao gerar PDF: {str(e)}"
    finally:
        if conn:
            conn.close()

# Manter compatibilidade com versão antiga
def gerar_pdf_cotacao(cotacao_id, db_name):
    """Função de compatibilidade que chama a nova versão"""
    return gerar_pdf_cotacao_nova(cotacao_id, db_name)