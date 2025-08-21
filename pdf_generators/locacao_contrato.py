import os
import subprocess
from datetime import datetime
from assets.filiais.filiais_config import obter_filial
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from PyPDF2 import PdfReader, PdfWriter


def _clean(text):
    return "" if text is None else str(text)


def _docx_to_pdf(docx_path: str, pdf_path: str):
    """Converte DOCX em PDF usando LibreOffice (ou soffice no Windows).

    Retorna True em caso de sucesso, False caso contrário.
    """
    outdir = os.path.dirname(pdf_path)
    os.makedirs(outdir, exist_ok=True)

    # Candidatos de executável (Linux/Mac/Windows)
    candidates = [
        'libreoffice',
        'soffice',
        r"C:\\Program Files\\LibreOffice\\program\\soffice.exe",
        r"C:\\Program Files (x86)\\LibreOffice\\program\\soffice.exe",
    ]

    exe_path = None
    for exe in candidates:
        if os.path.isabs(exe):
            if os.path.exists(exe):
                exe_path = exe
                break
        else:
            from shutil import which
            found = which(exe)
            if found:
                exe_path = found
                break

    if not exe_path:
        return False

    try:
        result = subprocess.run(
            [exe_path, '--headless', '--convert-to', 'pdf', '--outdir', outdir, docx_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        code = result.returncode
    except Exception:
        code = -1

    expected = os.path.join(outdir, os.path.splitext(os.path.basename(docx_path))[0] + ".pdf")

    if code == 0 and os.path.exists(expected):
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

    model_docx = os.path.join(os.getcwd(), "Modelo Contrato de Locação (1).docx")

    if not os.path.exists(model_docx):
        # Nome alternativo com cedilha/acentos, conforme repositório
        for fname in os.listdir(os.getcwd()):
            if fname.lower().startswith("modelo contrato de loc") and fname.lower().endswith('.docx'):

                model_docx = os.path.join(os.getcwd(), fname)
                break

    base_pdf = os.path.join(os.path.dirname(output_path), "_modelo_base_locacao.pdf")

    if not _docx_to_pdf(model_docx, base_pdf):
        raise RuntimeError("Falha ao converter o modelo DOCX para PDF. Instale LibreOffice no ambiente.")

    _overlay_dynamic_fields(base_pdf, output_path, dados)
    try:
        os.remove(base_pdf)
    except Exception:
        pass

