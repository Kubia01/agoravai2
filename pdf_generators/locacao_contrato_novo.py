"""
Gerador de PDF para contratos de locação seguindo o modelo exemplo-locação.pdf
Implementa todas as 13 páginas com formatação e layout idênticos
"""

import os
from datetime import datetime
import sqlite3
from assets.filiais.filiais_config import obter_filial

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False


def clean_text(text):
    """Limpa texto para uso em PDF"""
    if text is None:
        return ""
    
    # Converter para string e remover espaços extras
    text = str(text).strip()
    
    # Se o texto estiver vazio após strip, retornar string vazia
    if not text:
        return ""
    
    # Substitui caracteres acentuados
    replacements = {
        'ã': 'a', 'à': 'a', 'á': 'a', 'â': 'a', 'ç': 'c', 'é': 'e', 'ê': 'e',
        'í': 'i', 'ó': 'o', 'ô': 'o', 'õ': 'o', 'ú': 'u', 'ü': 'u',
        'Ã': 'A', 'À': 'A', 'Á': 'A', 'Â': 'A', 'Ç': 'C', 'É': 'E', 'Ê': 'E',
        'Í': 'I', 'Ó': 'O', 'Ô': 'O', 'Õ': 'O', 'Ú': 'U', 'Ü': 'U'
    }
    
    # Remove caracteres problemáticos para PDF
    text = text.replace('_', ' ')  # Substitui underscore por espaço
    text = text.replace('–', '-')  # Substitui en-dash por hífen
    text = text.replace('—', '-')  # Substitui em-dash por hífen
    text = text.replace('"', '"')  # Substitui aspas curvas por aspas simples
    text = text.replace('"', '"')
    text = text.replace(''', "'")  # Substitui aspas simples curvas por aspas simples
    text = text.replace(''', "'")
    
    # Remove caracteres não ASCII que podem causar problemas
    text = ''.join(char for char in text if ord(char) < 128 or char in replacements)
    
    # Aplica as substituições de acentos
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Remove espaços múltiplos e trim
    text = ' '.join(text.split())
    
    # Garantir que o texto não comece com underscore ou caracteres problemáticos
    if text and text[0] in ['_', '-', '.', ',', ';', ':', '!', '?', '"', "'", '(', ')', '[', ']', '{', '}']:
        text = text[1:].lstrip()
    
    # Se após a limpeza o texto estiver vazio, retornar um espaço
    if not text:
        return " "
    
    return text


def safe_text_for_pdf(text):
    """Função adicional de segurança para textos que vão para o PDF"""
    if text is None:
        return " "
    
    # Aplicar clean_text primeiro
    cleaned = clean_text(text)
    
    # Verificações adicionais de segurança
    if not cleaned or cleaned.strip() == '':
        return " "
    
    # Garantir que não há underscores no início ou fim
    cleaned = cleaned.strip('_')
    
    # Se ficou vazio após remover underscores, retornar espaço
    if not cleaned:
        return " "
    
    # Verificação final: se ainda tem underscore no início, remover
    if cleaned and cleaned[0] == '_':
        cleaned = cleaned[1:].lstrip()
    
    return cleaned


def format_currency(value):
    """Formata valor monetário"""
    if not value:
        return "R$ 0,00"
    try:
        if isinstance(value, str):
            value = value.replace('R$', '').replace('.', '').replace(',', '.').strip()
        val = float(value)
        return f"R$ {val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except:
        return f"R$ {value}"


def get_cliente_data(cliente_id):
    """Busca dados do cliente"""
    try:
        from database import DB_NAME
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        c.execute("SELECT nome, nome_fantasia, endereco, cidade, estado, cep, cnpj, telefone, email FROM clientes WHERE id = ?", (cliente_id,))
        cliente = c.fetchone()
        
        c.execute("SELECT nome, telefone, email FROM contatos WHERE cliente_id = ?", (cliente_id,))
        contatos = c.fetchall()
        
        conn.close()
        return cliente, contatos
    except:
        return None, []


class LocacaoPDF(FPDF):
    """Classe para gerar PDF do contrato de locação"""
    
    def __init__(self, dados):
        super().__init__()
        self.dados = dados
        self.filial = obter_filial(dados.get('filial_id', 2)) or {}
        self.cliente, self.contatos = get_cliente_data(dados.get('cliente_id')) if dados.get('cliente_id') else (None, [])
        self.set_auto_page_break(auto=True, margin=20)
        
        # Configurar encoding para suportar mais caracteres
        self.set_doc_option('core_fonts_encoding', 'latin-1')
    
    def safe_cell(self, w, h, txt='', border=0, ln=0, align='', fill=False, link=''):
        """Versão segura do cell que trata textos problemáticos"""
        safe_txt = safe_text_for_pdf(txt)
        try:
            super().cell(w, h, safe_txt, border, ln, align, fill, link)
        except Exception as e:
            # Fallback: usar texto vazio
            super().cell(w, h, " ", border, ln, align, fill, link)
    
    def safe_write(self, h, txt='', link=''):
        """Versão segura do write que trata textos problemáticos"""
        safe_txt = safe_text_for_pdf(txt)
        try:
            super().write(h, safe_txt, link)
        except Exception as e:
            # Fallback: usar texto vazio
            super().write(h, " ", link)

    def header(self):
        """Cabeçalho das páginas (exceto capa)"""
        if self.page_no() > 1:
            self.set_font('Arial', 'B', 10)
            self.safe_cell(0, 10, self.filial.get('nome', ''), 0, 1, 'L')
            self.ln(5)

    def footer(self):
        """Rodapé das páginas (exceto capa)"""
        if self.page_no() > 1:
            self.set_y(-25)
            self.set_font('Arial', '', 8)
            
            # Endereço e telefones
            endereco = self.filial.get('endereco', '')
            telefones = self.filial.get('telefones', '')
            self.safe_cell(0, 5, f"{endereco} - {telefones}", 0, 1, 'C')
            
            # Email
            email = self.filial.get('email', '')
            self.safe_cell(0, 5, email, 0, 1, 'C')
            
            # Número da página
            self.safe_cell(0, 5, f"Pagina {self.page_no()}", 0, 0, 'C')

    def write_multiline(self, text, max_chars=85):
        """Escreve texto com quebra de linha"""
        # Aplicar safe_text_for_pdf no texto antes de processar
        text = safe_text_for_pdf(text)
        paragraphs = text.strip().split('\n')
        for paragraph in paragraphs:
            if paragraph.strip():
                words = paragraph.strip().split(' ')
                current_line = ""
                for word in words:
                    test_line = current_line + (" " if current_line else "") + word
                    if len(test_line) <= max_chars:
                        current_line = test_line
                    else:
                        if current_line:
                            self.safe_cell(0, 5, current_line, 0, 1, 'L')
                        current_line = word
                if current_line:
                    self.safe_cell(0, 5, current_line, 0, 1, 'L')
                self.ln(2)

    def page_1_capa(self):
        """Página 1 - Capa"""
        self.add_page()
        
        # Logo se existir
        logo_path = self.filial.get('logo_path', '')
        if logo_path and os.path.exists(logo_path):
            try:
                self.image(logo_path, x=10, y=20, w=40, h=30)
            except:
                pass

        # Título
        self.ln(60)
        self.set_font('Arial', 'B', 20)
        self.safe_cell(0, 15, 'PROPOSTA DE LOCACAO', 0, 1, 'C')
        self.safe_cell(0, 10, 'DE COMPRESSOR DE AR', 0, 1, 'C')
        
        # Número da proposta
        self.ln(20)
        self.set_font('Arial', 'B', 14)
        numero = self.dados.get('numero', '')
        self.safe_cell(0, 10, f'Proposta No {numero}', 0, 1, 'C')
        
        # Data
        self.ln(10)
        self.set_font('Arial', '', 12)
        data_hoje = datetime.now().strftime("%d/%m/%Y")
        self.safe_cell(0, 8, f'Data: {data_hoje}', 0, 1, 'C')

    def page_2_proposta_comercial(self):
        """Página 2 - Proposta Comercial"""
        self.add_page()
        
        # Cabeçalho da proposta
        self.set_font('Arial', 'B', 14)
        self.safe_cell(0, 10, 'PROPOSTA COMERCIAL', 0, 1, 'L')
        self.ln(5)
        
        # Referência, número e data
        self.set_font('Arial', '', 10)
        self.safe_cell(0, 6, 'REF:  CONTRATO DE LOCACAO', 0, 1, 'L')
        numero = self.dados.get('numero', '')
        self.safe_cell(0, 6, f'NUMERO: {numero}', 0, 1, 'L')
        data_hoje = datetime.now().strftime("%d/%m/%Y")
        self.safe_cell(0, 6, f'DATA: {data_hoje}', 0, 1, 'L')
        self.ln(15)

        # Seção A/C e De (duas colunas)
        y_pos = self.get_y()
        
        # Coluna esquerda - A/C
        self.set_xy(10, y_pos)
        self.set_font('Arial', 'B', 10)
        self.safe_cell(80, 6, 'A/C:', 0, 0, 'L')
        
        # Coluna direita - De
        self.set_xy(110, y_pos)
        self.safe_cell(80, 6, 'De:', 0, 1, 'L')
        
        # Nome do cliente e empresa
        cliente_nome = self.dados.get('cliente_nome', 'GRUPO DELGA')
        if self.cliente:
            cliente_nome = self.cliente[1] or self.cliente[0]  # nome_fantasia ou nome
        
        # Garantir que o nome do cliente não tenha underscores
        cliente_nome = safe_text_for_pdf(cliente_nome)
        if not cliente_nome or cliente_nome.strip() == '' or cliente_nome.strip() == ' ':
            cliente_nome = 'CLIENTE'
            
        self.set_xy(10, y_pos + 8)
        self.safe_cell(80, 6, cliente_nome, 0, 0, 'L')
        self.set_xy(110, y_pos + 8)
        self.safe_cell(80, 6, 'WORLD COMP DO BRASIL', 0, 1, 'L')
        
        # Contato
        contato = self.dados.get('contato', 'Srta')
        self.set_xy(10, y_pos + 16)
        self.set_font('Arial', '', 10)
        self.safe_cell(80, 6, safe_text_for_pdf(contato), 0, 0, 'L')
        self.set_xy(110, y_pos + 16)
        self.safe_cell(80, 6, 'Rogerio Cerqueira | Valdir Bernardes', 0, 1, 'L')
        
        # Departamento e email
        self.set_xy(10, y_pos + 24)
        self.safe_cell(80, 6, 'Compras', 0, 0, 'L')
        self.set_xy(110, y_pos + 24)
        self.safe_cell(80, 6, 'rogerio@worldcompressores.com.br', 0, 1, 'L')
        
        # Telefone
        telefone = '11 97283-8255'
        if self.cliente and len(self.cliente) > 7 and self.cliente[7]:
            telefone = self.cliente[7]
        self.set_xy(10, y_pos + 32)
        self.safe_cell(80, 6, safe_text_for_pdf(telefone), 0, 0, 'L')
        self.set_xy(110, y_pos + 32)
        self.safe_cell(80, 6, 'valdir@worldcompressores.com.br', 0, 1, 'L')
        
        # Email do cliente se existir
        if self.cliente and len(self.cliente) > 8 and self.cliente[8]:
            self.set_xy(10, y_pos + 40)
            self.safe_cell(80, 6, safe_text_for_pdf(self.cliente[8]), 0, 1, 'L')
            
        self.set_y(y_pos + 55)

        # Saudação
        self.set_font('Arial', '', 11)
        self.safe_cell(0, 8, 'Prezados Senhores:', 0, 1, 'L')
        self.ln(10)

        # Texto da apresentação
        texto = """Agradecemos por nos conceder a oportunidade de apresentarmos nossa proposta para fornecimento de LOCACAO DE COMPRESSOR DE AR.

A World Comp Compressores e especializada em manutencao de compressores de parafuso das principais marcas do mercado, como Atlas Copco, Ingersoll Rand,Chicago. Atuamos tambem com revisao de equipamentos e unidades compressoras, venda de pecas, bem como venda e locacao de compressores de parafuso isentos de oleo e lubrificados.

Com profissionais altamente qualificados e atendimento especializado, colocamo-nos a disposicao para analisar, corrigir e prestar os devidos esclarecimentos, sempre buscando atender as especificacoes e necessidades dos nossos clientes."""

        self.set_font('Arial', '', 10)
        self.write_multiline(texto)

        # Assinatura
        self.ln(15)
        self.set_font('Arial', '', 10)
        self.safe_cell(0, 6, 'Atenciosamente,', 0, 1, 'L')
        self.set_font('Arial', 'B', 10)
        self.safe_cell(0, 6, 'WORLD COMP DO BRASIL COMPRESSORES EIRELI', 0, 1, 'L')

    def generate_all_pages(self):
        """Gera todas as 13 páginas"""
        self.page_1_capa()
        self.page_2_proposta_comercial()
        
        # Página 3 - Sobre a World Comp
        self.add_page()
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 10, 'SOBRE A WORLD COMP', 0, 1, 'L')
        self.ln(5)
        
        texto3 = """A World Comp Compressores e uma empresa com mais de uma decada de atuacao no mercado nacional, especializada na manutencao de compressores de ar do tipo parafuso. Seu atendimento abrange todo o territorio brasileiro, oferecendo solucoes tecnicas e comerciais voltadas a maximizacao do desempenho e da confiabilidade dos sistemas de ar comprimido utilizados por seus clientes."""
        
        self.set_font('Arial', '', 10)
        self.write_multiline(texto3)
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 10, 'NOSSOS SERVICOS', 0, 1, 'L')
        self.ln(5)
        
        texto_servicos = """A empresa oferece um portfolio completo de servicos, que contempla a manutencao preventiva e corretiva de compressores e unidades compressoras, a venda de pecas de reposicao para diversas marcas, a locacao de compressores de parafuso — incluindo modelos lubrificados e isentos de oleo —, alem da recuperacao de unidades compressoras e trocadores de calor.

A World Comp tambem disponibiliza contratos de manutencao personalizados, adaptados as necessidades operacionais especificas de cada cliente. Dentre os principais fabricantes atendidos, destacam-se marcas reconhecidas como Atlas Copco, Ingersoll Rand e Chicago Pneumatic."""
        
        self.set_font('Arial', '', 10)
        self.write_multiline(texto_servicos)
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 10, 'QUALIDADE DOS SERVICOS & MELHORIA CONTINUA', 0, 1, 'L')
        self.ln(5)
        
        texto_qualidade = """A empresa investe continuamente na capacitacao de sua equipe, na modernizacao de processos e no aprimoramento da estrutura de atendimento, assegurando alto padrao de qualidade, agilidade e eficacia nos servicos. Mantem ainda uma politica ativa de melhoria continua, com avaliacoes periodicas que visam atualizar tecnologias, aperfecoar metodos e garantir excelencia tecnica."""
        
        self.set_font('Arial', '', 10)
        self.write_multiline(texto_qualidade)
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 10, 'CONTE CONOSCO PARA UMA PARCERIA!', 0, 1, 'L')
        self.ln(5)
        self.set_font('Arial', '', 10)
        self.safe_cell(0, 6, 'Nossa missao e ser sua melhor parceria com sinonimo de qualidade, garantia e o melhor custo beneficio.', 0, 1, 'L')

        # Páginas 4-13: Implementação completa do contrato de locação
        self.page_4_especificacoes_tecnicas()
        self.page_5_condicoes_comerciais()
        self.page_6_termos_locacao()
        self.page_7_responsabilidades()
        self.page_8_garantias()
        self.page_9_instalacao_manutencao()
        self.page_10_clausulas_gerais()
        self.page_11_rescisao()
        self.page_12_disposicoes_finais()
        self.page_13_assinaturas()

    def page_4_especificacoes_tecnicas(self):
        """Página 4 - Especificações Técnicas do Equipamento"""
        self.add_page()
        
        self.set_font('Arial', 'B', 14)
        self.safe_cell(0, 10, 'ESPECIFICACOES TECNICAS DO EQUIPAMENTO', 0, 1, 'L')
        self.ln(10)
        
        # Dados do equipamento
        marca = self.dados.get('marca', 'Atlas Copco')
        modelo = self.dados.get('modelo', 'GA22')
        serie = self.dados.get('serie', '12345')
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, 'DADOS DO COMPRESSOR:', 0, 1, 'L')
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        self.safe_cell(0, 6, f'Marca: {safe_text_for_pdf(marca)}', 0, 1, 'L')
        self.safe_cell(0, 6, f'Modelo: {safe_text_for_pdf(modelo)}', 0, 1, 'L')
        self.safe_cell(0, 6, f'Numero de Serie: {safe_text_for_pdf(serie)}', 0, 1, 'L')
        self.safe_cell(0, 6, 'Tipo: Compressor de parafuso lubrificado', 0, 1, 'L')
        self.safe_cell(0, 6, 'Capacidade: Conforme especificacao do modelo', 0, 1, 'L')
        self.safe_cell(0, 6, 'Pressao de trabalho: 7 a 13 bar', 0, 1, 'L')
        self.safe_cell(0, 6, 'Tensao: 220V/380V/440V (conforme disponibilidade)', 0, 1, 'L')
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, 'ITENS INCLUSOS NA LOCACAO:', 0, 1, 'L')
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        self.safe_cell(0, 6, '• Compressor de ar completo', 0, 1, 'L')
        self.safe_cell(0, 6, '• Manual de operacao', 0, 1, 'L')
        self.safe_cell(0, 6, '• Certificado de calibracao (quando aplicavel)', 0, 1, 'L')
        self.safe_cell(0, 6, '• Suporte tecnico durante o periodo de locacao', 0, 1, 'L')
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, 'CONDICOES DE ENTREGA:', 0, 1, 'L')
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        texto_entrega = """O equipamento sera entregue em perfeitas condicoes de funcionamento, testado e aprovado pela equipe tecnica da World Comp. A entrega sera agendada conforme disponibilidade e necessidade do cliente, respeitando o prazo acordado comercialmente."""
        self.write_multiline(texto_entrega)

    def page_5_condicoes_comerciais(self):
        """Página 5 - Condições Comerciais"""
        self.add_page()
        
        self.set_font('Arial', 'B', 14)
        self.safe_cell(0, 10, 'CONDICOES COMERCIAIS', 0, 1, 'L')
        self.ln(10)
        
        # Valores
        valor_mensal = self.dados.get('valor_mensal', '0')
        moeda = self.dados.get('moeda', 'BRL')
        vencimento = self.dados.get('vencimento_dia', '10')
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, 'VALORES DA LOCACAO:', 0, 1, 'L')
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        if valor_mensal and valor_mensal != '0':
            self.safe_cell(0, 6, f'Valor mensal da locacao: {format_currency(valor_mensal)}', 0, 1, 'L')
        else:
            self.safe_cell(0, 6, 'Valor mensal da locacao: Conforme cotacao em anexo', 0, 1, 'L')
        
        self.safe_cell(0, 6, f'Moeda: {moeda}', 0, 1, 'L')
        self.safe_cell(0, 6, f'Vencimento: Todo dia {vencimento} de cada mes', 0, 1, 'L')
        self.safe_cell(0, 6, 'Forma de pagamento: Boleto bancario', 0, 1, 'L')
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, 'CONDICOES DE PAGAMENTO:', 0, 1, 'L')
        self.ln(5)
        
        condicoes = self.dados.get('condicoes_pagamento', 'Pagamento mensal conforme vencimento')
        self.set_font('Arial', '', 10)
        self.write_multiline(safe_text_for_pdf(condicoes))
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, 'OBSERVACOES IMPORTANTES:', 0, 1, 'L')
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        self.safe_cell(0, 6, '• Valores nao incluem frete e instalacao', 0, 1, 'L')
        self.safe_cell(0, 6, '• Multa por atraso de pagamento: 2% sobre o valor em atraso', 0, 1, 'L')
        self.safe_cell(0, 6, '• Juros de mora: 1% ao mes sobre o valor em atraso', 0, 1, 'L')
        self.safe_cell(0, 6, '• Reajuste anual conforme IGPM ou indice oficial', 0, 1, 'L')

    def page_6_termos_locacao(self):
        """Página 6 - Termos e Condições da Locação"""
        self.add_page()
        
        self.set_font('Arial', 'B', 14)
        self.safe_cell(0, 10, 'TERMOS E CONDICOES DA LOCACAO', 0, 1, 'L')
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, '1. PRAZO DE LOCACAO:', 0, 1, 'L')
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        data_inicio = self.dados.get('data_inicio', 'A definir')
        data_fim = self.dados.get('data_fim', 'A definir')
        texto_prazo = f"""O prazo de locacao sera de: {data_inicio} ate {data_fim}, podendo ser prorrogado mediante acordo entre as partes, com antecedencia minima de 30 dias."""
        self.write_multiline(texto_prazo)
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, '2. USO DO EQUIPAMENTO:', 0, 1, 'L')
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        texto_uso = """O equipamento devera ser utilizado exclusivamente para os fins industriais aos quais se destina, conforme especificacoes tecnicas do fabricante. E vedado o uso inadequado, sobrecarga ou modificacoes no equipamento sem autorizacao expressa da locadora."""
        self.write_multiline(texto_uso)
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, '3. LOCAL DE INSTALACAO:', 0, 1, 'L')
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        texto_local = """O equipamento sera instalado no endereco fornecido pelo locatario, devendo este providenciar local adequado, com infraestrutura eletrica, espaco fisico e condicoes ambientais conforme especificacoes tecnicas."""
        self.write_multiline(texto_local)
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, '4. SEGURO:', 0, 1, 'L')
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        texto_seguro = """O locatario devera manter o equipamento segurado contra roubo, furto, incendio e danos eletricos, com cobertura minima equivalente ao valor de reposicao do equipamento. A apolice devera indicar a World Comp como beneficiaria."""
        self.write_multiline(texto_seguro)

    def page_7_responsabilidades(self):
        """Página 7 - Responsabilidades das Partes"""
        self.add_page()
        
        self.set_font('Arial', 'B', 14)
        self.safe_cell(0, 10, 'RESPONSABILIDADES DAS PARTES', 0, 1, 'L')
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, 'RESPONSABILIDADES DA LOCADORA (WORLD COMP):', 0, 1, 'L')
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        self.safe_cell(0, 6, '• Fornecer o equipamento em perfeitas condicoes de funcionamento', 0, 1, 'L')
        self.safe_cell(0, 6, '• Realizar manutencao preventiva conforme cronograma do fabricante', 0, 1, 'L')
        self.safe_cell(0, 6, '• Providenciar reparos em caso de defeitos no equipamento', 0, 1, 'L')
        self.safe_cell(0, 6, '• Fornecer suporte tecnico durante horario comercial', 0, 1, 'L')
        self.safe_cell(0, 6, '• Substituir o equipamento em caso de defeito irreparavel', 0, 1, 'L')
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, 'RESPONSABILIDADES DO LOCATARIO:', 0, 1, 'L')
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        self.safe_cell(0, 6, '• Efetuar pagamentos nas datas acordadas', 0, 1, 'L')
        self.safe_cell(0, 6, '• Operar o equipamento conforme manual de instrucoes', 0, 1, 'L')
        self.safe_cell(0, 6, '• Manter o equipamento em local adequado e seguro', 0, 1, 'L')
        self.safe_cell(0, 6, '• Realizar verificacoes diarias basicas (nivel de oleo, pressao)', 0, 1, 'L')
        self.safe_cell(0, 6, '• Comunicar imediatamente qualquer problema ou defeito', 0, 1, 'L')
        self.safe_cell(0, 6, '• Permitir acesso para manutencao e vistoria', 0, 1, 'L')
        self.safe_cell(0, 6, '• Devolver o equipamento nas mesmas condicoes recebidas', 0, 1, 'L')
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, 'CUSTOS POR CONTA DO LOCATARIO:', 0, 1, 'L')
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        self.safe_cell(0, 6, '• Energia eletrica consumida pelo equipamento', 0, 1, 'L')
        self.safe_cell(0, 6, '• Oleo lubrificante e filtros (reposicao entre manutencoes)', 0, 1, 'L')
        self.safe_cell(0, 6, '• Danos causados por mau uso ou operacao inadequada', 0, 1, 'L')
        self.safe_cell(0, 6, '• Frete para devolucao ao final do contrato', 0, 1, 'L')

    def page_8_garantias(self):
        """Página 8 - Garantias e Assistência Técnica"""
        self.add_page()
        
        self.set_font('Arial', 'B', 14)
        self.safe_cell(0, 10, 'GARANTIAS E ASSISTENCIA TECNICA', 0, 1, 'L')
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, 'GARANTIA DE FUNCIONAMENTO:', 0, 1, 'L')
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        texto_garantia = """A World Comp garante o perfeito funcionamento do equipamento durante todo o periodo de locacao, desde que utilizado conforme especificacoes tecnicas e operado adequadamente pelo locatario."""
        self.write_multiline(texto_garantia)
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, 'ASSISTENCIA TECNICA:', 0, 1, 'L')
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        self.safe_cell(0, 6, '• Atendimento telefonico: Segunda a sexta, 8h as 18h', 0, 1, 'L')
        self.safe_cell(0, 6, '• Atendimento emergencial: Conforme disponibilidade', 0, 1, 'L')
        self.safe_cell(0, 6, '• Tempo de resposta: Ate 24h para chamados urgentes', 0, 1, 'L')
        self.safe_cell(0, 6, '• Manutencao preventiva: Conforme cronograma do fabricante', 0, 1, 'L')
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, 'LIMITACOES DA GARANTIA:', 0, 1, 'L')
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        texto_limitacoes = """A garantia nao cobre danos causados por: uso inadequado, sobrecarga, falta de manutencao basica, interferencia de terceiros, condicoes ambientais adversas, falta de energia eletrica ou variacao de tensao fora dos padroes especificados."""
        self.write_multiline(texto_limitacoes)
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, 'PROCEDIMENTOS PARA ACIONAMENTO:', 0, 1, 'L')
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        self.safe_cell(0, 6, '1. Comunicar o problema via telefone ou email', 0, 1, 'L')
        self.safe_cell(0, 6, '2. Fornecer informacoes detalhadas sobre o defeito', 0, 1, 'L')
        self.safe_cell(0, 6, '3. Aguardar orientacoes da equipe tecnica', 0, 1, 'L')
        self.safe_cell(0, 6, '4. Permitir acesso ao equipamento para diagnostico', 0, 1, 'L')

    def page_9_instalacao_manutencao(self):
        """Página 9 - Instalação e Manutenção"""
        self.add_page()
        
        self.set_font('Arial', 'B', 14)
        self.safe_cell(0, 10, 'INSTALACAO E MANUTENCAO', 0, 1, 'L')
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, 'INSTALACAO DO EQUIPAMENTO:', 0, 1, 'L')
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        texto_instalacao = """A instalacao do equipamento sera realizada pela equipe tecnica da World Comp ou empresa credenciada. O local de instalacao devera atender aos requisitos tecnicos especificados, incluindo espaco adequado, ventilacao, alimentacao eletrica e drenagem."""
        self.write_multiline(texto_instalacao)
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, 'REQUISITOS DO LOCAL:', 0, 1, 'L')
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        self.safe_cell(0, 6, '• Area minima: Conforme especificacao tecnica do modelo', 0, 1, 'L')
        self.safe_cell(0, 6, '• Ventilacao adequada para dissipacao de calor', 0, 1, 'L')
        self.safe_cell(0, 6, '• Alimentacao eletrica conforme potencia do equipamento', 0, 1, 'L')
        self.safe_cell(0, 6, '• Piso nivelado e com capacidade de suporte adequada', 0, 1, 'L')
        self.safe_cell(0, 6, '• Drenagem para condensado', 0, 1, 'L')
        self.safe_cell(0, 6, '• Protecao contra intemperies', 0, 1, 'L')
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, 'PROGRAMA DE MANUTENCAO:', 0, 1, 'L')
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        self.safe_cell(0, 6, '• Manutencao preventiva: Conforme horas de operacao', 0, 1, 'L')
        self.safe_cell(0, 6, '• Troca de oleo: A cada 2000 horas ou conforme especificacao', 0, 1, 'L')
        self.safe_cell(0, 6, '• Substituicao de filtros: Conforme cronograma', 0, 1, 'L')
        self.safe_cell(0, 6, '• Inspecoes periodicas: Conforme plano de manutencao', 0, 1, 'L')
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, 'MANUTENCAO CORRETIVA:', 0, 1, 'L')
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        texto_corretiva = """Em caso de defeito ou falha do equipamento, a World Comp providenciara o reparo no menor prazo possivel, utilizando pecas originais ou equivalentes aprovadas pelo fabricante. Se necessario, sera fornecido equipamento substituto temporario."""
        self.write_multiline(texto_corretiva)

    def page_10_clausulas_gerais(self):
        """Página 10 - Cláusulas Gerais"""
        self.add_page()
        
        self.set_font('Arial', 'B', 14)
        self.safe_cell(0, 10, 'CLAUSULAS GERAIS', 0, 1, 'L')
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, '1. INADIMPLENCIA:', 0, 1, 'L')
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        texto_inadimplencia = """O atraso no pagamento superior a 15 dias autoriza a locadora a considerar rescindido o contrato, independente de notificacao judicial, podendo retirar o equipamento imediatamente."""
        self.write_multiline(texto_inadimplencia)
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, '2. FORCA MAIOR:', 0, 1, 'L')
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        texto_forca_maior = """Nenhuma das partes sera responsabilizada por atrasos ou impossibilidade de cumprimento das obrigacoes contratuais decorrentes de caso fortuito ou forca maior."""
        self.write_multiline(texto_forca_maior)
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, '3. TRANSFERENCIA:', 0, 1, 'L')
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        texto_transferencia = """E vedada a transferencia, sublocacao ou cessao do equipamento a terceiros sem autorizacao expressa e por escrito da locadora."""
        self.write_multiline(texto_transferencia)
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, '4. MODIFICACOES:', 0, 1, 'L')
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        texto_modificacoes = """Qualquer modificacao neste contrato devera ser feita por escrito e assinada por ambas as partes."""
        self.write_multiline(texto_modificacoes)
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, '5. FORO:', 0, 1, 'L')
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        texto_foro = """Fica eleito o foro da comarca de Sao Bernardo do Campo - SP para dirimir quaisquer duvidas ou questoes oriundas deste contrato."""
        self.write_multiline(texto_foro)

    def page_11_rescisao(self):
        """Página 11 - Rescisão e Devolução"""
        self.add_page()
        
        self.set_font('Arial', 'B', 14)
        self.safe_cell(0, 10, 'RESCISAO E DEVOLUCAO', 0, 1, 'L')
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, 'RESCISAO ANTECIPADA:', 0, 1, 'L')
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        texto_rescisao = """O contrato podera ser rescindido antecipadamente por qualquer das partes, mediante aviso previo de 30 dias. Em caso de rescisao pelo locatario antes do prazo minimo de 6 meses, sera cobrada multa equivalente a 2 meses de locacao."""
        self.write_multiline(texto_rescisao)
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, 'DEVOLUCAO DO EQUIPAMENTO:', 0, 1, 'L')
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        self.safe_cell(0, 6, '• O equipamento devera ser devolvido nas mesmas condicoes', 0, 1, 'L')
        self.safe_cell(0, 6, '• Limpeza e inspecao serao realizadas na devolucao', 0, 1, 'L')
        self.safe_cell(0, 6, '• Eventuais danos serao cobrados do locatario', 0, 1, 'L')
        self.safe_cell(0, 6, '• Frete de devolucao por conta do locatario', 0, 1, 'L')
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, 'MOTIVOS PARA RESCISAO IMEDIATA:', 0, 1, 'L')
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        self.safe_cell(0, 6, '• Inadimplencia superior a 15 dias', 0, 1, 'L')
        self.safe_cell(0, 6, '• Uso inadequado ou danos intencionais', 0, 1, 'L')
        self.safe_cell(0, 6, '• Transferencia nao autorizada do equipamento', 0, 1, 'L')
        self.safe_cell(0, 6, '• Descumprimento grave das clausulas contratuais', 0, 1, 'L')
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, 'PROCEDIMENTOS DE DEVOLUCAO:', 0, 1, 'L')
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        texto_procedimentos = """Ao final do contrato ou em caso de rescisao, o locatario devera agendar a retirada do equipamento com antecedencia minima de 5 dias uteis. O equipamento sera inspecionado e eventual laudo de condicoes sera emitido."""
        self.write_multiline(texto_procedimentos)

    def page_12_disposicoes_finais(self):
        """Página 12 - Disposições Finais"""
        self.add_page()
        
        self.set_font('Arial', 'B', 14)
        self.safe_cell(0, 10, 'DISPOSICOES FINAIS', 0, 1, 'L')
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, 'VALIDADE DA PROPOSTA:', 0, 1, 'L')
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        self.safe_cell(0, 6, 'Esta proposta tem validade de 30 dias a partir da data de emissao.', 0, 1, 'L')
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, 'DOCUMENTOS NECESSARIOS:', 0, 1, 'L')
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        self.safe_cell(0, 6, '• Contrato social da empresa', 0, 1, 'L')
        self.safe_cell(0, 6, '• Cartao CNPJ atualizado', 0, 1, 'L')
        self.safe_cell(0, 6, '• Comprovante de endereco', 0, 1, 'L')
        self.safe_cell(0, 6, '• Referencias comerciais', 0, 1, 'L')
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, 'CONDICOES DE APROVACAO:', 0, 1, 'L')
        self.ln(5)
        
        self.set_font('Arial', '', 10)
        texto_aprovacao = """A efetivacao da locacao esta condicionada a aprovacao do cadastro e analise de credito do locatario, bem como apresentacao da documentacao completa."""
        self.write_multiline(texto_aprovacao)
        self.ln(10)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, 'CONTATOS PARA DUVIDAS:', 0, 1, 'L')
        self.ln(5)
        
        telefones = self.filial.get('telefones', '(11) 4543-6896')
        email = self.filial.get('email', 'rogerio@worldcompressores.com.br')
        
        self.set_font('Arial', '', 10)
        self.safe_cell(0, 6, f'Telefone: {safe_text_for_pdf(telefones)}', 0, 1, 'L')
        self.safe_cell(0, 6, f'Email: {safe_text_for_pdf(email)}', 0, 1, 'L')
        self.ln(15)
        
        self.set_font('Arial', '', 10)
        self.safe_cell(0, 6, 'Agradecemos a oportunidade e aguardamos sua aprovacao.', 0, 1, 'L')
        self.ln(5)
        self.set_font('Arial', 'B', 10)
        self.safe_cell(0, 6, 'Atenciosamente,', 0, 1, 'L')
        self.safe_cell(0, 6, 'WORLD COMP DO BRASIL COMPRESSORES LTDA', 0, 1, 'L')

    def page_13_assinaturas(self):
        """Página 13 - Assinaturas e Aceite"""
        self.add_page()
        
        self.set_font('Arial', 'B', 14)
        self.safe_cell(0, 10, 'ACEITE E ASSINATURAS', 0, 1, 'C')
        self.ln(20)
        
        # Data e local
        self.set_font('Arial', '', 10)
        data_hoje = datetime.now().strftime("%d/%m/%Y")
        self.safe_cell(0, 6, f'Sao Bernardo do Campo, {data_hoje}', 0, 1, 'L')
        self.ln(20)
        
        # Espaço para assinaturas
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, 'LOCADORA:', 0, 1, 'L')
        self.ln(20)
        
        self.set_font('Arial', '', 10)
        self.safe_cell(0, 6, '___________________________________________', 0, 1, 'L')
        self.safe_cell(0, 6, 'WORLD COMP DO BRASIL COMPRESSORES LTDA', 0, 1, 'L')
        self.safe_cell(0, 6, 'CNPJ: 22.790.603/0001-77', 0, 1, 'L')
        self.safe_cell(0, 6, 'Representante Legal', 0, 1, 'L')
        self.ln(30)
        
        self.set_font('Arial', 'B', 12)
        self.safe_cell(0, 8, 'LOCATARIO:', 0, 1, 'L')
        self.ln(20)
        
        cliente_nome = 'CLIENTE'
        if self.cliente:
            cliente_nome = self.cliente[1] or self.cliente[0]
        
        # Garantir que o nome do cliente não tenha underscores
        cliente_nome = safe_text_for_pdf(cliente_nome)
        if not cliente_nome or cliente_nome.strip() == '' or cliente_nome.strip() == ' ':
            cliente_nome = 'CLIENTE'
        
        self.set_font('Arial', '', 10)
        self.safe_cell(0, 6, '___________________________________________', 0, 1, 'L')
        self.safe_cell(0, 6, cliente_nome, 0, 1, 'L')
        if self.cliente and len(self.cliente) > 6 and self.cliente[6]:
            self.safe_cell(0, 6, f'CNPJ: {self.cliente[6]}', 0, 1, 'L')
        self.safe_cell(0, 6, 'Representante Legal', 0, 1, 'L')
        self.ln(20)
        
        # Testemunhas
        self.set_font('Arial', 'B', 10)
        self.safe_cell(0, 6, 'TESTEMUNHAS:', 0, 1, 'L')
        self.ln(15)
        
        self.set_font('Arial', '', 10)
        self.safe_cell(100, 6, 'Nome: _______________________________', 0, 0, 'L')
        self.safe_cell(100, 6, 'Nome: _______________________________', 0, 1, 'L')
        self.safe_cell(100, 6, 'CPF: ________________________________', 0, 0, 'L')
        self.safe_cell(100, 6, 'CPF: ________________________________', 0, 1, 'L')
        self.safe_cell(100, 6, 'Assinatura: _________________________', 0, 0, 'L')
        self.safe_cell(100, 6, 'Assinatura: _________________________', 0, 1, 'L')


def gerar_pdf_locacao(dados, output_path):
    """Função principal para gerar o PDF de locação"""
    if not FPDF_AVAILABLE:
        raise RuntimeError("FPDF não está disponível. Instale com: pip install fpdf2")
    
    # Criar diretório de saída se necessário
    output_dir = os.path.dirname(output_path)
    if output_dir and output_dir != '.':
        os.makedirs(output_dir, exist_ok=True)
    
    # Gerar PDF
    pdf = LocacaoPDF(dados)
    pdf.generate_all_pages()
    
    # Salvar arquivo
    pdf.output(output_path)
    
    return output_path

