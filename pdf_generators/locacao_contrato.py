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

    def _clean(text):
        if text is None:
            return ""
        s = str(text).replace('\t', '    ')
        replacements = {
            '–': '-', '—': '-', ''': "'", ''': "'", '"': '"', '"': '"',
            '…': '...', '®': '(R)', '©': '(C)', '™': '(TM)', 'º': 'o', 'ª': 'a',
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
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'CONTRATO DE LOCAÇÃO DE COMPRESSORES', 0, 1, 'C')
    pdf.ln(10)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, f'Proposta: {dados.get("numero", "")}', 0, 1, 'L')
    pdf.cell(0, 8, f'Cliente: {dados.get("cliente_nome", "")}', 0, 1, 'L')
    pdf.cell(0, 8, f'Data: {datetime.today().strftime("%d/%m/%Y")}', 0, 1, 'L')

    # Página 2: Saudação dinâmica
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 8, 'CORRESPONDÊNCIA', 0, 1, 'L')
    pdf.ln(5)
    equip = 'compressor'
    if dados.get('marca') or dados.get('modelo'):
        equip = f"compressor {dados.get('marca') or ''} {dados.get('modelo') or ''}".strip()
    saudacao = f"Prezados Senhores, referente à locação de {equip}."
    pdf.set_font('Arial', '', 12)
    # Usar cell em vez de multi_cell para evitar problemas de layout
    pdf.cell(0, 8, _clean(saudacao), 0, 1, 'L')

    # Página 3: Dados do equipamento
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 8, 'DADOS DO EQUIPAMENTO', 0, 1, 'L')
    pdf.ln(5)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, f'Marca: {dados.get("marca", "")}', 0, 1, 'L')
    pdf.cell(0, 8, f'Modelo: {dados.get("modelo", "")}', 0, 1, 'L')
    pdf.cell(0, 8, f'Número de Série: {dados.get("serie", "")}', 0, 1, 'L')
    pdf.cell(0, 8, f'Período: {dados.get("data_inicio", "")} a {dados.get("data_fim", "")}', 0, 1, 'L')

    # Página 4: Imagem do compressor
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 8, 'IMAGEM DO EQUIPAMENTO', 0, 1, 'L')
    pdf.ln(5)
    img_path = dados.get('imagem_compressor')
    if not img_path or not os.path.exists(img_path):
        fallback = filial.get('logo_path')
        if fallback and os.path.exists(fallback):
            img_path = fallback
    if img_path and os.path.exists(img_path):
        try:
            pdf.image(img_path, x=25, y=40, w=160)
        except Exception:
            pdf.set_font('Arial', 'I', 11)
            pdf.cell(0, 8, 'Imagem do compressor não fornecida.', 0, 1, 'L')
    else:
        pdf.set_font('Arial', 'I', 11)
        pdf.cell(0, 8, 'Imagem do compressor não fornecida.', 0, 1, 'L')

    # Página 5: Condições gerais
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 8, 'CONDIÇÕES GERAIS', 0, 1, 'L')
    pdf.ln(5)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, _clean("Contrato de locação sujeito às condições gerais da empresa."), 0, 1, 'L')

    # Página 6: Condições de pagamento dinâmicas
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 8, 'CONDIÇÕES DE PAGAMENTO', 0, 1, 'L')
    pdf.ln(5)
    condicoes = dados.get('condicoes_pagamento')
    if not condicoes:
        dia = dados.get('vencimento_dia') or '10'
        condicoes = f"A vencimento de cada mensalidade, todo dia {dia}, conforme proposta acordada com o cliente."
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, _clean(condicoes), 0, 1, 'L')

    # Página 7: Termos e condições + imagem
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 8, 'TERMOS E CONDIÇÕES GERAIS', 0, 1, 'L')
    pdf.ln(5)
    filial_nome = filial.get('nome', '')
    locataria = dados.get('cliente_nome', '')
    proposta = dados.get('numero', '')
    
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, f"Filial: {filial_nome}", 0, 1, 'L')
    pdf.cell(0, 8, f"Locatária: {locataria}", 0, 1, 'L')
    pdf.cell(0, 8, f"Nº da Proposta: {proposta}", 0, 1, 'L')
    pdf.ln(5)
    pdf.cell(0, 8, "As demais cláusulas e responsabilidades permanecem conforme as normas de locação da empresa.", 0, 1, 'L')

    # Imagem na página 7 também
    if img_path and os.path.exists(img_path):
        try:
            y = pdf.get_y() + 5
            pdf.image(img_path, x=25, y=y, w=70)
        except Exception:
            pass

    # Criar diretório se necessário (apenas se não for diretório atual)
    output_dir = os.path.dirname(output_path)
    if output_dir and output_dir != '.':
        os.makedirs(output_dir, exist_ok=True)
    pdf.output(output_path)


def gerar_pdf_locacao(dados: dict, output_path: str):
    """Gera um PDF idêntico ao DOCX de modelo, com sobreposição dos campos dinâmicos.

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

    # 1) Procurar PDF base enviado (ex: exemplolocação.pdf) no diretório do projeto
    project_dir = os.getcwd()
    candidate_pdf = None
    for fname in os.listdir(project_dir):
        if not fname.lower().endswith('.pdf'):
            continue
        name_norm = _normalize(fname)
        if 'exemplo' in name_norm and 'loca' in name_norm:
            candidate_pdf = os.path.join(project_dir, fname)
            break

    # 2) Se não encontrar no root, procurar em subpastas comuns (assets, data, pdf_generators)
    if not candidate_pdf:
        for sub in ['assets', 'data', 'pdf_generators']:
            subdir = os.path.join(project_dir, sub)
            if not os.path.isdir(subdir):
                continue
            try:
                for fname in os.listdir(subdir):
                    if not fname.lower().endswith('.pdf'):
                        continue
                    name_norm = _normalize(fname)
                    if 'exemplo' in name_norm and 'loca' in name_norm:
                        candidate_pdf = os.path.join(subdir, fname)
                        break
            except Exception:
                pass
            if candidate_pdf:
                break

    # 3) Se o PDF de exemplo existir, usar diretamente; senão, fazer fallback para DOCX -> PDF
    if candidate_pdf and os.path.exists(candidate_pdf):
        _overlay_dynamic_fields(candidate_pdf, output_path, dados)
        return

    # Fallback para DOCX
    model_docx = os.path.join(project_dir, "Modelo Contrato de Locação (1).docx")
    if not os.path.exists(model_docx):
        for fname in os.listdir(project_dir):
            if fname.lower().startswith("modelo contrato de loc") and fname.lower().endswith('.docx'):
                model_docx = os.path.join(project_dir, fname)
                break

    base_pdf = os.path.join(os.path.dirname(output_path), "_modelo_base_locacao.pdf")
    if not _docx_to_pdf(model_docx, base_pdf):
        # Se tudo falhar, usar o gerador básico
        if FPDF_AVAILABLE:
            _generate_basic_pdf(dados, output_path)
        else:
            _generate_text_fallback(dados, output_path)
        return

    _overlay_dynamic_fields(base_pdf, output_path, dados)
    try:
        os.remove(base_pdf)
    except Exception:
        pass


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

