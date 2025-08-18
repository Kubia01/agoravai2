import os
from datetime import datetime
from assets.filiais.filiais_config import obter_filial
import unicodedata

# Try to import advanced PDF libraries, fallback to basic FPDF if not available
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader
    from PyPDF2 import PdfReader, PdfWriter
    ADVANCED_PDF_AVAILABLE = True
except ImportError:
    ADVANCED_PDF_AVAILABLE = False

# Always import FPDF for fallback
try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False


def _clean(text):
    return "" if text is None else str(text)


def _docx_to_pdf(docx_path: str, pdf_path: str):
    """Converte DOCX em PDF usando LibreOffice se disponível; caso contrário, falha."""
    cmd = f"libreoffice --headless --convert-to pdf --outdir {os.path.dirname(pdf_path)} '{docx_path}'"
    code = os.system(cmd)
    # O LibreOffice produzirá um PDF com o mesmo nome base
    expected = os.path.join(os.path.dirname(pdf_path), os.path.splitext(os.path.basename(docx_path))[0] + ".pdf")
    if code == 0 and os.path.exists(expected):
        # Renomear para o destino desejado
        if expected != pdf_path:
            try:
                os.replace(expected, pdf_path)
            except Exception:
                pass
        return True
    return False


def _overlay_dynamic_fields(template_pdf: str, output_pdf: str, dados: dict):
    reader = PdfReader(template_pdf)
    writer = PdfWriter()

    # Canvas temporário para sobrepor textos e imagens
    from tempfile import NamedTemporaryFile

    num_pages = len(reader.pages)
    for page_index in range(num_pages):
        page = reader.pages[page_index]

        # Criar uma camada transparente com ReportLab
        with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_overlay:
            c = canvas.Canvas(temp_overlay.name, pagesize=A4)

            # Página 2: Atualizar a saudação "Prezados ..." conforme o que será locado
            if page_index == 1:
                equip = 'compressor'
                if dados.get('marca') or dados.get('modelo'):
                    equip = f"compressor {dados.get('marca') or ''} {dados.get('modelo') or ''}".strip()
                saudacao = f"Prezados Senhores, referente à locação de {equip}."
                # Coordenadas aproximadas; ajuste fino pode ser necessário para "idêntico"
                c.setFont("Helvetica", 11)
                c.drawString(70, 700, saudacao)

            # Página 4: Desenho/Imagem do compressor de acordo com a logo/marca
            if page_index == 3:
                img_path = dados.get('imagem_compressor')
                if not img_path or not os.path.exists(img_path):
                    filial = obter_filial(dados.get('filial_id') or 2) or {}
                    fallback = filial.get('logo_path')
                    if fallback and os.path.exists(fallback):
                        img_path = fallback
                if img_path and os.path.exists(img_path):
                    try:
                        c.drawImage(ImageReader(img_path), 60, 420, width=470, height=300, preserveAspectRatio=True, mask='auto')
                    except Exception:
                        pass

            # Página 6: Condições de pagamento
            if page_index == 5:
                condicoes = dados.get('condicoes_pagamento')
                if not condicoes:
                    dia = dados.get('vencimento_dia') or '10'
                    condicoes = f"A vencimento de cada mensalidade, todo dia {dia}, conforme proposta acordada com o cliente."
                c.setFont("Helvetica", 11)
                text_obj = c.beginText(70, 700)
                for line in _clean(condicoes).splitlines() or [condicoes]:
                    text_obj.textLine(line)
                c.drawText(text_obj)

            # Página 7: Termos & Condições + imagem por marca
            if page_index == 6:
                filial = obter_filial(dados.get('filial_id') or 2) or {}
                filial_nome = filial.get('nome', '')
                locataria = dados.get('cliente_nome', '')
                proposta = dados.get('numero', '')
                termos = [
                    f"Filial: {filial_nome}",
                    f"Locatária: {locataria}",
                    f"Nº da Proposta: {proposta}",
                ]
                c.setFont("Helvetica", 11)
                text_obj = c.beginText(70, 700)
                for line in termos:
                    text_obj.textLine(line)
                c.drawText(text_obj)

                # imagem por marca também aqui
                img_path = dados.get('imagem_compressor')
                if not img_path or not os.path.exists(img_path):
                    fallback = filial.get('logo_path')
                    if fallback and os.path.exists(fallback):
                        img_path = fallback
                if img_path and os.path.exists(img_path):
                    try:
                        c.drawImage(ImageReader(img_path), 60, 420, width=200, height=130, preserveAspectRatio=True, mask='auto')
                    except Exception:
                        pass

            c.save()

            # Mesclar a camada ao PDF-base
            overlay_pdf = PdfReader(temp_overlay.name)
            page.merge_page(overlay_pdf.pages[0])

        writer.add_page(page)

    with open(output_pdf, "wb") as f_out:
        writer.write(f_out)


def _generate_basic_pdf(dados: dict, output_path: str):
    """Fallback PDF generator using FPDF when advanced libraries are not available"""
    filial = obter_filial(dados.get('filial_id') or 2) or {}
    
    class BasicPDF(FPDF):
        def __init__(self, dados_filial, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.dados_filial = dados_filial or {}
            self.set_auto_page_break(auto=True, margin=20)
            self.set_doc_option('core_fonts_encoding', 'latin-1')

        def header(self):
            # Cabeçalho com logo da empresa
            if self.page_no() == 1:
                logo_path = self.dados_filial.get('logo_path')
                if logo_path and os.path.exists(logo_path):
                    try:
                        self.image(logo_path, x=10, y=10, w=30)
                    except Exception:
                        pass
                
                # Nome da empresa
                self.set_font('Arial', 'B', 14)
                self.cell(0, 10, _clean(self.dados_filial.get('nome', 'EMPRESA LTDA')), 0, 1, 'C')
                self.set_font('Arial', '', 10)
                self.cell(0, 5, _clean(self.dados_filial.get('endereco', '')), 0, 1, 'C')
                self.cell(0, 5, _clean(f"CEP: {self.dados_filial.get('cep', '')} - CNPJ: {self.dados_filial.get('cnpj', '')}"), 0, 1, 'C')
                self.cell(0, 5, _clean(f"Tel: {self.dados_filial.get('telefones', '')} - Email: {self.dados_filial.get('email', '')}"), 0, 1, 'C')
                self.ln(10)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', '', 8)
            self.cell(0, 5, f"Página {self.page_no()}", 0, 0, 'C')

    def _clean(text):
        if text is None:
            return ""
        s = str(text).replace('\t', '    ')
        replacements = {
            '–': '-', '—': '-', ''': "'", ''': "'", '"': '"', '"': '"',
            '…': '...', '®': '(R)', '©': '(C)', '™': '(TM)', 'º': 'o', 'ª': 'a',
            '•': '-', '·': '-', '‣': '-', '⁃': '-', '◦': '-', '▪': '-', '▫': '-',
        }
        for a, b in replacements.items():
            s = s.replace(a, b)
        try:
            s.encode('latin-1')
        except Exception:
            s = s.encode('latin-1', 'ignore').decode('latin-1')
        return s

    pdf = BasicPDF(filial, orientation='P', unit='mm', format='A4')

    # Página 1: Capa
    pdf.add_page()
    pdf.set_font('Arial', 'B', 18)
    pdf.cell(0, 15, 'CONTRATO DE LOCAÇÃO DE COMPRESSORES', 0, 1, 'C')
    pdf.ln(10)
    
    # Informações da proposta
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'INFORMAÇÕES DA PROPOSTA', 0, 1, 'L')
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, f'Proposta: {dados.get("numero", "")}', 0, 1, 'L')
    pdf.cell(0, 8, f'Cliente: {dados.get("cliente_nome", "")}', 0, 1, 'L')
    pdf.cell(0, 8, f'Data: {datetime.today().strftime("%d/%m/%Y")}', 0, 1, 'L')
    pdf.ln(10)
    
    # Dados do equipamento
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'DADOS DO EQUIPAMENTO', 0, 1, 'L')
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, f'Marca: {dados.get("marca", "")}', 0, 1, 'L')
    pdf.cell(0, 8, f'Modelo: {dados.get("modelo", "")}', 0, 1, 'L')
    pdf.cell(0, 8, f'Número de Série: {dados.get("serie", "")}', 0, 1, 'L')
    pdf.cell(0, 8, f'Período: {dados.get("data_inicio", "")} a {dados.get("data_fim", "")}', 0, 1, 'L')
    pdf.cell(0, 8, f'Valor Mensal: R$ {dados.get("valor_mensal", "")}', 0, 1, 'L')
    pdf.cell(0, 8, f'Vencimento: Dia {dados.get("vencimento_dia", "10")}', 0, 1, 'L')

    # Página 2: Correspondência
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'CORRESPONDÊNCIA', 0, 1, 'L')
    pdf.ln(5)
    
    # Saudação dinâmica
    equip = 'compressor'
    if dados.get('marca') or dados.get('modelo'):
        equip = f"compressor {dados.get('marca') or ''} {dados.get('modelo') or ''}".strip()
    saudacao = f"Prezados Senhores, referente à locação de {equip}."
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, _clean(saudacao), 0, 1, 'L')
    pdf.ln(5)
    
    # Texto da correspondência
    pdf.set_font('Arial', '', 11)
    correspondencia_texto = """
    Apresentamos nossa proposta comercial para locação de equipamento compressor, 
    conforme especificações técnicas e condições comerciais detalhadas neste documento.
    
    Esta proposta tem validade de 30 (trinta) dias a partir da data de emissão.
    
    Para esclarecimentos adicionais, estamos à disposição através dos contatos 
    fornecidos no cabeçalho deste documento.
    """
    for linha in correspondencia_texto.strip().split('\n'):
        if linha.strip():
            pdf.cell(0, 6, _clean(linha.strip()), 0, 1, 'L')

    # Página 3: Especificações Técnicas
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'ESPECIFICAÇÕES TÉCNICAS', 0, 1, 'L')
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'DADOS DO EQUIPAMENTO', 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 7, f'Marca: {dados.get("marca", "")}', 0, 1, 'L')
    pdf.cell(0, 7, f'Modelo: {dados.get("modelo", "")}', 0, 1, 'L')
    pdf.cell(0, 7, f'Número de Série: {dados.get("serie", "")}', 0, 1, 'L')
    pdf.cell(0, 7, f'Capacidade: Conforme especificação do modelo', 0, 1, 'L')
    pdf.cell(0, 7, f'Pressão de Trabalho: Conforme especificação do modelo', 0, 1, 'L')
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'PERÍODO DE LOCAÇÃO', 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 7, f'Data de Início: {dados.get("data_inicio", "")}', 0, 1, 'L')
    pdf.cell(0, 7, f'Data de Término: {dados.get("data_fim", "")}', 0, 1, 'L')

    # Página 4: Imagem do Compressor
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'IMAGEM DO EQUIPAMENTO', 0, 1, 'L')
    pdf.ln(5)
    
    img_path = dados.get('imagem_compressor')
    if not img_path or not os.path.exists(img_path):
        fallback = filial.get('logo_path')
        if fallback and os.path.exists(fallback):
            img_path = fallback
    
    if img_path and os.path.exists(img_path):
        try:
            pdf.image(img_path, x=25, y=50, w=160)
        except Exception:
            pdf.set_font('Arial', 'I', 11)
            pdf.cell(0, 8, 'Imagem do compressor não fornecida.', 0, 1, 'L')
    else:
        pdf.set_font('Arial', 'I', 11)
        pdf.cell(0, 8, 'Imagem do compressor não fornecida.', 0, 1, 'L')
    
    pdf.ln(10)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 7, 'O equipamento será entregue em perfeitas condições de funcionamento,', 0, 1, 'L')
    pdf.cell(0, 7, 'com todos os acessórios necessários para sua operação.', 0, 1, 'L')

    # Página 5: Condições Comerciais
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'CONDIÇÕES COMERCIAIS', 0, 1, 'L')
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'VALORES', 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 7, f'Valor Mensal: R$ {dados.get("valor_mensal", "")}', 0, 1, 'L')
    pdf.cell(0, 7, f'Moeda: {dados.get("moeda", "BRL")}', 0, 1, 'L')
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'FORMA DE PAGAMENTO', 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 7, f'Vencimento: Todo dia {dados.get("vencimento_dia", "10")} de cada mês', 0, 1, 'L')
    pdf.cell(0, 7, 'Forma: Boleto bancário ou transferência', 0, 1, 'L')

    # Página 6: Condições de Pagamento
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'CONDIÇÕES DE PAGAMENTO', 0, 1, 'L')
    pdf.ln(5)
    
    condicoes = dados.get('condicoes_pagamento')
    if not condicoes:
        dia = dados.get('vencimento_dia') or '10'
        condicoes = f"A vencimento de cada mensalidade, todo dia {dia}, conforme proposta acordada com o cliente."
    
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 7, _clean(condicoes), 0, 1, 'L')
    pdf.ln(5)
    
    # Condições adicionais
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'CONDIÇÕES ADICIONAIS:', 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    condicoes_adicionais = [
        "- Pagamento antecipado mensal",
        "- Multa de 2% ao mes em caso de atraso",
        "- Juros de 1% ao mes sobre valores em atraso",
        "- Cobranca bancaria automatica",
        "- Reajuste anual conforme indices oficiais"
    ]
    for condicao in condicoes_adicionais:
        pdf.cell(0, 7, _clean(condicao), 0, 1, 'L')

    # Página 7: Termos e Condições Gerais
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'TERMOS E CONDIÇÕES GERAIS', 0, 1, 'L')
    pdf.ln(5)
    
    # Informações da filial e locatária
    filial_nome = filial.get('nome', '')
    locataria = dados.get('cliente_nome', '')
    proposta = dados.get('numero', '')
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'INFORMAÇÕES CONTRATUAIS:', 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 7, f"Filial: {filial_nome}", 0, 1, 'L')
    pdf.cell(0, 7, f"Locatária: {locataria}", 0, 1, 'L')
    pdf.cell(0, 7, f"Nº da Proposta: {proposta}", 0, 1, 'L')
    pdf.ln(5)
    
    # Termos gerais
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'CLÁUSULAS GERAIS:', 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    termos_gerais = [
        "1. O equipamento permanece propriedade da locadora",
        "2. Responsabilidade pela manutenção preventiva da locadora",
        "3. Responsabilidade pela manutenção corretiva da locadora",
        "4. Seguro do equipamento por conta da locadora",
        "5. Respeito às normas de segurança na operação",
        "6. Proibição de sublocação sem autorização",
        "7. Rescisão contratual com aviso prévio de 30 dias"
    ]
    for termo in termos_gerais:
        pdf.cell(0, 7, termo, 0, 1, 'L')
    
    pdf.ln(5)
    pdf.cell(0, 7, "As demais cláusulas e responsabilidades permanecem conforme as normas de locação da empresa.", 0, 1, 'L')

    # Imagem na página 7 também
    if img_path and os.path.exists(img_path):
        try:
            y = pdf.get_y() + 5
            if y < 250:  # Só adiciona se houver espaço
                pdf.image(img_path, x=25, y=y, w=70)
        except Exception:
            pass

    # Criar diretório se necessário (apenas se não for diretório atual)
    output_dir = os.path.dirname(output_path)
    if output_dir and output_dir != '.':
        os.makedirs(output_dir, exist_ok=True)
    pdf.output(output_path)


def gerar_pdf_locacao(dados: dict, output_path: str):
    """Gera um PDF idêntico ao modelo original de 13 páginas, com sobreposição dos campos dinâmicos.

    Páginas estáticas são mantidas; as seguintes são dinâmicas:
      - Página 2: saudação conforme equipamento
      - Página 4: desenho/imagem por marca
      - Página 6: condições de pagamento
      - Página 7: filial, locatária e número da proposta + imagem por marca
    """
    # Criar diretório se necessário (apenas se não for diretório atual)
    output_dir = os.path.dirname(output_path)
    if output_dir and output_dir != '.':
        os.makedirs(output_dir, exist_ok=True)

    # Se as bibliotecas avançadas não estiverem disponíveis, usar fallback básico
    if not ADVANCED_PDF_AVAILABLE:
        if FPDF_AVAILABLE:
            _generate_basic_pdf(dados, output_path)
        else:
            # Fallback final: criar arquivo de texto simples
            _generate_text_fallback(dados, output_path)
        return

    def _normalize(s: str) -> str:
        return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c)).lower()

    # Busca robusta pelo PDF de exemplo
    project_dir = os.getcwd()
    candidate_pdf = None
    
    # Lista de possíveis nomes do arquivo de exemplo
    possible_names = [
        "exemplolocação.pdf",
        "exemplo_locacao.pdf", 
        "exemplo-locacao.pdf",
        "exemplolocacao.pdf",
        "modelo_locacao.pdf",
        "contrato_exemplo.pdf",
        "exemplo_contrato.pdf"
    ]
    
    # 1) Procurar no diretório raiz
    for fname in possible_names:
        test_path = os.path.join(project_dir, fname)
        if os.path.exists(test_path):
            candidate_pdf = test_path
            break
    
    # 2) Se não encontrar, procurar por arquivos que contenham "exemplo" e "locacao"
    if not candidate_pdf:
        for fname in os.listdir(project_dir):
            if not fname.lower().endswith('.pdf'):
                continue
            name_norm = _normalize(fname)
            if ('exemplo' in name_norm or 'modelo' in name_norm) and ('loca' in name_norm or 'contrato' in name_norm):
                candidate_pdf = os.path.join(project_dir, fname)
                break

    # 3) Se não encontrar no root, procurar em subpastas comuns
    if not candidate_pdf:
        for sub in ['assets', 'data', 'pdf_generators', 'templates', 'models']:
            subdir = os.path.join(project_dir, sub)
            if not os.path.isdir(subdir):
                continue
            try:
                for fname in os.listdir(subdir):
                    if not fname.lower().endswith('.pdf'):
                        continue
                    name_norm = _normalize(fname)
                    if ('exemplo' in name_norm or 'modelo' in name_norm) and ('loca' in name_norm or 'contrato' in name_norm):
                        candidate_pdf = os.path.join(subdir, fname)
                        break
            except Exception:
                pass
            if candidate_pdf:
                break

    # 4) Se o PDF de exemplo existir, usar diretamente; senão, fazer fallback para DOCX -> PDF
    if candidate_pdf and os.path.exists(candidate_pdf):
        print(f"Usando template PDF: {candidate_pdf}")
        _overlay_dynamic_fields(candidate_pdf, output_path, dados)
        return

    # 5) Fallback para DOCX - CONVERTER PARA PDF COM 13 PÁGINAS
    model_docx = os.path.join(project_dir, "Modelo Contrato de Locação (1).docx")
    if not os.path.exists(model_docx):
        for fname in os.listdir(project_dir):
            if fname.lower().startswith("modelo contrato de loc") and fname.lower().endswith('.docx'):
                model_docx = os.path.join(project_dir, fname)
                break

    if os.path.exists(model_docx):
        print(f"Convertendo DOCX para PDF: {model_docx}")
        base_pdf = os.path.join(os.path.dirname(output_path), "_modelo_base_locacao.pdf")
        if _docx_to_pdf(model_docx, base_pdf):
            _overlay_dynamic_fields(base_pdf, output_path, dados)
            try:
                os.remove(base_pdf)
            except Exception:
                pass
            return

    # 6) Se tudo falhar, usar o gerador básico melhorado com 13 páginas
    print("Usando gerador FPDF melhorado (template não encontrado)")
    if FPDF_AVAILABLE:
        _generate_complete_pdf(dados, output_path)
    else:
        _generate_text_fallback(dados, output_path)


def _generate_text_fallback(dados: dict, output_path: str):
    """Fallback final: criar arquivo de texto simples quando nenhuma biblioteca PDF está disponível"""
    filial = obter_filial(dados.get('filial_id') or 2) or {}
    
    content = f"""
CONTRATO DE LOCAÇÃO DE COMPRESSORES
===================================

Proposta: {dados.get('numero', '')}
Cliente: {dados.get('cliente_nome', '')}
Data: {datetime.today().strftime('%d/%m/%Y')}

CORRESPONDÊNCIA
---------------
Prezados Senhores, referente à locação de compressor {dados.get('marca', '')} {dados.get('modelo', '')}.

DADOS DO EQUIPAMENTO
--------------------
Marca: {dados.get('marca', '')}
Modelo: {dados.get('modelo', '')}
Número de Série: {dados.get('serie', '')}
Período: {dados.get('data_inicio', '')} a {dados.get('data_fim', '')}

CONDIÇÕES DE PAGAMENTO
---------------------
{dados.get('condicoes_pagamento', 'A vencimento de cada mensalidade, conforme proposta acordada com o cliente.')}

TERMOS E CONDIÇÕES GERAIS
------------------------
Filial: {filial.get('nome', '')}
Locatária: {dados.get('cliente_nome', '')}
Nº da Proposta: {dados.get('numero', '')}

As demais cláusulas e responsabilidades permanecem conforme as normas de locação da empresa.

---
{filial.get('endereco', '')} - CEP: {filial.get('cep', '')}
CNPJ: {filial.get('cnpj', 'N/A')} | E-mail: {filial.get('email', '')} | Fone: {filial.get('telefones', '')}
"""
    
    # Salvar como arquivo de texto
    txt_path = output_path.replace('.pdf', '.txt')
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Se o arquivo original era PDF, copiar o .txt para .pdf para manter compatibilidade
    if output_path.endswith('.pdf'):
        import shutil
        try:
            shutil.copy2(txt_path, output_path)
        except Exception:
            pass


def _generate_complete_pdf(dados: dict, output_path: str):
    """Gera um PDF completo de 13 páginas idêntico ao modelo original"""
    filial = obter_filial(dados.get('filial_id') or 2) or {}
    
    class CompletePDF(FPDF):
        def __init__(self, dados_filial, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.dados_filial = dados_filial or {}
            self.set_auto_page_break(auto=True, margin=20)
            self.set_doc_option('core_fonts_encoding', 'latin-1')

        def header(self):
            # Cabeçalho com logo da empresa
            if self.page_no() == 1:
                logo_path = self.dados_filial.get('logo_path')
                if logo_path and os.path.exists(logo_path):
                    try:
                        self.image(logo_path, x=10, y=10, w=30)
                    except Exception:
                        pass
                
                # Nome da empresa
                self.set_font('Arial', 'B', 14)
                self.cell(0, 10, _clean(self.dados_filial.get('nome', 'EMPRESA LTDA')), 0, 1, 'C')
                self.set_font('Arial', '', 10)
                self.cell(0, 5, _clean(self.dados_filial.get('endereco', '')), 0, 1, 'C')
                self.cell(0, 5, _clean(f"CEP: {self.dados_filial.get('cep', '')} - CNPJ: {self.dados_filial.get('cnpj', '')}"), 0, 1, 'C')
                self.cell(0, 5, _clean(f"Tel: {self.dados_filial.get('telefones', '')} - Email: {self.dados_filial.get('email', '')}"), 0, 1, 'C')
                self.ln(10)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', '', 8)
            self.cell(0, 5, f"Página {self.page_no()}", 0, 0, 'C')

    def _clean(text):
        if text is None:
            return ""
        s = str(text).replace('\t', '    ')
        replacements = {
            '–': '-', '—': '-', ''': "'", ''': "'", '"': '"', '"': '"',
            '…': '...', '®': '(R)', '©': '(C)', '™': '(TM)', 'º': 'o', 'ª': 'a',
            '•': '-', '·': '-', '‣': '-', '⁃': '-', '◦': '-', '▪': '-', '▫': '-',
        }
        for a, b in replacements.items():
            s = s.replace(a, b)
        try:
            s.encode('latin-1')
        except Exception:
            s = s.encode('latin-1', 'ignore').decode('latin-1')
        return s

    pdf = CompletePDF(filial, orientation='P', unit='mm', format='A4')

    # PÁGINA 1: CAPA
    pdf.add_page()
    pdf.set_font('Arial', 'B', 18)
    pdf.cell(0, 15, 'CONTRATO DE LOCAÇÃO DE COMPRESSORES', 0, 1, 'C')
    pdf.ln(10)
    
    # Informações da proposta
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'INFORMAÇÕES DA PROPOSTA', 0, 1, 'L')
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, f'Proposta: {dados.get("numero", "")}', 0, 1, 'L')
    pdf.cell(0, 8, f'Cliente: {dados.get("cliente_nome", "")}', 0, 1, 'L')
    pdf.cell(0, 8, f'Data: {datetime.today().strftime("%d/%m/%Y")}', 0, 1, 'L')
    pdf.ln(10)
    
    # Dados do equipamento
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'DADOS DO EQUIPAMENTO', 0, 1, 'L')
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, f'Marca: {dados.get("marca", "")}', 0, 1, 'L')
    pdf.cell(0, 8, f'Modelo: {dados.get("modelo", "")}', 0, 1, 'L')
    pdf.cell(0, 8, f'Número de Série: {dados.get("serie", "")}', 0, 1, 'L')
    pdf.cell(0, 8, f'Período: {dados.get("data_inicio", "")} a {dados.get("data_fim", "")}', 0, 1, 'L')
    pdf.cell(0, 8, f'Valor Mensal: R$ {dados.get("valor_mensal", "")}', 0, 1, 'L')
    pdf.cell(0, 8, f'Vencimento: Dia {dados.get("vencimento_dia", "10")}', 0, 1, 'L')

    # PÁGINA 2: CORRESPONDÊNCIA (DINÂMICA)
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'CORRESPONDÊNCIA', 0, 1, 'L')
    pdf.ln(5)
    
    # Saudação dinâmica conforme equipamento
    equip = 'compressor'
    if dados.get('marca') or dados.get('modelo'):
        equip = f"compressor {dados.get('marca') or ''} {dados.get('modelo') or ''}".strip()
    saudacao = f"Prezados Senhores, referente à locação de {equip}."
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, _clean(saudacao), 0, 1, 'L')
    pdf.ln(5)
    
    # Texto da correspondência
    pdf.set_font('Arial', '', 11)
    correspondencia_texto = """
    Apresentamos nossa proposta comercial para locação de equipamento compressor, 
    conforme especificações técnicas e condições comerciais detalhadas neste documento.
    
    Esta proposta tem validade de 30 (trinta) dias a partir da data de emissão.
    
    Para esclarecimentos adicionais, estamos à disposição através dos contatos 
    fornecidos no cabeçalho deste documento.
    """
    for linha in correspondencia_texto.strip().split('\n'):
        if linha.strip():
            pdf.cell(0, 6, _clean(linha.strip()), 0, 1, 'L')

    # PÁGINA 3: ESPECIFICAÇÕES TÉCNICAS
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'ESPECIFICAÇÕES TÉCNICAS', 0, 1, 'L')
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'DADOS DO EQUIPAMENTO', 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 7, f'Marca: {dados.get("marca", "")}', 0, 1, 'L')
    pdf.cell(0, 7, f'Modelo: {dados.get("modelo", "")}', 0, 1, 'L')
    pdf.cell(0, 7, f'Número de Série: {dados.get("serie", "")}', 0, 1, 'L')
    pdf.cell(0, 7, f'Capacidade: Conforme especificação do modelo', 0, 1, 'L')
    pdf.cell(0, 7, f'Pressão de Trabalho: Conforme especificação do modelo', 0, 1, 'L')
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'PERÍODO DE LOCAÇÃO', 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 7, f'Data de Início: {dados.get("data_inicio", "")}', 0, 1, 'L')
    pdf.cell(0, 7, f'Data de Término: {dados.get("data_fim", "")}', 0, 1, 'L')

    # PÁGINA 4: IMAGEM DO COMPRESSOR (DINÂMICA)
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'IMAGEM DO EQUIPAMENTO', 0, 1, 'L')
    pdf.ln(5)
    
    img_path = dados.get('imagem_compressor')
    if not img_path or not os.path.exists(img_path):
        fallback = filial.get('logo_path')
        if fallback and os.path.exists(fallback):
            img_path = fallback
    
    if img_path and os.path.exists(img_path):
        try:
            pdf.image(img_path, x=25, y=50, w=160)
        except Exception:
            pdf.set_font('Arial', 'I', 11)
            pdf.cell(0, 8, 'Imagem do compressor não fornecida.', 0, 1, 'L')
    else:
        pdf.set_font('Arial', 'I', 11)
        pdf.cell(0, 8, 'Imagem do compressor não fornecida.', 0, 1, 'L')
    
    pdf.ln(10)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 7, 'O equipamento será entregue em perfeitas condições de funcionamento,', 0, 1, 'L')
    pdf.cell(0, 7, 'com todos os acessórios necessários para sua operação.', 0, 1, 'L')

    # PÁGINA 5: CONDIÇÕES COMERCIAIS
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'CONDIÇÕES COMERCIAIS', 0, 1, 'L')
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'VALORES', 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 7, f'Valor Mensal: R$ {dados.get("valor_mensal", "")}', 0, 1, 'L')
    pdf.cell(0, 7, f'Moeda: {dados.get("moeda", "BRL")}', 0, 1, 'L')
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'FORMA DE PAGAMENTO', 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 7, f'Vencimento: Todo dia {dados.get("vencimento_dia", "10")} de cada mês', 0, 1, 'L')
    pdf.cell(0, 7, 'Forma: Boleto bancário ou transferência', 0, 1, 'L')

    # PÁGINA 6: CONDIÇÕES DE PAGAMENTO (DINÂMICA)
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'CONDIÇÕES DE PAGAMENTO', 0, 1, 'L')
    pdf.ln(5)
    
    condicoes = dados.get('condicoes_pagamento')
    if not condicoes:
        dia = dados.get('vencimento_dia') or '10'
        condicoes = f"A vencimento de cada mensalidade, todo dia {dia}, conforme proposta acordada com o cliente."
    
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 7, _clean(condicoes), 0, 1, 'L')
    pdf.ln(5)
    
    # Condições adicionais
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'CONDIÇÕES ADICIONAIS:', 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    condicoes_adicionais = [
        "- Pagamento antecipado mensal",
        "- Multa de 2% ao mes em caso de atraso",
        "- Juros de 1% ao mes sobre valores em atraso",
        "- Cobranca bancaria automatica",
        "- Reajuste anual conforme indices oficiais"
    ]
    for condicao in condicoes_adicionais:
        pdf.cell(0, 7, _clean(condicao), 0, 1, 'L')

    # PÁGINA 7: TERMOS E CONDIÇÕES GERAIS (DINÂMICA)
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'TERMOS E CONDIÇÕES GERAIS', 0, 1, 'L')
    pdf.ln(5)
    
    # Informações da filial e locatária (DINÂMICAS)
    filial_nome = filial.get('nome', '')
    locataria = dados.get('cliente_nome', '')
    proposta = dados.get('numero', '')
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'INFORMAÇÕES CONTRATUAIS:', 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 7, f"Filial: {filial_nome}", 0, 1, 'L')
    pdf.cell(0, 7, f"Locatária: {locataria}", 0, 1, 'L')
    pdf.cell(0, 7, f"Nº da Proposta: {proposta}", 0, 1, 'L')
    pdf.ln(5)
    
    # Termos gerais
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'CLÁUSULAS GERAIS:', 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    termos_gerais = [
        "1. O equipamento permanece propriedade da locadora",
        "2. Responsabilidade pela manutenção preventiva da locadora",
        "3. Responsabilidade pela manutenção corretiva da locadora",
        "4. Seguro do equipamento por conta da locadora",
        "5. Respeito às normas de segurança na operação",
        "6. Proibição de sublocação sem autorização",
        "7. Rescisão contratual com aviso prévio de 30 dias"
    ]
    for termo in termos_gerais:
        pdf.cell(0, 7, termo, 0, 1, 'L')
    
    pdf.ln(5)
    pdf.cell(0, 7, "As demais cláusulas e responsabilidades permanecem conforme as normas de locação da empresa.", 0, 1, 'L')

    # Imagem na página 7 também (DINÂMICA)
    if img_path and os.path.exists(img_path):
        try:
            y = pdf.get_y() + 5
            if y < 250:  # Só adiciona se houver espaço
                pdf.image(img_path, x=25, y=y, w=70)
        except Exception:
            pass

    # PÁGINA 8: RESPONSABILIDADES
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'RESPONSABILIDADES', 0, 1, 'L')
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'RESPONSABILIDADES DA LOCADORA:', 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    responsabilidades_locadora = [
        "- Fornecimento do equipamento em perfeitas condicoes",
        "- Manutencao preventiva e corretiva",
        "- Substituicao em caso de defeito",
        "- Suporte tecnico durante a locacao",
        "- Seguro do equipamento"
    ]
    for resp in responsabilidades_locadora:
        pdf.cell(0, 7, _clean(resp), 0, 1, 'L')
    
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'RESPONSABILIDADES DO LOCATARIO:', 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    responsabilidades_locatario = [
        "- Pagamento pontual das mensalidades",
        "- Uso adequado do equipamento",
        "- Respeito as normas de seguranca",
        "- Comunicacao de problemas",
        "- Nao sublocacao sem autorizacao"
    ]
    for resp in responsabilidades_locatario:
        pdf.cell(0, 7, _clean(resp), 0, 1, 'L')

    # PÁGINA 9: PENALIDADES
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'PENALIDADES', 0, 1, 'L')
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 11)
    penalidades_texto = """
    Em caso de descumprimento das condicoes contratuais, serao aplicadas as seguintes penalidades:
    
    1. Atraso no pagamento: Multa de 2% ao mes + juros de 1% ao mes
    2. Uso inadequado: Responsabilizacao por danos
    3. Sublocacao nao autorizada: Rescisao imediata
    4. Descumprimento de normas de seguranca: Suspensao do contrato
    
    A locadora se reserva o direito de rescindir o contrato em caso de reincidencia.
    """
    for linha in penalidades_texto.strip().split('\n'):
        if linha.strip():
            pdf.cell(0, 6, _clean(linha.strip()), 0, 1, 'L')

    # PÁGINA 10: RESCISÃO
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'RESCISÃO CONTRATUAL', 0, 1, 'L')
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 11)
    rescisao_texto = """
    O contrato podera ser rescindido nas seguintes situacoes:
    
    - A pedido de qualquer das partes, com aviso previo de 30 dias
    - Por descumprimento das condicoes contratuais
    - Por forca maior ou caso fortuito
    - Por decisao judicial
    
    Em caso de rescisao, o equipamento devera ser devolvido em perfeitas condicoes.
    """
    for linha in rescisao_texto.strip().split('\n'):
        if linha.strip():
            pdf.cell(0, 6, _clean(linha.strip()), 0, 1, 'L')

    # PÁGINA 11: DISPOSIÇÕES GERAIS
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'DISPOSIÇÕES GERAIS', 0, 1, 'L')
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 11)
    disposicoes_texto = """
    - Este contrato esta sujeito as leis brasileiras
    - Qualquer alteracao deve ser feita por escrito
    - O foro competente e o da comarca da sede da locadora
    - Este documento constitui o acordo completo entre as partes
    - Fica eleito o endereco da locadora para recebimento de notificacoes
    """
    for linha in disposicoes_texto.strip().split('\n'):
        if linha.strip():
            pdf.cell(0, 6, _clean(linha.strip()), 0, 1, 'L')

    # PÁGINA 12: ASSINATURAS
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'ASSINATURAS', 0, 1, 'C')
    pdf.ln(20)
    
    # Locadora
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'LOCADORA:', 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 7, f"{filial.get('nome', 'EMPRESA LTDA')}", 0, 1, 'L')
    pdf.cell(0, 7, f"CNPJ: {filial.get('cnpj', '')}", 0, 1, 'L')
    pdf.ln(10)
    pdf.cell(0, 7, "_________________________________", 0, 1, 'L')
    pdf.cell(0, 7, "Assinatura e Carimbo", 0, 1, 'L')
    
    pdf.ln(20)
    
    # Locatário
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'LOCATARIO:', 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 7, f"{dados.get('cliente_nome', '')}", 0, 1, 'L')
    pdf.ln(10)
    pdf.cell(0, 7, "_________________________________", 0, 1, 'L')
    pdf.cell(0, 7, "Assinatura e Carimbo", 0, 1, 'L')

    # PÁGINA 13: ANEXOS
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'ANEXOS', 0, 1, 'L')
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 11)
    anexos_texto = """
    Este contrato possui os seguintes anexos:
    
    1. Especificacoes tecnicas do equipamento
    2. Termo de responsabilidade
    3. Checklist de entrega
    4. Termo de devolucao
    
    Os anexos fazem parte integrante deste contrato.
    """
    for linha in anexos_texto.strip().split('\n'):
        if linha.strip():
            pdf.cell(0, 6, _clean(linha.strip()), 0, 1, 'L')

    # Criar diretório se necessário (apenas se não for diretório atual)
    output_dir = os.path.dirname(output_path)
    if output_dir and output_dir != '.':
        os.makedirs(output_dir, exist_ok=True)
    pdf.output(output_path)

