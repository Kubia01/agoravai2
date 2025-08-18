import os
from datetime import datetime
from assets.filiais.filiais_config import obter_filial
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from PyPDF2 import PdfReader, PdfWriter
import unicodedata


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


def gerar_pdf_locacao(dados: dict, output_path: str):
    """Gera um PDF idêntico ao DOCX de modelo, com sobreposição dos campos dinâmicos.

    Páginas estáticas são mantidas; as seguintes são dinâmicas:
      - Página 2: saudação conforme equipamento
      - Página 4: desenho/imagem por marca
      - Página 6: condições de pagamento
      - Página 7: filial, locatária e número da proposta + imagem por marca
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

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
        raise RuntimeError("Modelo PDF 'exemplolocação.pdf' não encontrado e DOCX->PDF falhou (LibreOffice ausente).")

    _overlay_dynamic_fields(base_pdf, output_path, dados)
    try:
        os.remove(base_pdf)
    except Exception:
        pass

