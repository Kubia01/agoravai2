import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sqlite3
from datetime import datetime, timedelta
from .base_module import BaseModule
from database import DB_NAME
from utils.formatters import format_currency, format_date

class ConsultasModule(BaseModule):
    def setup_ui(self):
        # Container principal
        container = tk.Frame(self.frame, bg='#f8fafc')
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        self.create_header(container)
        
        # Notebook para organizar seções
        self.notebook = ttk.Notebook(container)
        self.notebook.pack(fill="both", expand=True, pady=(20, 0))
        
        # Aba: Consultas por Status
        self.create_consultas_status_tab()
        
        # Aba: Consultas por Usuário
        self.create_consultas_usuario_tab()
        
        # Aba: Consultas de Faturamento
        self.create_consultas_faturamento_tab()
        
        # Aba: Consultas Personalizadas
        self.create_consultas_personalizadas_tab()
        
        # Inicializar variáveis
        self.current_user_id = None
        
    def create_header(self, parent):
        header_frame = tk.Frame(parent, bg='#f8fafc')
        header_frame.pack(fill="x", pady=(0, 20))
        
        title_label = tk.Label(header_frame, text="Consultas Avançadas", 
                               font=('Arial', 18, 'bold'),
                               bg='#f8fafc',
                               fg='#1e293b')
        title_label.pack(side="left")
        
    def create_consultas_status_tab(self):
        """Criar aba de consultas por status"""
        status_frame = tk.Frame(self.notebook, bg='white')
        self.notebook.add(status_frame, text="Por Status")
        
        content_frame = tk.Frame(status_frame, bg='white', padx=20, pady=20)
        content_frame.pack(fill="both", expand=True)
        
        # Frame de filtros
        filtros_frame = tk.Frame(content_frame, bg='white')
        filtros_frame.pack(fill="x", pady=(0, 15))
        
        # Status
        tk.Label(filtros_frame, text="Status:", font=('Arial', 10, 'bold'), bg='white').pack(side="left")
        self.status_var = tk.StringVar(value="Todas")
        status_combo = ttk.Combobox(filtros_frame, textvariable=self.status_var, 
                                   values=["Todas", "Em Aberto", "Aprovada", "Rejeitada"], 
                                   width=15, state="readonly")
        status_combo.pack(side="left", padx=(10, 20))
        
        # Período
        tk.Label(filtros_frame, text="Período:", font=('Arial', 10, 'bold'), bg='white').pack(side="left")
        self.periodo_var = tk.StringVar(value="Últimos 30 dias")
        periodo_combo = ttk.Combobox(filtros_frame, textvariable=self.periodo_var, 
                                    values=["Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias", "Este ano", "Todos"], 
                                    width=15, state="readonly")
        periodo_combo.pack(side="left", padx=(10, 20))
        
        # Botão consultar
        consultar_btn = self.create_button(filtros_frame, "Consultar", self.consultar_por_status, bg='#3b82f6')
        consultar_btn.pack(side="left", padx=(10, 0))
        
        # Treeview para resultados
        columns = ("numero", "cliente", "responsavel", "data", "status", "valor")
        self.status_tree = ttk.Treeview(content_frame, columns=columns, show="headings", height=15)
        
        self.status_tree.heading("numero", text="Número")
        self.status_tree.heading("cliente", text="Cliente")
        self.status_tree.heading("responsavel", text="Responsável")
        self.status_tree.heading("data", text="Data")
        self.status_tree.heading("status", text="Status")
        self.status_tree.heading("valor", text="Valor")
        
        self.status_tree.column("numero", width=150)
        self.status_tree.column("cliente", width=200)
        self.status_tree.column("responsavel", width=150)
        self.status_tree.column("data", width=100)
        self.status_tree.column("status", width=100)
        self.status_tree.column("valor", width=120)
        
        # Scrollbar
        status_scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=self.status_tree.yview)
        self.status_tree.configure(yscrollcommand=status_scrollbar.set)
        
        self.status_tree.pack(side="left", fill="both", expand=True)
        status_scrollbar.pack(side="right", fill="y")
        
    def create_consultas_usuario_tab(self):
        """Criar aba de consultas por usuário"""
        usuario_frame = tk.Frame(self.notebook, bg='white')
        self.notebook.add(usuario_frame, text="Por Usuário")
        
        content_frame = tk.Frame(usuario_frame, bg='white', padx=20, pady=20)
        content_frame.pack(fill="both", expand=True)
        
        # Frame de filtros
        filtros_frame = tk.Frame(content_frame, bg='white')
        filtros_frame.pack(fill="x", pady=(0, 15))
        
        # Usuário
        tk.Label(filtros_frame, text="Usuário:", font=('Arial', 10, 'bold'), bg='white').pack(side="left")
        self.usuario_var = tk.StringVar()
        self.usuario_combo = ttk.Combobox(filtros_frame, textvariable=self.usuario_var, width=25)
        self.usuario_combo.pack(side="left", padx=(10, 20))
        
        # Tipo de consulta
        tk.Label(filtros_frame, text="Tipo:", font=('Arial', 10, 'bold'), bg='white').pack(side="left")
        self.tipo_usuario_var = tk.StringVar(value="Cotações")
        tipo_combo = ttk.Combobox(filtros_frame, textvariable=self.tipo_usuario_var, 
                                 values=["Cotações", "Relatórios", "Faturamento"], 
                                 width=15, state="readonly")
        tipo_combo.pack(side="left", padx=(10, 20))
        
        # Botão consultar
        consultar_btn = self.create_button(filtros_frame, "Consultar", self.consultar_por_usuario, bg='#3b82f6')
        consultar_btn.pack(side="left", padx=(10, 0))
        
        # Treeview para resultados
        columns = ("data", "tipo", "numero", "cliente", "valor")
        self.usuario_tree = ttk.Treeview(content_frame, columns=columns, show="headings", height=15)
        
        self.usuario_tree.heading("data", text="Data")
        self.usuario_tree.heading("tipo", text="Tipo")
        self.usuario_tree.heading("numero", text="Número")
        self.usuario_tree.heading("cliente", text="Cliente")
        self.usuario_tree.heading("valor", text="Valor")
        
        self.usuario_tree.column("data", width=100)
        self.usuario_tree.column("tipo", width=100)
        self.usuario_tree.column("numero", width=150)
        self.usuario_tree.column("cliente", width=200)
        self.usuario_tree.column("valor", width=120)
        
        # Scrollbar
        usuario_scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=self.usuario_tree.yview)
        self.usuario_tree.configure(yscrollcommand=usuario_scrollbar.set)
        
        self.usuario_tree.pack(side="left", fill="both", expand=True)
        usuario_scrollbar.pack(side="right", fill="y")
        
        # Carregar usuários
        self.carregar_usuarios()
        
    def create_consultas_faturamento_tab(self):
        """Criar aba de consultas de faturamento"""
        faturamento_frame = tk.Frame(self.notebook, bg='white')
        self.notebook.add(faturamento_frame, text="Faturamento")
        
        content_frame = tk.Frame(faturamento_frame, bg='white', padx=20, pady=20)
        content_frame.pack(fill="both", expand=True)
        
        # Frame de filtros
        filtros_frame = tk.Frame(content_frame, bg='white')
        filtros_frame.pack(fill="x", pady=(0, 15))
        
        # Tipo de faturamento
        tk.Label(filtros_frame, text="Tipo:", font=('Arial', 10, 'bold'), bg='white').pack(side="left")
        self.tipo_faturamento_var = tk.StringVar(value="Por Usuário")
        tipo_combo = ttk.Combobox(filtros_frame, textvariable=self.tipo_faturamento_var, 
                                 values=["Por Usuário", "Por Tipo de Produto", "Por Cliente"], 
                                 width=15, state="readonly")
        tipo_combo.pack(side="left", padx=(10, 20))
        
        # Período
        tk.Label(filtros_frame, text="Período:", font=('Arial', 10, 'bold'), bg='white').pack(side="left")
        self.periodo_faturamento_var = tk.StringVar(value="Este mês")
        periodo_combo = ttk.Combobox(filtros_frame, textvariable=self.periodo_faturamento_var, 
                                    values=["Este mês", "Mês passado", "Este trimestre", "Este ano"], 
                                    width=15, state="readonly")
        periodo_combo.pack(side="left", padx=(10, 20))
        
        # Botão consultar
        consultar_btn = self.create_button(filtros_frame, "Consultar", self.consultar_faturamento, bg='#3b82f6')
        consultar_btn.pack(side="left", padx=(10, 0))
        
        # Treeview para resultados
        columns = ("categoria", "quantidade", "valor_total", "media")
        self.faturamento_tree = ttk.Treeview(content_frame, columns=columns, show="headings", height=15)
        
        self.faturamento_tree.heading("categoria", text="Categoria")
        self.faturamento_tree.heading("quantidade", text="Quantidade")
        self.faturamento_tree.heading("valor_total", text="Valor Total")
        self.faturamento_tree.heading("media", text="Média")
        
        self.faturamento_tree.column("categoria", width=200)
        self.faturamento_tree.column("quantidade", width=100)
        self.faturamento_tree.column("valor_total", width=150)
        self.faturamento_tree.column("media", width=120)
        
        # Scrollbar
        faturamento_scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=self.faturamento_tree.yview)
        self.faturamento_tree.configure(yscrollcommand=faturamento_scrollbar.set)
        
        self.faturamento_tree.pack(side="left", fill="both", expand=True)
        faturamento_scrollbar.pack(side="right", fill="y")
        
    def create_consultas_personalizadas_tab(self):
        """Criar aba de consultas personalizadas"""
        personalizada_frame = tk.Frame(self.notebook, bg='white')
        self.notebook.add(personalizada_frame, text="Personalizadas")
        
        content_frame = tk.Frame(personalizada_frame, bg='white', padx=20, pady=20)
        content_frame.pack(fill="both", expand=True)
        
        # Frame de consulta SQL
        sql_frame = tk.Frame(content_frame, bg='white')
        sql_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        tk.Label(sql_frame, text="Consulta SQL:", font=('Arial', 10, 'bold'), bg='white').pack(anchor="w")
        
        self.sql_text = scrolledtext.ScrolledText(sql_frame, height=8, width=80)
        self.sql_text.pack(fill="both", expand=True, pady=(5, 10))
        
        # Exemplos de consultas
        exemplos_frame = tk.Frame(sql_frame, bg='white')
        exemplos_frame.pack(fill="x")
        
        tk.Label(exemplos_frame, text="Exemplos:", font=('Arial', 10, 'bold'), bg='white').pack(anchor="w")
        
        exemplos = [
            "SELECT COUNT(*) as total FROM cotacoes WHERE status = 'Aprovada'",
            "SELECT u.nome_completo, COUNT(c.id) as cotações FROM usuarios u LEFT JOIN cotacoes c ON u.id = c.responsavel_id GROUP BY u.id",
            "SELECT c.nome, SUM(co.valor_total) as faturamento FROM clientes c LEFT JOIN cotacoes co ON c.id = co.cliente_id GROUP BY c.id"
        ]
        
        for exemplo in exemplos:
            exemplo_btn = tk.Button(exemplos_frame, text=exemplo, 
                                   command=lambda e=exemplo: self.sql_text.insert("1.0", e),
                                   bg='#f1f5f9', relief='flat', cursor='hand2')
            exemplo_btn.pack(fill="x", pady=2)
        
        # Botões
        buttons_frame = tk.Frame(content_frame, bg='white')
        buttons_frame.pack(fill="x")
        
        executar_btn = self.create_button(buttons_frame, "Executar Consulta", self.executar_consulta_personalizada, bg='#10b981')
        executar_btn.pack(side="left", padx=(0, 10))
        
        limpar_btn = self.create_button(buttons_frame, "Limpar", lambda: self.sql_text.delete("1.0", tk.END), bg='#f59e0b')
        limpar_btn.pack(side="left")
        
        # Treeview para resultados
        columns = ("resultado")
        self.personalizada_tree = ttk.Treeview(content_frame, columns=columns, show="headings", height=10)
        
        self.personalizada_tree.heading("resultado", text="Resultado")
        self.personalizada_tree.column("resultado", width=600)
        
        # Scrollbar
        personalizada_scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=self.personalizada_tree.yview)
        self.personalizada_tree.configure(yscrollcommand=personalizada_scrollbar.set)
        
        self.personalizada_tree.pack(side="left", fill="both", expand=True)
        personalizada_scrollbar.pack(side="right", fill="y")
        
    def carregar_usuarios(self):
        """Carregar lista de usuários"""
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            
            c.execute("SELECT id, nome_completo FROM usuarios ORDER BY nome_completo")
            usuarios = c.fetchall()
            
            # Popular combobox
            valores = [f"{row[1]} (ID: {row[0]})" for row in usuarios]
            self.usuario_combo['values'] = valores
            
            # Armazenar mapeamento
            self.usuarios_dict = {f"{row[1]} (ID: {row[0]})": row[0] for row in usuarios}
            
        except sqlite3.Error as e:
            self.show_error(f"Erro ao carregar usuários: {e}")
        finally:
            conn.close()
            
    def consultar_por_status(self):
        """Consultar cotações por status"""
        # Limpar resultados
        for item in self.status_tree.get_children():
            self.status_tree.delete(item)
            
        status = self.status_var.get()
        periodo = self.periodo_var.get()
        
        # Calcular data limite
        data_limite = self.calcular_data_limite(periodo)
        
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            
            if status == "Todas":
                if data_limite:
                    c.execute("""
                        SELECT c.numero_proposta, cl.nome, u.nome_completo, c.data_criacao, c.status, c.valor_total
                        FROM cotacoes c
                        JOIN clientes cl ON c.cliente_id = cl.id
                        JOIN usuarios u ON c.responsavel_id = u.id
                        WHERE c.data_criacao >= ?
                        ORDER BY c.data_criacao DESC
                    """, (data_limite,))
                else:
                    c.execute("""
                        SELECT c.numero_proposta, cl.nome, u.nome_completo, c.data_criacao, c.status, c.valor_total
                        FROM cotacoes c
                        JOIN clientes cl ON c.cliente_id = cl.id
                        JOIN usuarios u ON c.responsavel_id = u.id
                        ORDER BY c.data_criacao DESC
                    """)
            else:
                if data_limite:
                    c.execute("""
                        SELECT c.numero_proposta, cl.nome, u.nome_completo, c.data_criacao, c.status, c.valor_total
                        FROM cotacoes c
                        JOIN clientes cl ON c.cliente_id = cl.id
                        JOIN usuarios u ON c.responsavel_id = u.id
                        WHERE c.status = ? AND c.data_criacao >= ?
                        ORDER BY c.data_criacao DESC
                    """, (status, data_limite))
                else:
                    c.execute("""
                        SELECT c.numero_proposta, cl.nome, u.nome_completo, c.data_criacao, c.status, c.valor_total
                        FROM cotacoes c
                        JOIN clientes cl ON c.cliente_id = cl.id
                        JOIN usuarios u ON c.responsavel_id = u.id
                        WHERE c.status = ?
                        ORDER BY c.data_criacao DESC
                    """, (status,))
            
            for row in c.fetchall():
                numero, cliente, responsavel, data, status, valor = row
                self.status_tree.insert("", "end", values=(
                    numero,
                    cliente,
                    responsavel,
                    format_date(data),
                    status,
                    format_currency(valor or 0)
                ))
                
        except sqlite3.Error as e:
            self.show_error(f"Erro ao consultar: {e}")
        finally:
            conn.close()
            
    def consultar_por_usuario(self):
        """Consultar por usuário"""
        # Limpar resultados
        for item in self.usuario_tree.get_children():
            self.usuario_tree.delete(item)
            
        usuario_str = self.usuario_var.get()
        tipo = self.tipo_usuario_var.get()
        
        if not usuario_str:
            self.show_warning("Selecione um usuário.")
            return
            
        # Obter ID do usuário
        usuario_id = self.usuarios_dict.get(usuario_str)
        if not usuario_id:
            self.show_warning("Usuário selecionado inválido.")
            return
            
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            
            if tipo == "Cotações":
                c.execute("""
                    SELECT c.data_criacao, 'Cotação' as tipo, c.numero_proposta, cl.nome, c.valor_total
                    FROM cotacoes c
                    JOIN clientes cl ON c.cliente_id = cl.id
                    WHERE c.responsavel_id = ?
                    ORDER BY c.data_criacao DESC
                """, (usuario_id,))
            elif tipo == "Relatórios":
                c.execute("""
                    SELECT r.data_criacao, 'Relatório' as tipo, r.numero_relatorio, cl.nome, 0 as valor
                    FROM relatorios_tecnicos r
                    JOIN clientes cl ON r.cliente_id = cl.id
                    WHERE r.responsavel_id = ?
                    ORDER BY r.data_criacao DESC
                """, (usuario_id,))
            else:  # Faturamento
                c.execute("""
                    SELECT c.data_criacao, 'Cotação' as tipo, c.numero_proposta, cl.nome, c.valor_total
                    FROM cotacoes c
                    JOIN clientes cl ON c.cliente_id = cl.id
                    WHERE c.responsavel_id = ? AND c.status = 'Aprovada'
                    ORDER BY c.data_criacao DESC
                """, (usuario_id,))
            
            for row in c.fetchall():
                data, tipo, numero, cliente, valor = row
                self.usuario_tree.insert("", "end", values=(
                    format_date(data),
                    tipo,
                    numero,
                    cliente,
                    format_currency(valor or 0)
                ))
                
        except sqlite3.Error as e:
            self.show_error(f"Erro ao consultar: {e}")
        finally:
            conn.close()
            
    def consultar_faturamento(self):
        """Consultar faturamento"""
        # Limpar resultados
        for item in self.faturamento_tree.get_children():
            self.faturamento_tree.delete(item)
            
        tipo = self.tipo_faturamento_var.get()
        periodo = self.periodo_faturamento_var.get()
        
        # Calcular data limite
        data_limite = self.calcular_data_limite(periodo)
        
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            
            if tipo == "Por Usuário":
                if data_limite:
                    c.execute("""
                        SELECT u.nome_completo, COUNT(c.id) as quantidade, 
                               SUM(c.valor_total) as valor_total, AVG(c.valor_total) as media
                        FROM usuarios u
                        LEFT JOIN cotacoes c ON u.id = c.responsavel_id AND c.data_criacao >= ?
                        WHERE c.status = 'Aprovada'
                        GROUP BY u.id, u.nome_completo
                        ORDER BY valor_total DESC
                    """, (data_limite,))
                else:
                    c.execute("""
                        SELECT u.nome_completo, COUNT(c.id) as quantidade, 
                               SUM(c.valor_total) as valor_total, AVG(c.valor_total) as media
                        FROM usuarios u
                        LEFT JOIN cotacoes c ON u.id = c.responsavel_id
                        WHERE c.status = 'Aprovada'
                        GROUP BY u.id, u.nome_completo
                        ORDER BY valor_total DESC
                    """)
            elif tipo == "Por Tipo de Produto":
                if data_limite:
                    c.execute("""
                        SELECT ic.tipo, COUNT(ic.id) as quantidade, 
                               SUM(ic.valor_total_item) as valor_total, AVG(ic.valor_total_item) as media
                        FROM itens_cotacao ic
                        JOIN cotacoes c ON ic.cotacao_id = c.id
                        WHERE c.status = 'Aprovada' AND c.data_criacao >= ?
                        GROUP BY ic.tipo
                        ORDER BY valor_total DESC
                    """, (data_limite,))
                else:
                    c.execute("""
                        SELECT ic.tipo, COUNT(ic.id) as quantidade, 
                               SUM(ic.valor_total_item) as valor_total, AVG(ic.valor_total_item) as media
                        FROM itens_cotacao ic
                        JOIN cotacoes c ON ic.cotacao_id = c.id
                        WHERE c.status = 'Aprovada'
                        GROUP BY ic.tipo
                        ORDER BY valor_total DESC
                    """)
            else:  # Por Cliente
                if data_limite:
                    c.execute("""
                        SELECT cl.nome, COUNT(c.id) as quantidade, 
                               SUM(c.valor_total) as valor_total, AVG(c.valor_total) as media
                        FROM clientes cl
                        LEFT JOIN cotacoes c ON cl.id = c.cliente_id AND c.data_criacao >= ?
                        WHERE c.status = 'Aprovada'
                        GROUP BY cl.id, cl.nome
                        ORDER BY valor_total DESC
                    """, (data_limite,))
                else:
                    c.execute("""
                        SELECT cl.nome, COUNT(c.id) as quantidade, 
                               SUM(c.valor_total) as valor_total, AVG(c.valor_total) as media
                        FROM clientes cl
                        LEFT JOIN cotacoes c ON cl.id = c.cliente_id
                        WHERE c.status = 'Aprovada'
                        GROUP BY cl.id, cl.nome
                        ORDER BY valor_total DESC
                    """)
            
            for row in c.fetchall():
                categoria, quantidade, valor_total, media = row
                self.faturamento_tree.insert("", "end", values=(
                    categoria or "N/A",
                    quantidade or 0,
                    format_currency(valor_total or 0),
                    format_currency(media or 0)
                ))
                
        except sqlite3.Error as e:
            self.show_error(f"Erro ao consultar: {e}")
        finally:
            conn.close()
            
    def executar_consulta_personalizada(self):
        """Executar consulta SQL personalizada"""
        # Limpar resultados
        for item in self.personalizada_tree.get_children():
            self.personalizada_tree.delete(item)
            
        sql = self.sql_text.get("1.0", tk.END).strip()
        
        if not sql:
            self.show_warning("Digite uma consulta SQL.")
            return
            
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            
            c.execute(sql)
            resultados = c.fetchall()
            
            # Obter nomes das colunas
            colunas = [description[0] for description in c.description]
            
            # Configurar colunas da tree
            self.personalizada_tree["columns"] = colunas
            for col in colunas:
                self.personalizada_tree.heading(col, text=col)
                self.personalizada_tree.column(col, width=150)
            
            # Inserir resultados
            for row in resultados:
                self.personalizada_tree.insert("", "end", values=row)
                
        except sqlite3.Error as e:
            self.show_error(f"Erro na consulta SQL: {e}")
        finally:
            conn.close()
            
    def calcular_data_limite(self, periodo):
        """Calcular data limite baseada no período"""
        hoje = datetime.now()
        
        if periodo == "Últimos 7 dias":
            return (hoje - timedelta(days=7)).strftime('%Y-%m-%d')
        elif periodo == "Últimos 30 dias":
            return (hoje - timedelta(days=30)).strftime('%Y-%m-%d')
        elif periodo == "Últimos 90 dias":
            return (hoje - timedelta(days=90)).strftime('%Y-%m-%d')
        elif periodo == "Este ano":
            return f"{hoje.year}-01-01"
        elif periodo == "Este mês":
            return f"{hoje.year}-{hoje.month:02d}-01"
        elif periodo == "Mês passado":
            mes_passado = hoje.replace(day=1) - timedelta(days=1)
            return f"{mes_passado.year}-{mes_passado.month:02d}-01"
        elif periodo == "Este trimestre":
            trimestre = ((hoje.month - 1) // 3) * 3 + 1
            return f"{hoje.year}-{trimestre:02d}-01"
        else:
            return None
            
    def handle_event(self, event_type, data=None):
        """Manipular eventos do sistema"""
        if event_type == 'usuario_changed':
            self.current_user_id = data