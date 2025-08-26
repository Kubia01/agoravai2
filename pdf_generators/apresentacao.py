import os
import sqlite3
from datetime import datetime
from fpdf import FPDF
from database import DB_NAME

TITLE = "Proposta Comercial"

SECTIONS = [
	("Descrição Geral", "Sistema desktop para gestão comercial e técnica, com foco em cotações (compra e locação), relatórios técnicos, clientes, produtos, usuários e geração de PDFs executivos. Facilita o ciclo comercial completo: cadastro, proposta, acompanhamento e documentação."),
	("Principais Benefícios", "Velocidade na geração de propostas; padronização de documentos comerciais; histórico organizado; redução de retrabalho; exportação de consultas para Excel; apresentação profissional para clientes."),
]

class ExecPDF(FPDF):
	def header(self):
		self.set_auto_page_break(auto=True, margin=20)
		self.set_font("Arial", 'B', 16)
		self.set_text_color(30, 41, 59)
		self.cell(0, 10, TITLE, 0, 1, 'L')
		self.ln(2)
		self.set_draw_color(200, 200, 200)
		self.line(10, self.get_y(), 200, self.get_y())
		self.ln(6)
	def footer(self):
		self.set_y(-15)
		self.set_font("Arial", '', 9)
		self.set_text_color(100, 116, 139)
		self.cell(0, 10, f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} • Página {self.page_no()}", 0, 0, 'R')


def _clean(txt: str) -> str:
	return (txt or "").replace("\t", " ")


def _list_modules() -> list:
	# Mapear módulos pela estrutura do diretório interface/modules
	modules = []
	try:
		modules_dir = os.path.join(os.path.dirname(__file__), '..', 'interface', 'modules')
		modules_dir = os.path.abspath(modules_dir)
		for f in sorted(os.listdir(modules_dir)):
			if f.endswith('.py') and f not in ('__init__.py',):
				modules.append(f.replace('.py', ''))
	except Exception:
		pass
	return modules


def _db_overview() -> dict:
	info = {"tables": []}
	try:
		conn = sqlite3.connect(DB_NAME)
		c = conn.cursor()
		c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
		tables = [r[0] for r in c.fetchall()]
		for t in tables:
			try:
				c.execute(f"PRAGMA table_info({t})")
				cols = [row[1] for row in c.fetchall()]
				info["tables"].append((t, cols))
			except sqlite3.Error:
				info["tables"].append((t, []))
	finally:
		try:
			conn.close()
		except Exception:
			pass
	return info


def gerar_pdf_apresentacao(output_path: str = None) -> tuple:
	"""
	Gera o documento executivo de apresentação do sistema em PDF.
	Retorna (True, caminho) em sucesso ou (False, erro).
	"""
	try:
		modules = _list_modules()
		db = _db_overview()

		pdf = ExecPDF(orientation='P', unit='mm', format='A4')
		pdf.add_page()

		# Seção: Descrição geral + benefícios
		pdf.set_font("Arial", '', 12)
		for title, body in SECTIONS:
			pdf.set_text_color(2, 132, 199)
			pdf.set_font("Arial", 'B', 14)
			pdf.cell(0, 8, _clean(title), 0, 1, 'L')
			pdf.set_text_color(0, 0, 0)
			pdf.set_font("Arial", '', 11)
			pdf.multi_cell(0, 6, _clean(body))
			pdf.ln(3)

		# Seção: Estrutura dos Módulos
		pdf.set_text_color(2, 132, 199)
		pdf.set_font("Arial", 'B', 14)
		pdf.cell(0, 8, _clean("Estrutura de Módulos"), 0, 1, 'L')
		pdf.set_text_color(0, 0, 0)
		pdf.set_font("Arial", '', 11)
		if modules:
			pdf.multi_cell(0, 6, _clean("Módulos presentes no sistema:"))
			pdf.ln(2)
			for m in modules:
				pdf.cell(0, 6, f"- {m}", 0, 1, 'L')
		else:
			pdf.cell(0, 6, "(Não foi possível mapear módulos)", 0, 1, 'L')
		pdf.ln(3)

		# Seção: Funcionalidades
		pdf.set_text_color(2, 132, 199)
		pdf.set_font("Arial", 'B', 14)
		pdf.cell(0, 8, _clean("Funcionalidades"), 0, 1, 'L')
		pdf.set_text_color(0, 0, 0)
		pdf.set_font("Arial", '', 11)
		features = [
			"Gestão de cotações de Compra e Locação (numeração distinta, filtros e histórico)",
			"Geração de PDF de propostas com layout executivo (capas, páginas temáticas, termos)",
			"Inserção de itens com valores, meses/contrato, imagens e cálculo automático de totais",
			"Gestão de clientes, contatos associados e responsáveis",
			"Relatórios técnicos com registro de serviços, tempos e peças",
			"Consultas avançadas com exportação para Excel (openpyxl)",
			"Configuração de filiais e dados fiscais (rodapés, CNPJ, telefones, e-mail)",
		]
		for f in features:
			pdf.cell(0, 6, f"- {f}", 0, 1, 'L')
		pdf.ln(3)

		# Seção: Como funciona / Problemas resolvidos
		pdf.set_text_color(2, 132, 199)
		pdf.set_font("Arial", 'B', 14)
		pdf.cell(0, 8, _clean("Como o sistema funciona"), 0, 1, 'L')
		pdf.set_text_color(0, 0, 0)
		pdf.set_font("Arial", '', 11)
		pdf.multi_cell(0, 6, _clean(
			"O usuário registra clientes, seleciona uma filial e cria cotações com itens, prazos e condições. \n"
			"Durante a criação, o sistema calcula totais, permite anexar imagens e gera PDFs padronizados. \n"
			"Consultas e relatórios podem ser emitidos e exportados para Excel."
		))
		pdf.ln(3)

		# Seção: Integrações e conexões
		pdf.set_text_color(2, 132, 199)
		pdf.set_font("Arial", 'B', 14)
		pdf.cell(0, 8, _clean("Conexões e Integrações"), 0, 1, 'L')
		pdf.set_text_color(0, 0, 0)
		pdf.set_font("Arial", '', 11)
		pdf.cell(0, 6, "- Banco de dados: SQLite local (arquivo) ", 0, 1, 'L')
		pdf.cell(0, 6, "- Geração de PDFs: fpdf2", 0, 1, 'L')
		pdf.cell(0, 6, "- Exportação Excel: openpyxl", 0, 1, 'L')
		pdf.ln(3)

		# Seção: Estrutura do banco de dados (resumo)
		pdf.set_text_color(2, 132, 199)
		pdf.set_font("Arial", 'B', 14)
		pdf.cell(0, 8, _clean("Estrutura do Banco de Dados (resumo)"), 0, 1, 'L')
		pdf.set_text_color(0, 0, 0)
		pdf.set_font("Arial", '', 10)
		for (t, cols) in db.get("tables", [])[:20]:  # limitar listagem
			pdf.cell(0, 5, f"- {t}: {', '.join(cols) if cols else '(colunas não mapeadas)'}", 0, 1, 'L')
		pdf.ln(3)

		# Seção: Estrutura de módulos (detalhada)
		pdf.set_text_color(2, 132, 199)
		pdf.set_font("Arial", 'B', 14)
		pdf.cell(0, 8, _clean("Módulos (detalhamento sintético)"), 0, 1, 'L')
		pdf.set_text_color(0, 0, 0)
		pdf.set_font("Arial", '', 11)
		for m in modules:
			pdf.cell(0, 6, f"- {m}", 0, 1, 'L')
		pdf.ln(3)

		# Salvar
		if not output_path:
			output_dir = os.path.join('data', 'docs')
			os.makedirs(output_dir, exist_ok=True)
			output_path = os.path.join(output_dir, 'Apresentacao_Proposta_Comercial.pdf')
		pdf.output(output_path)
		return True, output_path
	except Exception as e:
		return False, str(e)