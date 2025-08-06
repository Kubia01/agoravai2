import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import tempfile

try:
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.units import mm, cm, inch
    from reportlab.lib.colors import Color, black, white, blue, red, green
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
    print("✅ ReportLab carregado com sucesso")
except ImportError as e:
    REPORTLAB_AVAILABLE = False
    print(f"⚠️ ReportLab não disponível - funcionalidade de PDF limitada: {e}")
    
    # Mock classes when ReportLab is not available
    class Color:
        def __init__(self, r, g, b, alpha=1):
            self.r, self.g, self.b, self.alpha = r, g, b, alpha
    
    A4 = (595.276, 841.890)
    mm = 2.834645669
    black = Color(0, 0, 0)

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    
    # Mock classes when PIL is not available
    class Image:
        @staticmethod
        def new(mode, size, color='white'):
            return None
    
    class ImageDraw:
        @staticmethod
        def Draw(img):
            return None
    
    class ImageFont:
        @staticmethod
        def load_default():
            return None

class PDFTemplateEngine:
    """
    Engine completo para geração de PDFs baseado em templates visuais.
    Converte elementos do editor visual em PDFs profissionais.
    """
    
    def __init__(self, template_data: Dict[str, Any], field_resolver=None):
        self.template_data = template_data
        self.field_resolver = field_resolver
        self.output_path = None
        
        # Configurações padrão
        self.page_size = A4
        self.page_width, self.page_height = A4
        self.margin_left = 72  # 1 inch
        self.margin_right = 72
        self.margin_top = 72
        self.margin_bottom = 72
        
        # Fontes disponíveis
        self.fonts = {
            'Arial': 'Helvetica',
            'Times': 'Times-Roman',
            'Helvetica': 'Helvetica',
            'Courier': 'Courier'
        }
        
        # Cache de imagens e elementos
        self.image_cache = {}
        self.element_cache = {}
        
        # Configurações avançadas
        self.quality_dpi = 300
        self.compress_images = True
        self.embed_fonts = True
        
    def generate_pdf(self, output_path: str, metadata: Optional[Dict] = None) -> bool:
        """
        Gerar PDF completo baseado no template
        
        Args:
            output_path: Caminho do arquivo PDF de saída
            metadata: Metadados do PDF (título, autor, etc.)
        
        Returns:
            True se geração foi bem-sucedida
        """
        if not REPORTLAB_AVAILABLE:
            print("❌ Erro: ReportLab não está instalado. Instale com: pip install reportlab")
            return False
            
        try:
            
            self.output_path = output_path
            
            # Criar documento PDF
            doc = SimpleDocTemplate(
                output_path,
                pagesize=self.page_size,
                leftMargin=self.margin_left,
                rightMargin=self.margin_right,
                topMargin=self.margin_top,
                bottomMargin=self.margin_bottom,
                title=metadata.get('title', 'Documento Gerado') if metadata else 'Documento Gerado',
                author=metadata.get('author', 'Sistema CRM') if metadata else 'Sistema CRM',
                subject=metadata.get('subject', 'Proposta Comercial') if metadata else 'Proposta Comercial'
            )
            
            # Preparar conteúdo de todas as páginas
            story = []
            
            pages = self.template_data.get('pages', [])
            total_pages = len(pages)
            
            for page_index, page_data in enumerate(pages):
                print(f"🔄 Processando página {page_index + 1} de {total_pages}")
                
                # Processar elementos da página
                page_elements = self.process_page_elements(page_data, page_index + 1, total_pages)
                
                # Adicionar elementos ao story
                story.extend(page_elements)
                
                # Quebra de página (exceto última página)
                if page_index < total_pages - 1:
                    from reportlab.platypus import PageBreak
                    story.append(PageBreak())
            
            # Construir PDF
            doc.build(story, onFirstPage=self.create_page_template, onLaterPages=self.create_page_template)
            
            print(f"✅ PDF gerado com sucesso: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao gerar PDF: {e}")
            return False
    
    def process_page_elements(self, page_data: Dict[str, Any], page_num: int, total_pages: int) -> List[Any]:
        """
        Processar elementos de uma página específica
        
        Args:
            page_data: Dados da página do template
            page_num: Número da página atual
            total_pages: Total de páginas
        
        Returns:
            Lista de elementos para o ReportLab
        """
        elements = []
        page_elements = page_data.get('elements', [])
        
        # Ordenar elementos por posição Y (top to bottom)
        sorted_elements = sorted(page_elements, key=lambda x: x.get('y', 0))
        
        # Processar cada elemento
        for element in sorted_elements:
            try:
                element_type = element.get('type', '')
                
                if element_type == 'text':
                    processed = self.process_text_element(element)
                elif element_type == 'dynamic_field':
                    processed = self.process_dynamic_field_element(element)
                elif element_type == 'image':
                    processed = self.process_image_element(element)
                elif element_type == 'table':
                    processed = self.process_table_element(element)
                elif element_type == 'line':
                    processed = self.process_line_element(element)
                elif element_type == 'rectangle':
                    processed = self.process_rectangle_element(element)
                else:
                    continue  # Tipo não suportado
                
                if processed:
                    if isinstance(processed, list):
                        elements.extend(processed)
                    else:
                        elements.append(processed)
                        
            except Exception as e:
                print(f"⚠️ Erro ao processar elemento {element.get('id', 'unknown')}: {e}")
                continue
        
        return elements
    
    def process_text_element(self, element: Dict[str, Any]) -> Optional[Any]:
        """Processar elemento de texto"""
        try:
            text = element.get('text', '')
            if not text:
                return None
            
            # Resolver campos dinâmicos no texto
            if self.field_resolver:
                text = self.field_resolver.resolve_template_text(text)
            
            # Configurações de estilo
            font_family = self.fonts.get(element.get('font_family', 'Arial'), 'Helvetica')
            font_size = element.get('font_size', 12)
            color = self.parse_color(element.get('color', '#000000'))
            bold = element.get('bold', False)
            italic = element.get('italic', False)
            
            # Criar estilo
            style_name = f"custom_{element.get('id', 'text')}"
            style = ParagraphStyle(
                style_name,
                parent=getSampleStyleSheet()['Normal'],
                fontName=self.get_font_name(font_family, bold, italic),
                fontSize=font_size,
                textColor=color,
                alignment=TA_LEFT,  # Pode ser configurável
                spaceAfter=6
            )
            
            # Criar parágrafo
            paragraph = Paragraph(text, style)
            
            return paragraph
            
        except Exception as e:
            print(f"Erro ao processar texto: {e}")
            return None
    
    def process_dynamic_field_element(self, element: Dict[str, Any]) -> Optional[Any]:
        """Processar elemento de campo dinâmico"""
        try:
            field_ref = element.get('field_ref', '')
            if not field_ref:
                return None
            
            # Resolver campo dinâmico
            if self.field_resolver:
                text = self.field_resolver.resolve_field(field_ref)
            else:
                text = f"[{field_ref}]"
            
            # Criar elemento de texto com o valor resolvido
            text_element = element.copy()
            text_element['text'] = text
            text_element['type'] = 'text'
            
            return self.process_text_element(text_element)
            
        except Exception as e:
            print(f"Erro ao processar campo dinâmico: {e}")
            return None
    
    def process_image_element(self, element: Dict[str, Any]) -> Optional[Any]:
        """Processar elemento de imagem"""
        try:
            image_path = element.get('image_path', '')
            if not image_path or not os.path.exists(image_path):
                return None
            
            width = element.get('width', 100) * point
            height = element.get('height', 100) * point
            
            # Criar imagem do ReportLab
            img = RLImage(image_path, width=width, height=height)
            
            return img
            
        except Exception as e:
            print(f"Erro ao processar imagem: {e}")
            return None
    
    def process_table_element(self, element: Dict[str, Any]) -> Optional[Any]:
        """Processar elemento de tabela"""
        try:
            # Dados da tabela
            table_data = element.get('data', [])
            if not table_data:
                # Criar tabela de exemplo se não houver dados
                rows = element.get('rows', 3)
                cols = element.get('cols', 3)
                table_data = [[f"Célula {r+1},{c+1}" for c in range(cols)] for r in range(rows)]
            
            # Criar tabela
            table = Table(table_data)
            
            # Estilo da tabela
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ])
            
            table.setStyle(table_style)
            
            return table
            
        except Exception as e:
            print(f"Erro ao processar tabela: {e}")
            return None
    
    def process_line_element(self, element: Dict[str, Any]) -> Optional[Any]:
        """Processar elemento de linha"""
        try:
            # Para linhas, usamos Spacer com linha customizada
            # Implementação simplificada - pode ser expandida
            return Spacer(1, 12)
            
        except Exception as e:
            print(f"Erro ao processar linha: {e}")
            return None
    
    def process_rectangle_element(self, element: Dict[str, Any]) -> Optional[Any]:
        """Processar elemento de retângulo"""
        try:
            # Para retângulos, criar usando canvas customizado
            # Implementação simplificada
            return Spacer(1, element.get('height', 50))
            
        except Exception as e:
            print(f"Erro ao processar retângulo: {e}")
            return None
    
    def create_page_template(self, canvas_obj, doc):
        """
        Criar template de página (cabeçalho/rodapé)
        """
        try:
            # Configurações da página
            page_width = self.page_width
            page_height = self.page_height
            
            # Cabeçalho (se configurado)
            if self.has_header():
                self.draw_header(canvas_obj, page_width, page_height)
            
            # Rodapé (se configurado)
            if self.has_footer():
                self.draw_footer(canvas_obj, page_width, page_height)
            
            # Numeração de página
            self.draw_page_number(canvas_obj, page_width, page_height)
            
        except Exception as e:
            print(f"Erro ao criar template de página: {e}")
    
    def has_header(self) -> bool:
        """Verificar se template tem cabeçalho"""
        # Implementar lógica para detectar elementos de cabeçalho
        return False
    
    def has_footer(self) -> bool:
        """Verificar se template tem rodapé"""
        # Implementar lógica para detectar elementos de rodapé
        return True  # Por enquanto sempre true
    
    def draw_header(self, canvas_obj, page_width: float, page_height: float):
        """Desenhar cabeçalho da página"""
        try:
            canvas_obj.setFont("Helvetica-Bold", 12)
            canvas_obj.drawString(72, page_height - 50, "Cabeçalho do Documento")
        except Exception as e:
            print(f"Erro ao desenhar cabeçalho: {e}")
    
    def draw_footer(self, canvas_obj, page_width: float, page_height: float):
        """Desenhar rodapé da página"""
        try:
            # Rodapé padrão com informações da empresa
            footer_y = 30
            
            canvas_obj.setFont("Helvetica", 8)
            canvas_obj.setFillColor(colors.Color(0.54, 0.81, 0.94))  # Azul bebê #89CFF0
            
            # Informações da empresa (centralizadas)
            empresa_info = [
                "WORLD COMP COMPRESSORES LTDA",
                "Rua Fernando Pessoa, nº 11 – Batistini – São Bernardo do Campo – SP – CEP: 09844-390",
                "CNPJ: 10.644.944/0001-55 | Fone: (11) 4543-6893 / 4543-6857",
                "E-mail: contato@worldcompressores.com.br"
            ]
            
            for i, info in enumerate(empresa_info):
                y_pos = footer_y + (len(empresa_info) - i - 1) * 10
                text_width = canvas_obj.stringWidth(info, "Helvetica", 8)
                x_pos = (page_width - text_width) / 2
                canvas_obj.drawString(x_pos, y_pos, info)
                
        except Exception as e:
            print(f"Erro ao desenhar rodapé: {e}")
    
    def draw_page_number(self, canvas_obj, page_width: float, page_height: float):
        """Desenhar numeração da página"""
        try:
            page_num = canvas_obj.getPageNumber()
            canvas_obj.setFont("Helvetica", 8)
            canvas_obj.setFillColor(colors.black)
            canvas_obj.drawRightString(page_width - 72, 20, f"Página {page_num}")
        except Exception as e:
            print(f"Erro ao desenhar número da página: {e}")
    
    def parse_color(self, color_str: str):
        """
        Converter string de cor em objeto Color do ReportLab
        
        Args:
            color_str: Cor em formato hex (#RRGGBB) ou nome
        
        Returns:
            Objeto Color do ReportLab
        """
        try:
            if color_str.startswith('#'):
                # Formato hex
                hex_color = color_str.lstrip('#')
                if len(hex_color) == 6:
                    r = int(hex_color[0:2], 16) / 255.0
                    g = int(hex_color[2:4], 16) / 255.0
                    b = int(hex_color[4:6], 16) / 255.0
                    return Color(r, g, b)
            
            # Cores nomeadas
            color_map = {
                'black': colors.black,
                'white': colors.white,
                'red': colors.red,
                'green': colors.green,
                'blue': colors.blue,
                'yellow': colors.yellow,
                'orange': colors.orange,
                'purple': colors.purple,
                'grey': colors.grey,
                'gray': colors.grey
            }
            
            return color_map.get(color_str.lower(), colors.black)
            
        except Exception:
            return colors.black
    
    def get_font_name(self, base_font: str, bold: bool = False, italic: bool = False) -> str:
        """
        Obter nome da fonte considerando estilos
        
        Args:
            base_font: Fonte base
            bold: Se deve ser negrito
            italic: Se deve ser itálico
        
        Returns:
            Nome da fonte para ReportLab
        """
        font_map = {
            'Helvetica': {
                (False, False): 'Helvetica',
                (True, False): 'Helvetica-Bold',
                (False, True): 'Helvetica-Oblique',
                (True, True): 'Helvetica-BoldOblique'
            },
            'Times-Roman': {
                (False, False): 'Times-Roman',
                (True, False): 'Times-Bold',
                (False, True): 'Times-Italic',
                (True, True): 'Times-BoldItalic'
            },
            'Courier': {
                (False, False): 'Courier',
                (True, False): 'Courier-Bold',
                (False, True): 'Courier-Oblique',
                (True, True): 'Courier-BoldOblique'
            }
        }
        
        font_variants = font_map.get(base_font, font_map['Helvetica'])
        return font_variants.get((bold, italic), base_font)
    
    def generate_preview_image(self, page_index: int = 0, scale: float = 1.0) -> Optional[str]:
        """
        Gerar imagem de preview de uma página
        
        Args:
            page_index: Índice da página (0-based)
            scale: Escala da imagem (1.0 = tamanho real)
        
        Returns:
            Caminho da imagem gerada ou None se erro
        """
        try:
            if not PIL_AVAILABLE:
                return None
            
            # Dimensões da página em pixels
            dpi = 150 * scale
            width_px = int(self.page_width * dpi / 72)
            height_px = int(self.page_height * dpi / 72)
            
            # Criar imagem
            img = Image.new('RGB', (width_px, height_px), 'white')
            draw = ImageDraw.Draw(img)
            
            # Desenhar elementos da página
            pages = self.template_data.get('pages', [])
            if page_index < len(pages):
                page_data = pages[page_index]
                self.draw_page_preview(draw, page_data, width_px, height_px, scale)
            
            # Salvar imagem temporária
            temp_path = os.path.join(tempfile.gettempdir(), f"preview_page_{page_index}_{datetime.now().timestamp()}.png")
            img.save(temp_path, 'PNG', dpi=(dpi, dpi))
            
            return temp_path
            
        except Exception as e:
            print(f"Erro ao gerar preview: {e}")
            return None
    
    def draw_page_preview(self, draw: ImageDraw.Draw, page_data: Dict[str, Any], 
                         width_px: int, height_px: int, scale: float):
        """
        Desenhar elementos da página no preview
        
        Args:
            draw: Objeto ImageDraw
            page_data: Dados da página
            width_px: Largura em pixels
            height_px: Altura em pixels
            scale: Escala de conversão
        """
        try:
            elements = page_data.get('elements', [])
            
            for element in elements:
                element_type = element.get('type', '')
                x = int(element.get('x', 0) * scale)
                y = int(element.get('y', 0) * scale)
                
                if element_type in ['text', 'dynamic_field']:
                    self.draw_text_preview(draw, element, x, y, scale)
                elif element_type == 'rectangle':
                    self.draw_rectangle_preview(draw, element, x, y, scale)
                elif element_type == 'line':
                    self.draw_line_preview(draw, element, x, y, scale)
                    
        except Exception as e:
            print(f"Erro ao desenhar preview da página: {e}")
    
    def draw_text_preview(self, draw: ImageDraw.Draw, element: Dict[str, Any], 
                         x: int, y: int, scale: float):
        """Desenhar texto no preview"""
        try:
            if element.get('type') == 'dynamic_field':
                field_ref = element.get('field_ref', '')
                text = self.field_resolver.resolve_field(field_ref) if self.field_resolver else f"[{field_ref}]"
            else:
                text = element.get('text', '')
            
            if not text:
                return
            
            font_size = int(element.get('font_size', 12) * scale)
            color = element.get('color', '#000000')
            
            # Tentar carregar fonte (simplificado)
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            draw.text((x, y), text, fill=color, font=font)
            
        except Exception as e:
            print(f"Erro ao desenhar texto no preview: {e}")
    
    def draw_rectangle_preview(self, draw: ImageDraw.Draw, element: Dict[str, Any], 
                              x: int, y: int, scale: float):
        """Desenhar retângulo no preview"""
        try:
            width = int(element.get('width', 100) * scale)
            height = int(element.get('height', 50) * scale)
            fill_color = element.get('fill_color', '')
            border_color = element.get('border_color', '#000000')
            
            # Desenhar retângulo
            coords = [x, y, x + width, y + height]
            
            if fill_color:
                draw.rectangle(coords, fill=fill_color)
            
            draw.rectangle(coords, outline=border_color)
            
        except Exception as e:
            print(f"Erro ao desenhar retângulo no preview: {e}")
    
    def draw_line_preview(self, draw: ImageDraw.Draw, element: Dict[str, Any], 
                         x: int, y: int, scale: float):
        """Desenhar linha no preview"""
        try:
            length = int(element.get('length', 100) * scale)
            color = element.get('color', '#000000')
            thickness = int(element.get('thickness', 1))
            
            end_x = x + length
            end_y = y + element.get('angle_offset', 0) * scale
            
            draw.line([x, y, end_x, end_y], fill=color, width=thickness)
            
        except Exception as e:
            print(f"Erro ao desenhar linha no preview: {e}")
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Obter metadados do template
        
        Returns:
            Dicionário com metadados
        """
        return {
            'template_version': self.template_data.get('version', '1.0'),
            'created_at': self.template_data.get('created_at', datetime.now().isoformat()),
            'total_pages': len(self.template_data.get('pages', [])),
            'has_dynamic_fields': self.has_dynamic_fields(),
            'generator': 'PDFTemplateEngine v1.0'
        }
    
    def has_dynamic_fields(self) -> bool:
        """Verificar se template tem campos dinâmicos"""
        pages = self.template_data.get('pages', [])
        for page in pages:
            elements = page.get('elements', [])
            for element in elements:
                if element.get('type') == 'dynamic_field':
                    return True
        return False
    
    def validate_template(self) -> Tuple[bool, List[str]]:
        """
        Validar template antes da geração
        
        Returns:
            Tuple (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            # Validar estrutura básica
            if not isinstance(self.template_data, dict):
                errors.append("Template deve ser um dicionário")
                return False, errors
            
            pages = self.template_data.get('pages', [])
            if not pages:
                errors.append("Template deve ter pelo menos uma página")
            
            # Validar cada página
            for i, page in enumerate(pages):
                if not isinstance(page, dict):
                    errors.append(f"Página {i+1} deve ser um dicionário")
                    continue
                
                elements = page.get('elements', [])
                for j, element in enumerate(elements):
                    if not isinstance(element, dict):
                        errors.append(f"Elemento {j+1} da página {i+1} deve ser um dicionário")
                        continue
                    
                    # Validar tipo de elemento
                    element_type = element.get('type', '')
                    if not element_type:
                        errors.append(f"Elemento {j+1} da página {i+1} deve ter um tipo")
                    
                    # Validar posição
                    if 'x' not in element or 'y' not in element:
                        errors.append(f"Elemento {j+1} da página {i+1} deve ter posição (x, y)")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"Erro na validação: {e}")
            return False, errors

    def generate_pdf_from_visual_template(self, template_data: Dict, output_path: str, data_resolver=None) -> bool:
        """
        Gerar PDF mantendo fidelidade total com o editor visual
        
        Args:
            template_data: Dados do template do editor visual
            output_path: Caminho do arquivo de saída
            data_resolver: Resolvedor de campos dinâmicos
        
        Returns:
            True se geração foi bem-sucedida
        """
        if not REPORTLAB_AVAILABLE:
            print("⚠️ ReportLab não disponível - usando fallback")
            return self._generate_fallback_pdf(template_data, output_path)
        
        print("🔄 Gerando PDF com ReportLab...")
        
        try:
            # Criar documento PDF
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=40,
                leftMargin=40,
                topMargin=40,
                bottomMargin=40
            )
            
            # Processar cada página do template
            story = []
            pages = template_data.get("pages", {})
            
            for page_num in sorted(pages.keys(), key=int):
                page_data = pages[page_num]
                
                # Pular página 1 (capa) se não for editável
                if page_num == "1" and not page_data.get("editable", True):
                    continue
                
                story.extend(self._build_page_from_template(page_data, int(page_num), data_resolver))
                
                # Adicionar quebra de página (exceto na última)
                if page_num != max(pages.keys(), key=int):
                    story.append(PageBreak())
            
            # Gerar PDF sem template de página (rodapé será adicionado como elemento)
            doc.build(story)
            
            print(f"✅ PDF gerado com sucesso: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao gerar PDF: {e}")
            return False
    
    def _generate_fallback_pdf(self, template_data: Dict, output_path: str) -> bool:
        """Gerar PDF de fallback quando ReportLab não está disponível"""
        try:
            # Criar um PDF simples usando fpdf2 como fallback
            from fpdf import FPDF
            import os
            
            # Garantir que o diretório existe
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            
            # Adicionar conteúdo básico
            pdf.cell(200, 10, txt="PDF Preview - ReportLab não disponível", ln=True, align='C')
            pdf.cell(200, 10, txt="", ln=True, align='L')
            pdf.cell(200, 10, txt="Template carregado com sucesso!", ln=True, align='L')
            pdf.cell(200, 10, txt="Instale o ReportLab para preview completo.", ln=True, align='L')
            
            # Salvar PDF
            pdf.output(output_path)
            print(f"✅ PDF de fallback gerado: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao gerar PDF de fallback: {e}")
            import traceback
            print(f"Erro detalhado: {traceback.format_exc()}")
            return False
    
    def _build_page_from_template(self, page_data: Dict, page_num: int, data_resolver=None) -> List:
        """Construir elementos da página baseado no template visual - fiel ao gerador original"""
        elements = []
        
        try:
            # Dados fictícios baseados no gerador original
            fake_data = {
                "cliente_nome": "EMPRESA EXEMPLO LTDA",
                "cliente_cnpj": "12.345.678/0001-90",
                "cliente_telefone": "(11) 3456-7890",
                "contato_nome": "Maria Silva",
                "filial_nome": "WORLD COMP COMPRESSORES LTDA",
                "filial_cnpj": "10.644.944/0001-55",
                "filial_telefones": "(11) 4543-6893 / 4543-6857",
                "responsavel_email": "rogerio@worldcomp.com.br",
                "responsavel_nome": "Rogerio Cerqueira",
                "numero_proposta": "PROP-2024-001",
                "data_criacao": "21/01/2025",
                "valor_total": "R$ 15.750,00",
                "modelo_compressor": "Atlas Copco GA 75",
                "numero_serie_compressor": "AC123456789"
            }
            
            # PÁGINA 1: CAPA (como no gerador original) - SEM CABEÇALHO/RODAPÉ
            if page_num == 1:
                elements.extend(self._create_capa_page(fake_data))
            
            # PÁGINAS 2-4: COM CABEÇALHO, RODAPÉ E BORDAS
            elif page_num in [2, 3, 4]:
                # Adicionar cabeçalho (como no gerador original)
                elements.extend(self._create_standard_header(fake_data))
                
                # Conteúdo específico da página
                if page_num == 2:
                    elements.extend(self._create_apresentacao_page(fake_data))
                elif page_num == 3:
                    elements.extend(self._create_sobre_empresa_page(fake_data))
                elif page_num == 4:
                    elements.extend(self._create_proposta_page(fake_data))
                
                # Adicionar rodapé na parte inferior (como no gerador original)
                elements.extend(self._create_standard_footer(page_num, fake_data))
                
                # Borda removida para evitar erro "Flowable too large"
                # O conteúdo principal já está formatado corretamente
            
            # Outras páginas - usar template do editor
            else:
                # Verificar se tem cabeçalho
                if page_data.get("has_header", False):
                    elements.extend(self._create_standard_header(data_resolver))
                
                # Processar elementos da página em ordem de Y (top to bottom)
                page_elements = page_data.get("elements", [])
                sorted_elements = sorted(page_elements, key=lambda x: x.get("y", 0))
                
                current_y = 120 if page_data.get("has_header", False) else 40
                
                for element in sorted_elements:
                    element_y = element.get("y", current_y)
                    
                    # Adicionar espaçamento se necessário
                    if element_y > current_y:
                        spacer_height = (element_y - current_y) * 0.75
                        if spacer_height > 0:
                            elements.append(Spacer(1, spacer_height))
                    
                    # Criar elemento visual baseado no tipo
                    visual_element = self._create_visual_element(element, data_resolver)
                    if visual_element:
                        elements.append(visual_element)
                        current_y = element_y + element.get("h", 20)
                
                # Verificar se tem rodapé
                if page_data.get("has_footer", False):
                    footer_y = 760
                    if current_y < footer_y:
                        elements.append(Spacer(1, footer_y - current_y))
                    
                    elements.extend(self._create_standard_footer(page_num, data_resolver))
            
        except Exception as e:
            print(f"Erro ao construir página {page_num}: {e}")
            error_style = ParagraphStyle(
                'Error',
                parent=getSampleStyleSheet()['Normal'],
                fontSize=10,
                textColor=colors.red
            )
            elements.append(Paragraph(f"❌ Erro na página {page_num}: {str(e)}", error_style))
        
        return elements
    
    def _create_visual_element(self, element: Dict, data_resolver=None):
        """Criar elemento visual baseado na definição do template"""
        try:
            element_type = element.get("type", "text")
            data_type = element.get("data_type", "fixed")
            
            if element_type == "text":
                return self._create_text_from_template(element, data_resolver)
            elif element_type == "image":
                return self._create_image_from_template(element, data_resolver)
            elif element_type == "line":
                return self._create_line_from_template(element)
            else:
                return None
                
        except Exception as e:
            print(f"Erro ao criar elemento visual: {e}")
            return None
    
    def _create_text_from_template(self, element: Dict, data_resolver=None):
        """Criar elemento de texto baseado no template com dados fictícios"""
        try:
            # Obter conteúdo
            if element.get("data_type") == "dynamic":
                # Resolver campo dinâmico
                field_name = element.get("current_field", "")
                content_template = element.get("content_template", "{value}")
                
                # Dados fictícios para melhor visualização
                fake_data = {
                    "cliente_nome": "EMPRESA EXEMPLO LTDA",
                    "cliente_cnpj": "12.345.678/0001-90",
                    "cliente_telefone": "(11) 3456-7890",
                    "contato_nome": "Maria Silva",
                    "filial_nome": "WORLD COMP COMPRESSORES LTDA",
                    "filial_cnpj": "10.644.944/0001-55",
                    "filial_telefones": "(11) 4543-6893 / 4543-6857",
                    "responsavel_email": "rogerio@worldcomp.com.br",
                    "responsavel_nome": "Rogerio Cerqueira",
                    "numero_proposta": "PROP-2024-001",
                    "data_criacao": "21/01/2025",
                    "valor_total": "R$ 15.750,00",
                    "modelo_compressor": "Atlas Copco GA 75",
                    "numero_serie_compressor": "AC123456789"
                }
                
                if data_resolver and hasattr(data_resolver, 'resolve_field'):
                    field_value = data_resolver.resolve_field(field_name)
                else:
                    field_value = fake_data.get(field_name, f"[{field_name}]")
                
                content = content_template.format(value=field_value)
            else:
                content = element.get("content", "")
            
            if not content:
                return None
            
            # Configurar estilo simples e funcional
            font_family = self.fonts.get(element.get("font_family", "Arial"), "Helvetica")
            font_size = element.get("font_size", 11)
            font_style = element.get("font_style", "normal")
            
            # Determinar fonte completa
            font_name = font_family
            if font_style == "bold":
                font_name += "-Bold"
            elif font_style == "italic":
                font_name += "-Oblique"
            elif font_style == "bold italic":
                font_name += "-BoldOblique"
            
            # Criar estilo simples sem posicionamento complexo
            style = ParagraphStyle(
                f"custom_{element.get('id', 'text')}",
                parent=getSampleStyleSheet()['Normal'],
                fontName=font_name,
                fontSize=font_size,
                textColor=colors.black,
                alignment=TA_LEFT,
                spaceAfter=6,
                spaceBefore=0
            )
            
            # Criar parágrafo
            return Paragraph(content, style)
            
        except Exception as e:
            print(f"Erro ao criar texto: {e}")
            return None
    
    def _create_image_from_template(self, element: Dict, data_resolver=None):
        """Criar elemento de imagem baseado no template"""
        try:
            image_path = element.get("content", "")
            
            # Verificar se arquivo existe
            if not os.path.exists(image_path):
                # Tentar caminhos alternativos
                alt_paths = [
                    os.path.join("assets", "logos", "world_comp_brasil.jpg"),
                    os.path.join("logo.jpg"),
                    "world_comp_brasil.jpg"
                ]
                
                for alt_path in alt_paths:
                    if os.path.exists(alt_path):
                        image_path = alt_path
                        break
                else:
                    print(f"⚠️ Imagem não encontrada: {image_path}")
                    return None
            
            # Dimensões do elemento (convertidas de pontos para units)
            width = element.get("w", 100) * 0.75  # Converter pontos para unidades
            height = element.get("h", 60) * 0.75
            
            return RLImage(image_path, width=width, height=height)
            
        except Exception as e:
            print(f"Erro ao criar imagem: {e}")
            return None
    
    def _create_line_from_template(self, element: Dict):
        """Criar linha baseada no template"""
        try:
            # Para linhas, criamos um spacer com borda
            width = element.get("w", 515) * 0.75
            
            # Criar parágrafo vazio com borda inferior
            style = ParagraphStyle(
                'Line',
                parent=getSampleStyleSheet()['Normal'],
                fontSize=1,
                spaceAfter=6,
                spaceBefore=6
            )
            
            return Paragraph("&nbsp;", style)
            
        except Exception as e:
            print(f"Erro ao criar linha: {e}")
            return None
    
    def _create_standard_header(self, data_resolver=None) -> List:
        """Criar cabeçalho padrão fiel ao gerador original"""
        elements = []
        
        try:
            # Cabeçalho como no gerador original: dados da proposta no canto superior esquerdo
            header_style = ParagraphStyle(
                'Header',
                parent=getSampleStyleSheet()['Normal'],
                fontName='Helvetica-Bold',
                fontSize=11,
                textColor=colors.black,
                spaceAfter=5,
                spaceBefore=0
            )
            
            # Dados da proposta (como no gerador original)
            if isinstance(data_resolver, dict):
                # Usar dados fictícios
                elements.append(Paragraph("WORLD COMP COMPRESSORES LTDA", header_style))
                elements.append(Paragraph("PROPOSTA COMERCIAL:", header_style))
                elements.append(Paragraph(f"NÚMERO: {data_resolver.get('numero_proposta', 'PROP-2024-001')}", header_style))
                elements.append(Paragraph(f"DATA: {data_resolver.get('data_criacao', '21/01/2025')}", header_style))
            else:
                # Fallback
                elements.append(Paragraph("WORLD COMP COMPRESSORES LTDA", header_style))
                elements.append(Paragraph("PROPOSTA COMERCIAL:", header_style))
                elements.append(Paragraph("NÚMERO: PROP-2024-001", header_style))
                elements.append(Paragraph("DATA: 21/01/2025", header_style))
            
            elements.append(Spacer(1, 10))
            
            # Linha de separação como no gerador original
            line_table = Table([[""]], colWidths=[503])
            line_table.setStyle(TableStyle([
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            elements.append(line_table)
            elements.append(Spacer(1, 10))
            
        except Exception as e:
            print(f"Erro ao criar cabeçalho: {e}")
        
        return elements
    
    def _create_page_border(self):
        """Criar borda da página fiel ao gerador original"""
        try:
            # Borda de 5mm de margem como no gerador original
            # Ajustar para o frame disponível do ReportLab
            # Frame normal: ~503 x ~750 pontos
            border_table = Table([[""]], colWidths=[503], rowHeights=[750])
            border_table.setStyle(TableStyle([
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            return border_table
        except Exception as e:
            print(f"Erro ao criar borda da página: {e}")
            return Spacer(1, 1)

    def _add_page_border_to_elements(self, elements: List) -> List:
        """Adicionar borda da página aos elementos"""
        try:
            # Criar borda
            border = self._create_page_border()
            if border:
                # Adicionar borda no início da lista de elementos
                elements.insert(0, border)
        except Exception as e:
            print(f"Erro ao adicionar borda da página: {e}")
        
        return elements
    
    def _create_standard_footer(self, page_num: int, data_resolver=None) -> List:
        """Criar rodapé padrão fiel ao gerador original"""
        elements = []
        
        try:
            # Espaçamento para posicionar na parte inferior
            elements.append(Spacer(1, 100))
            
            # Linha divisória acima do rodapé
            line_table = Table([[""]], colWidths=[503])
            line_table.setStyle(TableStyle([
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            elements.append(line_table)
            elements.append(Spacer(1, 5))
            
            # Rodapé como no gerador original: informações da filial centralizadas em azul bebê
            footer_style = ParagraphStyle(
                'Footer',
                parent=getSampleStyleSheet()['Normal'],
                fontName='Helvetica',
                fontSize=10,
                textColor=colors.HexColor('#89CFF0'),  # Azul bebê como no gerador
                alignment=TA_CENTER,
                spaceAfter=6,
                spaceBefore=0
            )
            
            # Dados fictícios da filial (como no gerador original)
            elements.append(Paragraph("Rua Fernando Pessoa, nº 11 - Batistini - São Bernardo do Campo - SP - CEP: 09843-000", footer_style))
            elements.append(Paragraph("CNPJ: 10.644.944/0001-55", footer_style))
            elements.append(Paragraph("E-mail: contato@worldcompressores.com.br | Fone: (11) 4543-6893 / 4543-6857", footer_style))
            
        except Exception as e:
            print(f"Erro ao criar rodapé: {e}")
        
        return elements

    def _create_page_template_with_footer(self, canvas, doc):
        """Criar template de página com rodapé na parte inferior"""
        # Salvar estado do canvas
        canvas.saveState()
        
        # Posicionar na parte inferior (1.5 cm do fundo)
        canvas.setFont("Helvetica", 10)
        canvas.setFillColor(colors.HexColor('#89CFF0'))  # Azul bebê
        
        # Linha divisória acima do rodapé
        canvas.setStrokeColor(colors.black)
        canvas.line(10, 25, 200, 25)
        
        # Texto do rodapé
        footer_text = [
            "Rua Fernando Pessoa, nº 11 - Batistini - São Bernardo do Campo - SP - CEP: 09843-000",
            "CNPJ: 10.644.944/0001-55",
            "E-mail: contato@worldcompressores.com.br | Fone: (11) 4543-6893 / 4543-6857"
        ]
        
        y_position = 20
        for text in footer_text:
            canvas.drawCentredString(105, y_position, text)
            y_position -= 5
        
        # Restaurar estado do canvas
        canvas.restoreState()

    def _create_capa_page(self, fake_data: Dict) -> List:
        """Criar página de capa fiel ao gerador original"""
        elements = []
        
        try:
            # Logo na primeira página (como no gerador original)
            logo_style = ParagraphStyle(
                'Logo',
                parent=getSampleStyleSheet()['Normal'],
                fontName='Helvetica-Bold',
                fontSize=14,
                textColor=colors.black,
                alignment=TA_CENTER,
                spaceAfter=30,
                spaceBefore=20
            )
            
            elements.append(Paragraph("WORLD COMP COMPRESSORES LTDA", logo_style))
            elements.append(Spacer(1, 20))
            
            # Título principal
            title_style = ParagraphStyle(
                'Title',
                parent=getSampleStyleSheet()['Title'],
                fontName='Helvetica-Bold',
                fontSize=16,
                textColor=colors.black,
                alignment=TA_CENTER,
                spaceAfter=20,
                spaceBefore=50
            )
            
            elements.append(Paragraph("PROPOSTA COMERCIAL", title_style))
            
            # Informações do cliente (centro-esquerda)
            info_style = ParagraphStyle(
                'Info',
                parent=getSampleStyleSheet()['Normal'],
                fontName='Helvetica-Bold',
                fontSize=12,
                textColor=colors.black,
                alignment=TA_CENTER,
                spaceAfter=10,
                spaceBefore=0
            )
            
            elements.append(Paragraph(f"EMPRESA: {fake_data['cliente_nome']}", info_style))
            elements.append(Paragraph(f"A/C SR. {fake_data['contato_nome']}", info_style))
            elements.append(Paragraph(f"DATA: {fake_data['data_criacao']}", info_style))
            
            # Informações do vendedor (canto inferior esquerdo)
            elements.append(Spacer(1, 100))
            vendedor_style = ParagraphStyle(
                'Vendedor',
                parent=getSampleStyleSheet()['Normal'],
                fontName='Helvetica',
                fontSize=10,
                textColor=colors.black,
                alignment=TA_LEFT,
                spaceAfter=5,
                spaceBefore=0,
                leftIndent=20
            )
            
            elements.append(Paragraph(f"Cliente: {fake_data['cliente_nome']}", vendedor_style))
            elements.append(Paragraph(f"Contato: {fake_data['contato_nome']}", vendedor_style))
            elements.append(Paragraph(f"Responsável: {fake_data['responsavel_nome']}", vendedor_style))
            
        except Exception as e:
            print(f"Erro ao criar página de capa: {e}")
        
        return elements

    def _create_apresentacao_page(self, fake_data: Dict) -> List:
        """Criar página de apresentação fiel ao gerador original"""
        elements = []
        
        try:
            # Logo centralizado (como no gerador original)
            logo_style = ParagraphStyle(
                'Logo',
                parent=getSampleStyleSheet()['Normal'],
                fontName='Helvetica-Bold',
                fontSize=14,
                textColor=colors.black,
                alignment=TA_CENTER,
                spaceAfter=30,
                spaceBefore=20
            )
            
            elements.append(Paragraph("WORLD COMP COMPRESSORES LTDA", logo_style))
            elements.append(Spacer(1, 20))
            
            # Posição para dados do cliente e empresa (como no gerador original)
            # Dados do cliente (lado esquerdo) e empresa (lado direito)
            section_style = ParagraphStyle(
                'Section',
                parent=getSampleStyleSheet()['Normal'],
                fontName='Helvetica-Bold',
                fontSize=10,
                textColor=colors.black,
                alignment=TA_LEFT,
                spaceAfter=5,
                spaceBefore=0
            )
            
            # Criar tabela para as duas colunas (como no gerador original)
            apresentacao_data = [
                ["APRESENTADO PARA:", "APRESENTADO POR:"],
                [fake_data['cliente_nome'], fake_data['filial_nome']],
                [f"CNPJ: {fake_data['cliente_cnpj']}", f"CNPJ: {fake_data['filial_cnpj']}"],
                [f"FONE: {fake_data['cliente_telefone']}", f"FONE: {fake_data['filial_telefones']}"],
                [f"Sr(a). {fake_data['contato_nome']}", f"E-mail: {fake_data['responsavel_email']}"],
                ["", f"Responsável: {fake_data['responsavel_nome']}"]
            ]
            
            apresentacao_table = Table(apresentacao_data, colWidths=[250, 250])
            apresentacao_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
            ]))
            
            elements.append(apresentacao_table)
            elements.append(Spacer(1, 20))
            
            # Texto de apresentação (como no gerador original)
            texto_style = ParagraphStyle(
                'Texto',
                parent=getSampleStyleSheet()['Normal'],
                fontName='Helvetica',
                fontSize=11,
                textColor=colors.black,
                alignment=TA_LEFT,
                spaceAfter=6,
                spaceBefore=0,
                leading=14  # Espaçamento entre linhas
            )
            
            texto_apresentacao = f"""
Prezados Senhores,

Agradecemos a sua solicitação e apresentamos nossas condições comerciais para fornecimento de peças para o compressor {fake_data['modelo_compressor']}.

A World Comp coloca-se a disposição para analisar, corrigir, prestar esclarecimentos para adequação das especificações e necessidades dos clientes, para tanto basta informar o número da proposta e revisão.

Atenciosamente,
            """.strip()
            
            elements.append(Paragraph(texto_apresentacao, texto_style))
            
            # Assinatura na parte inferior da página (como no gerador original)
            elements.append(Spacer(1, 30))
            assinatura_style = ParagraphStyle(
                'Assinatura',
                parent=getSampleStyleSheet()['Normal'],
                fontName='Helvetica-Bold',
                fontSize=11,
                textColor=colors.black,
                alignment=TA_LEFT,
                spaceAfter=5,
                spaceBefore=0
            )
            
            elements.append(Paragraph(fake_data['responsavel_nome'].upper(), assinatura_style))
            elements.append(Paragraph("Vendas", assinatura_style))
            elements.append(Paragraph(f"Fone: {fake_data['filial_telefones']}", assinatura_style))
            elements.append(Paragraph(fake_data['filial_nome'], assinatura_style))
            
        except Exception as e:
            print(f"Erro ao criar página de apresentação: {e}")
        
        return elements

    def _create_sobre_empresa_page(self, fake_data: Dict) -> List:
        """Criar página sobre a empresa fiel ao gerador original"""
        elements = []
        
        try:
            # Título
            title_style = ParagraphStyle(
                'Title',
                parent=getSampleStyleSheet()['Title'],
                fontName='Helvetica-Bold',
                fontSize=12,
                textColor=colors.black,
                alignment=TA_LEFT,
                spaceAfter=10,
                spaceBefore=0
            )
            
            elements.append(Paragraph("SOBRE A WORLD COMP", title_style))
            
            # Texto sobre a empresa
            texto_style = ParagraphStyle(
                'Texto',
                parent=getSampleStyleSheet()['Normal'],
                fontName='Helvetica',
                fontSize=11,
                textColor=colors.black,
                alignment=TA_LEFT,
                spaceAfter=6,
                spaceBefore=0,
                leading=14  # Espaçamento entre linhas
            )
            
            sobre_empresa = "Há mais de uma década no mercado de manutenção de compressores de ar de parafuso, de diversas marcas, atendemos clientes em todo território brasileiro."
            elements.append(Paragraph(sobre_empresa, texto_style))
            elements.append(Spacer(1, 10))
            
            # Seções sobre a empresa
            secoes = [
                ("FORNECIMENTO, SERVIÇO E LOCAÇÃO", "A World Comp oferece os serviços de Manutenção Preventiva e Corretiva em Compressores e Unidades Compressoras, Venda de peças, Locação de compressores, Recuperação de Unidades Compressoras, Recuperação de Trocadores de Calor e Contrato de Manutenção em compressores de marcas como: Atlas Copco, Ingersoll Rand, Chicago Pneumatic entre outros."),
                ("CONTE CONOSCO PARA UMA PARCERIA", "Adaptamos nossa oferta para suas necessidades, objetivos e planejamento. Trabalhamos para que seu processo seja eficiente."),
                ("MELHORIA CONTÍNUA", "Continuamente investindo em comprometimento, competência e eficiência de nossos serviços, produtos e estrutura para garantirmos a máxima eficiência de sua produtividade."),
                ("QUALIDADE DE SERVIÇOS", "Com uma equipe de técnicos altamente qualificados e constantemente treinados para atendimentos em todos os modelos de compressores de ar, a World Comp oferece garantia de excelente atendimento e produtividade superior com rapidez e eficácia.")
            ]
            
            for titulo, texto in secoes:
                # Título da seção em azul bebê
                titulo_style = ParagraphStyle(
                    'TituloSecao',
                    parent=getSampleStyleSheet()['Normal'],
                    fontName='Helvetica-Bold',
                    fontSize=12,
                    textColor=colors.HexColor('#89CFF0'),  # Azul bebê
                    alignment=TA_LEFT,
                    spaceAfter=5,
                    spaceBefore=10
                )
                
                elements.append(Paragraph(titulo, titulo_style))
                elements.append(Paragraph(texto, texto_style))
                elements.append(Spacer(1, 5))
            
            # Texto final
            texto_final = "Nossa missão é ser sua melhor parceria com sinônimo de qualidade, garantia e o melhor custo benefício."
            elements.append(Paragraph(texto_final, texto_style))
            
        except Exception as e:
            print(f"Erro ao criar página sobre a empresa: {e}")
        
        return elements

    def _create_proposta_page(self, fake_data: Dict) -> List:
        """Criar página da proposta fiel ao gerador original"""
        elements = []
        
        try:
            # Dados da proposta
            title_style = ParagraphStyle(
                'Title',
                parent=getSampleStyleSheet()['Title'],
                fontName='Helvetica-Bold',
                fontSize=12,
                textColor=colors.black,
                alignment=TA_LEFT,
                spaceAfter=8,
                spaceBefore=0
            )
            
            elements.append(Paragraph(f"PROPOSTA Nº {fake_data['numero_proposta']}", title_style))
            
            # Informações da proposta
            info_style = ParagraphStyle(
                'Info',
                parent=getSampleStyleSheet()['Normal'],
                fontName='Helvetica',
                fontSize=11,
                textColor=colors.black,
                alignment=TA_LEFT,
                spaceAfter=5,
                spaceBefore=0
            )
            
            elements.append(Paragraph(f"Data: {fake_data['data_criacao']}", info_style))
            elements.append(Paragraph(f"Responsável: {fake_data['responsavel_nome']}", info_style))
            elements.append(Paragraph(f"Telefone Responsável: {fake_data['filial_telefones']}", info_style))
            elements.append(Spacer(1, 15))
            
            # Dados do cliente
            elements.append(Paragraph("DADOS DO CLIENTE:", title_style))
            elements.append(Paragraph(f"Empresa: {fake_data['cliente_nome']}", info_style))
            elements.append(Paragraph(f"CNPJ: {fake_data['cliente_cnpj']}", info_style))
            elements.append(Paragraph(f"Contato: {fake_data['contato_nome']}", info_style))
            elements.append(Spacer(1, 10))
            
            # Dados do compressor
            elements.append(Paragraph("DADOS DO COMPRESSOR:", title_style))
            elements.append(Paragraph(f"Modelo: {fake_data['modelo_compressor']}", info_style))
            elements.append(Paragraph(f"Nº de Série: {fake_data['numero_serie_compressor']}", info_style))
            elements.append(Spacer(1, 10))
            
            # Descrição do serviço
            elements.append(Paragraph("DESCRIÇÃO DO SERVIÇO:", title_style))
            elements.append(Paragraph("Fornecimento de peças e serviços para compressor", info_style))
            elements.append(Spacer(1, 15))
            
            # Tabela de itens da proposta
            elements.append(Paragraph("ITENS DA PROPOSTA", title_style))
            elements.append(Spacer(1, 10))
            
            # Cabeçalho da tabela
            header_data = [["Item", "Descrição", "Qtd.", "Valor Unitário", "Valor Total"]]
            header_table = Table(header_data, colWidths=[30, 200, 30, 80, 80])
            header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#326BA8')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(header_table)
            
            # Itens fictícios da proposta
            itens_data = [
                ["1", "Kit de Filtros", "1", "R$ 2.500,00", "R$ 2.500,00"],
                ["2", "Óleo Lubrificante", "10", "R$ 150,00", "R$ 1.500,00"],
                ["3", "Mão de Obra", "1", "R$ 1.200,00", "R$ 1.200,00"],
                ["4", "Deslocamento", "1", "R$ 800,00", "R$ 800,00"]
            ]
            
            for item in itens_data:
                item_table = Table([item], colWidths=[30, 200, 30, 80, 80])
                item_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('ALIGN', (1, 0), (1, 0), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(item_table)
            
            # Valor total
            elements.append(Spacer(1, 10))
            total_data = [["", "", "", "VALOR TOTAL DA PROPOSTA:", fake_data['valor_total']]]
            total_table = Table(total_data, colWidths=[30, 200, 30, 80, 80])
            total_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (3, 0), (3, 0), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(total_table)
            elements.append(Spacer(1, 15))
            
            # Condições comerciais (como no gerador original)
            elements.append(Paragraph("CONDIÇÕES COMERCIAIS:", title_style))
            elements.append(Paragraph("Tipo de Frete: FOB", info_style))
            elements.append(Paragraph("Condição de Pagamento: A combinar", info_style))
            elements.append(Paragraph("Prazo de Entrega: A combinar", info_style))
            elements.append(Paragraph("Moeda: BRL (Real Brasileiro)", info_style))
            elements.append(Spacer(1, 10))
            
            # Observações
            elements.append(Paragraph("OBSERVAÇÕES:", title_style))
            elements.append(Paragraph("Proposta válida por 30 dias. Preços sujeitos a alteração sem aviso prévio.", info_style))
            
        except Exception as e:
            print(f"Erro ao criar página da proposta: {e}")
        
        return elements