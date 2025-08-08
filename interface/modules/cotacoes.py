import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sqlite3
from datetime import datetime
from .base_module import BaseModule
from database import DB_NAME
from utils.formatters import format_currency, format_date, clean_number
from utils.cotacao_validator import verificar_e_atualizar_status_cotacoes, obter_cotacoes_por_status
from pdf_generators.cotacao_nova import gerar_pdf_cotacao_nova

class CotacoesModule(BaseModule):
    def setup_ui(self):
        # Inicializar variáveis primeiro
        self.current_cotacao_id = None
        self.current_cotacao_itens = []
        
        # Container principal - usando toda a tela
        container = tk.Frame(self.frame, bg='#f8fafc')
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header
        self.create_header(container)
        
        # Layout principal em 2 colunas: esquerda (formulário) e direita (lista)
        main_frame = tk.Frame(container, bg='#f8fafc')
        main_frame.pack(fill="both", expand=True)
        main_frame.grid_columnconfigure(0, weight=1, uniform="cols")
        main_frame.grid_columnconfigure(1, weight=1, uniform="cols")
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Painel de cotação (esquerda)
        form_panel = tk.Frame(main_frame, bg='#f8fafc')
        form_panel.grid(row=0, column=0, sticky="nsew", padx=(10, 10), pady=(10, 10))
        form_panel.grid_columnconfigure(0, weight=1)
        
        # Botões fixos no rodapé do painel de formulário
        self.create_cotacao_buttons(form_panel)
        
        # Área rolável para o conteúdo do formulário
        scroll_container = tk.Frame(form_panel, bg='#f8fafc')
        scroll_container.pack(side="top", fill="both", expand=True)
        
        form_canvas = tk.Canvas(scroll_container, bg='#f8fafc', highlightthickness=0)
        form_scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=form_canvas.yview)
        form_canvas.configure(yscrollcommand=form_scrollbar.set)
        
        form_scrollbar.pack(side="right", fill="y")
        form_canvas.pack(side="left", fill="both", expand=True)
        
        form_inner = tk.Frame(form_canvas, bg='#f8fafc')
        form_window = form_canvas.create_window((0, 0), window=form_inner, anchor="nw")
        
        def _on_inner_configure(event):
            form_canvas.configure(scrollregion=form_canvas.bbox("all"))
        form_inner.bind("<Configure>", _on_inner_configure)
        
        def _on_canvas_configure(event):
            form_canvas.itemconfigure(form_window, width=event.width)
        form_canvas.bind("<Configure>", _on_canvas_configure)
        
        # Suporte a rolagem pelo mouse
        def _on_mousewheel(event):
            delta = 0
            if hasattr(event, 'delta') and event.delta:
                delta = int(-event.delta / 120)
            elif getattr(event, 'num', None) in (4, 5):
                delta = -1 if event.num == 5 else 1
            if delta:
                form_canvas.yview_scroll(delta, "units")
        form_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        form_canvas.bind_all("<Button-4>", _on_mousewheel)
        form_canvas.bind_all("<Button-5>", _on_mousewheel)
        
        # Conteúdo do formulário
        self.create_cotacao_content(form_inner)
        
        # Painel da lista (direita)
        lista_panel = tk.Frame(main_frame, bg='#f8fafc')
        lista_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 10), pady=(10, 10))
        lista_panel.grid_columnconfigure(0, weight=1)
        lista_panel.grid_rowconfigure(2, weight=1)
        
        lista_card = tk.Frame(lista_panel, bg='white', bd=0, relief='ridge', highlightthickness=0)
        lista_card.pack(fill="both", expand=True)
        
        tk.Label(lista_card, text="📋 Lista de Cotações", font=("Arial", 12, "bold"), bg='white', anchor="w").pack(fill="x", padx=12, pady=(12, 8))
        
        lista_inner = tk.Frame(lista_card, bg='white')
        lista_inner.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        
        # Busca
        search_frame, self.search_var = self.create_search_frame(lista_inner, command=self.buscar_cotacoes)
        search_frame.pack(fill="x", pady=(0, 10))
        
        # Reservar rodapé dos botões da lista antes da Treeview
        lista_buttons = tk.Frame(lista_inner, bg='white')
        lista_buttons.pack(side="bottom", fill="x", pady=(10, 0))
        
        # Treeview
        columns = ("numero", "cliente", "data", "valor", "status")
        self.cotacoes_tree = ttk.Treeview(lista_inner, columns=columns, show="headings")
        self.cotacoes_tree.heading("numero", text="Número")
        self.cotacoes_tree.heading("cliente", text="Cliente")
        self.cotacoes_tree.heading("data", text="Data")
        self.cotacoes_tree.heading("valor", text="Valor")
        self.cotacoes_tree.heading("status", text="Status")
        self.cotacoes_tree.column("numero", width=150)
        self.cotacoes_tree.column("cliente", width=250)
        self.cotacoes_tree.column("data", width=100)
        self.cotacoes_tree.column("valor", width=120)
        self.cotacoes_tree.column("status", width=100)
        
        lista_scrollbar = ttk.Scrollbar(lista_inner, orient="vertical", command=self.cotacoes_tree.yview)
        self.cotacoes_tree.configure(yscrollcommand=lista_scrollbar.set)
        
        self.cotacoes_tree.pack(side="left", fill="both", expand=True)
        lista_scrollbar.pack(side="right", fill="y")
        
        # Botões da lista
        editar_btn = self.create_button(lista_buttons, "Editar", self.editar_cotacao)
        editar_btn.pack(side="left", padx=(0, 10))
        
        duplicar_btn = self.create_button(lista_buttons, "Duplicar", self.duplicar_cotacao, bg='#f59e0b')
        duplicar_btn.pack(side="left", padx=(0, 10))
        
        gerar_pdf_lista_btn = self.create_button(lista_buttons, "Gerar PDF", self.gerar_pdf_selecionado, bg='#10b981')
        gerar_pdf_lista_btn.pack(side="right")
        
        # Dados iniciais
        self.refresh_all_data()
        
    def create_header(self, parent):
        header_frame = tk.Frame(parent, bg='#f8fafc')
        header_frame.pack(fill="x", pady=(0, 10))
        
        title_label = tk.Label(header_frame, text="Gestão de Cotações", 
                               font=('Arial', 16, 'bold'),
                               bg='#f8fafc',
                               fg='#1e293b')
        title_label.pack(side="left")
        
    # Estrutura antiga baseada em notebook removida; conteúdo agora no layout único
    def create_cotacao_content(self, parent):
        # Frame principal com grid 2 colunas, 100% da tela
        main_grid = tk.Frame(parent, bg='white')
        main_grid.pack(fill="both", expand=True)

        # 2 colunas, 2 linhas
        main_grid.grid_columnconfigure(0, weight=1, uniform="col")
        main_grid.grid_columnconfigure(1, weight=1, uniform="col")
        main_grid.grid_rowconfigure(0, weight=1, uniform="row")
        main_grid.grid_rowconfigure(1, weight=1, uniform="row")

        # Coluna 0: Dados + Itens (stacked)
        dados_frame = tk.Frame(main_grid, bg='white', relief='groove', bd=2)
        dados_frame.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        self.create_dados_cotacao_section(dados_frame)
        itens_frame = tk.Frame(main_grid, bg='white', relief='groove', bd=2)
        itens_frame.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        self.create_itens_cotacao_section(itens_frame)

        # Coluna 1 removida (dashboard)

        # Botões de ação abaixo do grid
        self.create_cotacao_buttons(parent)
        
    def create_dados_cotacao_section(self, parent):
        section_frame = self.create_section_frame(parent, "Dados da Cotação")
        section_frame.pack(fill="x", pady=(0, 10))
        
        # Grid de campos
        fields_frame = tk.Frame(section_frame, bg='white')
        fields_frame.pack(fill="x")
        
        # Variáveis
        self.numero_var = tk.StringVar()
        self.cliente_var = tk.StringVar()
        self.filial_var = tk.StringVar(value="2")  # Default para World Comp do Brasil
        self.modelo_var = tk.StringVar()
        self.serie_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Em Aberto")
        self.data_validade_var = tk.StringVar()
        self.condicao_pagamento_var = tk.StringVar()
        self.prazo_entrega_var = tk.StringVar()
        self.observacoes_var = tk.StringVar()
        
        row = 0
        
        # Número da Proposta
        tk.Label(fields_frame, text="Número da Proposta *:", 
                 font=('Arial', 10, 'bold'), bg='white').grid(row=row, column=0, sticky="w", pady=5)
        tk.Entry(fields_frame, textvariable=self.numero_var, 
                 font=('Arial', 10), width=30).grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        row += 1
        
        # Filial
        tk.Label(fields_frame, text="Filial *:", 
                 font=('Arial', 10, 'bold'), bg='white').grid(row=row, column=0, sticky="w", pady=5)
        filial_combo = ttk.Combobox(fields_frame, textvariable=self.filial_var, 
                                   values=["1 - WORLD COMP COMPRESSORES LTDA", 
                                          "2 - WORLD COMP DO BRASIL COMPRESSORES LTDA"], 
                                   width=45, state="readonly")
        filial_combo.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        row += 1
        
        # Cliente com busca reativa
        tk.Label(fields_frame, text="Cliente *:", 
                 font=('Arial', 10, 'bold'), bg='white').grid(row=row, column=0, sticky="w", pady=5)
        
        cliente_frame = tk.Frame(fields_frame, bg='white')
        cliente_frame.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        
        self.cliente_combo = ttk.Combobox(cliente_frame, textvariable=self.cliente_var, width=25)
        self.cliente_combo.pack(side="left", fill="x", expand=True)
        self.cliente_combo.bind("<<ComboboxSelected>>", self.on_cliente_selected)
        
        # Botão para buscar/atualizar clientes
        refresh_clientes_btn = self.create_button(cliente_frame, "🔄", self.refresh_clientes, bg='#10b981')
        refresh_clientes_btn.pack(side="right", padx=(5, 0))
        
        row += 1
        
        # Modelo e Série
        tk.Label(fields_frame, text="Modelo do Compressor:", 
                 font=('Arial', 10, 'bold'), bg='white').grid(row=row, column=0, sticky="w", pady=5)
        tk.Entry(fields_frame, textvariable=self.modelo_var, 
                 font=('Arial', 10), width=30).grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        row += 1
        
        tk.Label(fields_frame, text="Número de Série:", 
                 font=('Arial', 10, 'bold'), bg='white').grid(row=row, column=0, sticky="w", pady=5)
        tk.Entry(fields_frame, textvariable=self.serie_var, 
                 font=('Arial', 10), width=30).grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        row += 1
        
        # Status
        tk.Label(fields_frame, text="Status:", 
                 font=('Arial', 10, 'bold'), bg='white').grid(row=row, column=0, sticky="w", pady=5)
        status_combo = ttk.Combobox(fields_frame, textvariable=self.status_var, 
                                   values=["Em Aberto", "Aprovada", "Rejeitada"], 
                                   width=27, state="readonly")
        status_combo.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        row += 1
        
        # Data de Validade
        tk.Label(fields_frame, text="Data de Validade:", 
                 font=('Arial', 10, 'bold'), bg='white').grid(row=row, column=0, sticky="w", pady=5)
        tk.Entry(fields_frame, textvariable=self.data_validade_var, 
                 font=('Arial', 10), width=30).grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        row += 1
        
        # Condição de Pagamento
        tk.Label(fields_frame, text="Condição de Pagamento:", 
                 font=('Arial', 10, 'bold'), bg='white').grid(row=row, column=0, sticky="w", pady=5)
        tk.Entry(fields_frame, textvariable=self.condicao_pagamento_var, 
                 font=('Arial', 10), width=30).grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        row += 1
        
        # Prazo de Entrega
        tk.Label(fields_frame, text="Prazo de Entrega:", 
                 font=('Arial', 10, 'bold'), bg='white').grid(row=row, column=0, sticky="w", pady=5)
        tk.Entry(fields_frame, textvariable=self.prazo_entrega_var, 
                 font=('Arial', 10), width=30).grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        row += 1
        
        # Observações
        tk.Label(fields_frame, text="Observações:", 
                 font=('Arial', 10, 'bold'), bg='white').grid(row=row, column=0, sticky="nw", pady=5)
        self.observacoes_text = scrolledtext.ScrolledText(fields_frame, height=3, width=30)
        self.observacoes_text.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        
        fields_frame.grid_columnconfigure(1, weight=1)
        
        # Seção: Esboço do Serviço
        self.create_esboco_servico_section(parent)
        
        # Seção: Relação de Peças
        self.create_relacao_pecas_section(parent)
        
        # Configurar colunas
        fields_frame.grid_columnconfigure(1, weight=1)
        
    # Dashboards removidos deste módulo

    def create_esboco_servico_section(self, parent):
        """Criar seção para esboço do serviço"""
        section_frame = self.create_section_frame(parent, "Esboço do Serviço a Ser Executado")
        section_frame.pack(fill="x", pady=(0, 15))
        
        # Variáveis
        self.esboco_servico_var = tk.StringVar()
        
        # Text area para esboço do serviço
        self.esboco_servico_text = scrolledtext.ScrolledText(section_frame, height=6, width=80, wrap=tk.WORD)
        self.esboco_servico_text.pack(fill="both", expand=True, padx=10, pady=10)
        
    def create_relacao_pecas_section(self, parent):
        """Criar seção para relação de peças a serem substituídas"""
        section_frame = self.create_section_frame(parent, "Relação de Peças a Serem Substituídas")
        section_frame.pack(fill="x", pady=(0, 15))
        
        # Variáveis
        self.relacao_pecas_var = tk.StringVar()
        
        # Text area para relação de peças
        self.relacao_pecas_text = scrolledtext.ScrolledText(section_frame, height=6, width=80, wrap=tk.WORD)
        self.relacao_pecas_text.pack(fill="both", expand=True, padx=10, pady=10)
        
    def create_itens_cotacao_section(self, parent):
        section_frame = self.create_section_frame(parent, "Itens da Cotação")
        section_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Frame para adicionar item
        add_item_frame = tk.Frame(section_frame, bg='white')
        add_item_frame.pack(fill="x", pady=(0, 10))
        
        # Campos para novo item
        self.create_item_fields(add_item_frame)
        
        # Lista de itens
        self.create_itens_list(section_frame)
        
    def create_item_fields(self, parent):
        # Variáveis
        self.item_tipo_var = tk.StringVar()
        self.item_nome_var = tk.StringVar()
        self.item_qtd_var = tk.StringVar(value="1")
        self.item_valor_var = tk.StringVar(value="0.00")
        self.item_desc_var = tk.StringVar()
        self.item_mao_obra_var = tk.StringVar(value="0.00")
        self.item_deslocamento_var = tk.StringVar(value="0.00")
        self.item_estadia_var = tk.StringVar(value="0.00")
        self.item_tipo_operacao_var = tk.StringVar(value="Compra")
        
        # Grid de campos
        fields_grid = tk.Frame(parent, bg="white")
        fields_grid.pack(padx=10, pady=(0, 10), fill="x")
        
        # Primeira linha
        tk.Label(fields_grid, text="Tipo:", font=("Arial", 10, "bold"), bg="white").grid(row=0, column=0, padx=5, sticky="w")
        self.tipo_combo = ttk.Combobox(fields_grid, textvariable=self.item_tipo_var, 
                                      values=["Produto", "Serviço", "Kit"], 
                                      width=10, state="readonly")
        self.tipo_combo.grid(row=0, column=1, padx=5)
        self.tipo_combo.bind("<<ComboboxSelected>>", self.on_tipo_changed)
        
        tk.Label(fields_grid, text="Nome:", font=("Arial", 10, "bold"), bg="white").grid(row=0, column=2, padx=5, sticky="w")
        
        # Frame para nome do item com botão de refresh
        nome_frame = tk.Frame(fields_grid, bg='white')
        nome_frame.grid(row=0, column=3, padx=5, sticky="ew")
        
        self.item_nome_combo = ttk.Combobox(nome_frame, textvariable=self.item_nome_var, width=20)
        self.item_nome_combo.pack(side="left", fill="x", expand=True)
        self.item_nome_combo.bind("<<ComboboxSelected>>", self.on_item_selected)
        
        refresh_produtos_btn = self.create_button(nome_frame, "🔄", self.refresh_produtos, bg='#10b981')
        refresh_produtos_btn.pack(side="right", padx=(2, 0))
        
        tk.Label(fields_grid, text="Qtd:", font=("Arial", 10, "bold"), bg="white").grid(row=0, column=4, padx=5, sticky="w")
        tk.Entry(fields_grid, textvariable=self.item_qtd_var, width=5).grid(row=0, column=5, padx=5)
        
        tk.Label(fields_grid, text="Valor Unit.:", font=("Arial", 10, "bold"), bg="white").grid(row=0, column=6, padx=5, sticky="w")
        tk.Entry(fields_grid, textvariable=self.item_valor_var, width=10).grid(row=0, column=7, padx=5)
        
        tk.Label(fields_grid, text="Tipo:", font=("Arial", 10, "bold"), bg="white").grid(row=0, column=8, padx=5, sticky="w")
        tipo_operacao_combo = ttk.Combobox(fields_grid, textvariable=self.item_tipo_operacao_var, 
                                          values=["Compra", "Locação"], 
                                          width=8, state="readonly")
        tipo_operacao_combo.grid(row=0, column=9, padx=5)
        
        # Segunda linha - Descrição
        tk.Label(fields_grid, text="Descrição:", font=("Arial", 10, "bold"), bg="white").grid(row=1, column=0, padx=5, sticky="w")
        tk.Entry(fields_grid, textvariable=self.item_desc_var, width=50).grid(row=1, column=1, columnspan=4, padx=5, sticky="ew")
        
        # Terceira linha - Campos de serviço (inicialmente ocultos)
        self.servico_frame = tk.Frame(fields_grid, bg="white")
        self.servico_frame.grid(row=2, column=0, columnspan=8, sticky="ew", pady=5)
        
        tk.Label(self.servico_frame, text="Mão de Obra:", font=("Arial", 10, "bold"), bg="white").grid(row=0, column=0, padx=5, sticky="w")
        tk.Entry(self.servico_frame, textvariable=self.item_mao_obra_var, width=10).grid(row=0, column=1, padx=5)
        
        tk.Label(self.servico_frame, text="Deslocamento:", font=("Arial", 10, "bold"), bg="white").grid(row=0, column=2, padx=5, sticky="w")
        tk.Entry(self.servico_frame, textvariable=self.item_deslocamento_var, width=10).grid(row=0, column=3, padx=5)
        
        tk.Label(self.servico_frame, text="Estadia:", font=("Arial", 10, "bold"), bg="white").grid(row=0, column=4, padx=5, sticky="w")
        tk.Entry(self.servico_frame, textvariable=self.item_estadia_var, width=10).grid(row=0, column=5, padx=5)
        
        # Inicialmente ocultar campos de serviço
        self.servico_frame.grid_remove()
        
        # Botão adicionar
        adicionar_button = self.create_button(fields_grid, "Adicionar Item", self.adicionar_item)
        adicionar_button.grid(row=3, column=0, columnspan=8, pady=10)
        
        # Configurar grid
        fields_grid.grid_columnconfigure(3, weight=1)
        
    def on_tipo_changed(self, event=None):
        """Callback quando o tipo do item muda"""
        tipo = self.item_tipo_var.get()
        
        # Mostrar/ocultar campos de serviço
        if tipo == "Serviço":
            self.servico_frame.grid()
        else:
            self.servico_frame.grid_remove()
            # Resetar valores de serviço
            self.item_mao_obra_var.set("0.00")
            self.item_deslocamento_var.set("0.00")
            self.item_estadia_var.set("0.00")
        
        # Atualizar lista de produtos
        self.update_produtos_combo()
        
    def update_produtos_combo(self):
        """Atualizar combo de produtos baseado no tipo selecionado"""
        tipo = self.item_tipo_var.get()
        if not tipo:
            self.item_nome_combo['values'] = []
            return
            
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        try:
            c.execute("SELECT nome FROM produtos WHERE tipo = ? AND ativo = 1 ORDER BY nome", (tipo,))
            produtos = [row[0] for row in c.fetchall()]
            self.item_nome_combo['values'] = produtos
            self.item_nome_var.set("")  # Limpar seleção
        except sqlite3.Error as e:
            self.show_error(f"Erro ao carregar produtos: {e}")
        finally:
            conn.close()
            
    def on_item_selected(self, event=None):
        """Callback quando um produto é selecionado"""
        nome = self.item_nome_var.get()
        tipo = self.item_tipo_var.get()
        
        if not nome or not tipo:
            return
            
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        try:
            c.execute("SELECT valor_unitario, descricao FROM produtos WHERE nome = ? AND tipo = ?", (nome, tipo))
            result = c.fetchone()
            if result:
                valor, descricao = result
                self.item_valor_var.set(f"{valor:.2f}")
                if descricao:
                    self.item_desc_var.set(descricao)
        except sqlite3.Error as e:
            self.show_error(f"Erro ao buscar dados do produto: {e}")
        finally:
            conn.close()
            
    def create_itens_list(self, parent):
        # Frame para lista
        list_frame = tk.Frame(parent, bg='white')
        list_frame.pack(fill="both", expand=True)
        
        # Treeview
        columns = ("tipo", "nome", "qtd", "valor_unit", "mao_obra", "deslocamento", "estadia", "valor_total", "descricao")
        self.itens_tree = ttk.Treeview(list_frame, 
                                      columns=columns,
                                      show="headings",
                                      height=8)
        
        # Cabeçalhos
        self.itens_tree.heading("tipo", text="Tipo")
        self.itens_tree.heading("nome", text="Nome")
        self.itens_tree.heading("qtd", text="Qtd")
        self.itens_tree.heading("valor_unit", text="Valor Unit.")
        self.itens_tree.heading("mao_obra", text="Mão Obra")
        self.itens_tree.heading("deslocamento", text="Desloc.")
        self.itens_tree.heading("estadia", text="Estadia")
        self.itens_tree.heading("valor_total", text="Total")
        self.itens_tree.heading("descricao", text="Descrição")
        
        # Larguras
        self.itens_tree.column("tipo", width=80)
        self.itens_tree.column("nome", width=150)
        self.itens_tree.column("qtd", width=50)
        self.itens_tree.column("valor_unit", width=80)
        self.itens_tree.column("mao_obra", width=80)
        self.itens_tree.column("deslocamento", width=80)
        self.itens_tree.column("estadia", width=80)
        self.itens_tree.column("valor_total", width=80)
        self.itens_tree.column("descricao", width=200)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", 
                                 command=self.itens_tree.yview)
        self.itens_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        self.itens_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Botões para itens
        item_buttons = tk.Frame(parent, bg='white')
        item_buttons.pack(fill="x", pady=(10, 0))
        
        remove_btn = self.create_button(item_buttons, "Remover Item", self.remover_item, bg='#dc2626')
        remove_btn.pack(side="left", padx=5)
        
        # Label do total
        self.total_label = tk.Label(item_buttons, text="Total: R$ 0,00",
                                   font=('Arial', 12, 'bold'),
                                   bg='white',
                                   fg='#1e293b')
        self.total_label.pack(side="right")
        
    def create_cotacao_buttons(self, parent):
        buttons_frame = tk.Frame(parent, bg='white')
        buttons_frame.pack(fill="x", pady=(20, 0))
        
        # Botões
        nova_btn = self.create_button(buttons_frame, "Nova Cotação", self.nova_cotacao, bg='#e2e8f0', fg='#475569')
        nova_btn.pack(side="left", padx=(0, 10))
        
        salvar_btn = self.create_button(buttons_frame, "Salvar Cotação", self.salvar_cotacao)
        salvar_btn.pack(side="left", padx=(0, 10))
        
        gerar_pdf_btn = self.create_button(buttons_frame, "Gerar PDF", self.gerar_pdf, bg='#10b981')
        gerar_pdf_btn.pack(side="right")
        
    # Lista de cotações integrada no layout único
    def refresh_all_data(self):
        """Atualizar todos os dados do módulo"""
        self.refresh_clientes()
        self.refresh_produtos()
        self.carregar_cotacoes()
        
    def refresh_clientes(self):
        """Atualizar lista de clientes"""
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        try:
            c.execute("SELECT id, nome FROM clientes ORDER BY nome")
            clientes = c.fetchall()
            
            self.clientes_dict = {f"{nome} (ID: {id})": id for id, nome in clientes}
            cliente_values = list(self.clientes_dict.keys())
            
            self.cliente_combo['values'] = cliente_values
            
            print(f"Clientes carregados: {len(cliente_values)}")  # Debug
            
        except sqlite3.Error as e:
            self.show_error(f"Erro ao carregar clientes: {e}")
        finally:
            conn.close()
            
    def refresh_produtos(self):
        """Atualizar lista de produtos"""
        # Atualizar combo baseado no tipo selecionado
        self.update_produtos_combo()
        print("Produtos atualizados")  # Debug
        
    def on_cliente_selected(self, event=None):
        """Preencher automaticamente a condição de pagamento baseada no cliente selecionado"""
        cliente_str = self.cliente_var.get()
        if not cliente_str:
            return
            
        # Obter ID do cliente
        cliente_id = self.clientes_dict.get(cliente_str)
        if not cliente_id:
            return
            
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            
            # Buscar prazo de pagamento do cliente
            c.execute("SELECT prazo_pagamento FROM clientes WHERE id = ?", (cliente_id,))
            result = c.fetchone()
            
            if result and result[0]:
                # Preencher automaticamente a condição de pagamento
                self.condicao_pagamento_var.set(result[0])
                
        except sqlite3.Error as e:
            print(f"Erro ao buscar prazo de pagamento do cliente: {e}")
        finally:
            conn.close()
            
    def gerar_numero_sequencial(self):
        """Gerar número sequencial para cotação"""
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            
            # Buscar o maior número sequencial existente
            c.execute("SELECT MAX(CAST(SUBSTR(numero_proposta, 6) AS INTEGER)) FROM cotacoes WHERE numero_proposta LIKE 'PROP-%'")
            result = c.fetchone()
            
            if result and result[0]:
                proximo_numero = result[0] + 1
            else:
                proximo_numero = 1
                
            return f"PROP-{proximo_numero:06d}"
            
        except sqlite3.Error as e:
            print(f"Erro ao gerar número sequencial: {e}")
            # Fallback para timestamp
            return f"PROP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        finally:
            conn.close()
        
    def adicionar_item(self):
        tipo = self.item_tipo_var.get()
        nome = self.item_nome_var.get()
        qtd_str = self.item_qtd_var.get()
        valor_str = self.item_valor_var.get()
        descricao = self.item_desc_var.get()
        mao_obra_str = self.item_mao_obra_var.get()
        deslocamento_str = self.item_deslocamento_var.get()
        estadia_str = self.item_estadia_var.get()
        tipo_operacao = self.item_tipo_operacao_var.get()
        
        # Validações
        if not tipo or not nome:
            self.show_warning("Selecione o tipo e nome do item.")
            return
            
        try:
            quantidade = float(qtd_str) if qtd_str else 1
            valor_unitario = clean_number(valor_str)
            mao_obra = clean_number(mao_obra_str)
            deslocamento = clean_number(deslocamento_str)
            estadia = clean_number(estadia_str)
            
            valor_total = quantidade * (valor_unitario + mao_obra + deslocamento + estadia)
        except ValueError:
            self.show_error("Verifique os valores numéricos informados.")
            return
            
        # Adicionar à lista
        self.itens_tree.insert("", "end", values=(
            tipo,
            nome,
            f"{quantidade:.2f}",
            format_currency(valor_unitario),
            format_currency(mao_obra),
            format_currency(deslocamento),
            format_currency(estadia),
            format_currency(valor_total),
            tipo_operacao,
            descricao
        ))
        
        # Limpar campos
        self.item_nome_var.set("")
        self.item_desc_var.set("")
        self.item_qtd_var.set("1")
        self.item_valor_var.set("0.00")
        self.item_mao_obra_var.set("0.00")
        self.item_deslocamento_var.set("0.00")
        self.item_estadia_var.set("0.00")
        self.item_tipo_operacao_var.set("Compra")
        
        # Atualizar total
        self.atualizar_total()
        
    def remover_item(self):
        selected = self.itens_tree.selection()
        if not selected:
            self.show_warning("Selecione um item para remover.")
            return
            
        for item in selected:
            self.itens_tree.delete(item)
            
        self.atualizar_total()
        
    def atualizar_total(self):
        """Atualizar valor total da cotação"""
        total = 0
        for item in self.itens_tree.get_children():
            values = self.itens_tree.item(item)['values']
            if len(values) >= 8:
                # Remover formatação e converter para float
                valor_total_str = values[7].replace('R$ ', '').replace('.', '').replace(',', '.')
                try:
                    total += float(valor_total_str)
                except ValueError:
                    pass
                    
        self.total_label.config(text=f"Total: {format_currency(total)}")
        
    def nova_cotacao(self):
        """Limpar formulário para nova cotação"""
        self.current_cotacao_id = None
        
        # Limpar campos
        self.numero_var.set("")
        self.cliente_var.set("")
        self.modelo_var.set("")
        self.serie_var.set("")
        self.status_var.set("Em Aberto")
        self.data_validade_var.set("")
        self.condicao_pagamento_var.set("")
        self.prazo_entrega_var.set("")
        self.observacoes_text.delete("1.0", tk.END)
        self.esboco_servico_text.delete("1.0", tk.END)
        self.relacao_pecas_text.delete("1.0", tk.END)
        
        # Limpar itens
        for item in self.itens_tree.get_children():
            self.itens_tree.delete(item)
            
        self.atualizar_total()
        
        # Gerar número sequencial automático
        numero = self.gerar_numero_sequencial()
        self.numero_var.set(numero)
        
    def salvar_cotacao(self):
        """Salvar cotação no banco de dados"""
        # Validações
        numero = self.numero_var.get().strip()
        cliente_str = self.cliente_var.get().strip()
        
        if not numero:
            self.show_warning("Informe o número da proposta.")
            return
            
        if not cliente_str:
            self.show_warning("Selecione um cliente.")
            return
            
        # Obter ID do cliente
        cliente_id = self.clientes_dict.get(cliente_str)
        if not cliente_id:
            self.show_warning("Cliente selecionado inválido.")
            return
            
        # Verificar se há itens
        if not self.itens_tree.get_children():
            self.show_warning("Adicione pelo menos um item à cotação.")
            return
            
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        try:
            # Calcular valor total
            valor_total = 0
            for item in self.itens_tree.get_children():
                values = self.itens_tree.item(item)['values']
                if len(values) >= 8:
                    valor_total_str = values[7].replace('R$ ', '').replace('.', '').replace(',', '.')
                    try:
                        valor_total += float(valor_total_str)
                    except ValueError:
                        pass
            
            # Obter ID da filial
            filial_str = self.filial_var.get()
            filial_id = int(filial_str.split(' - ')[0]) if ' - ' in filial_str else int(filial_str)
            
            # Dados da cotação
            if self.current_cotacao_id:
                # Atualizar cotação existente
                c.execute("""
                    UPDATE cotacoes SET
                        numero_proposta = ?, modelo_compressor = ?, numero_serie_compressor = ?,
                        observacoes = ?, valor_total = ?, status = ?, data_validade = ?,
                        condicao_pagamento = ?, prazo_entrega = ?, filial_id = ?,
                        esboco_servico = ?, relacao_pecas_substituir = ?
                    WHERE id = ?
                """, (numero, self.modelo_var.get(), self.serie_var.get(),
                     self.observacoes_text.get("1.0", tk.END).strip(), valor_total,
                     self.status_var.get(), self.data_validade_var.get(),
                     self.condicao_pagamento_var.get(), self.prazo_entrega_var.get(),
                     filial_id, 
                     self.esboco_servico_text.get("1.0", tk.END).strip(),
                     self.relacao_pecas_text.get("1.0", tk.END).strip(),
                     self.current_cotacao_id))
                
                # Remover itens antigos
                c.execute("DELETE FROM itens_cotacao WHERE cotacao_id = ?", (self.current_cotacao_id,))
                cotacao_id = self.current_cotacao_id
            else:
                # Inserir nova cotação
                c.execute("""
                    INSERT INTO cotacoes (numero_proposta, cliente_id, responsavel_id, data_criacao,
                                        modelo_compressor, numero_serie_compressor, observacoes,
                                        valor_total, status, data_validade, condicao_pagamento,
                                        prazo_entrega, filial_id, esboco_servico, relacao_pecas_substituir)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (numero, cliente_id, self.user_id, datetime.now().strftime('%Y-%m-%d'),
                     self.modelo_var.get(), self.serie_var.get(),
                     self.observacoes_text.get("1.0", tk.END).strip(), valor_total,
                     self.status_var.get(), self.data_validade_var.get(),
                     self.condicao_pagamento_var.get(), self.prazo_entrega_var.get(),
                     filial_id,
                     self.esboco_servico_text.get("1.0", tk.END).strip(),
                     self.relacao_pecas_text.get("1.0", tk.END).strip()))
                     
                cotacao_id = c.lastrowid
                self.current_cotacao_id = cotacao_id
            
            # Inserir itens
            for item in self.itens_tree.get_children():
                values = self.itens_tree.item(item)['values']
                tipo, nome, qtd, valor_unit, mao_obra, desloc, estadia, total, tipo_operacao, desc = values
                
                # Converter valores
                quantidade = float(qtd)
                valor_unitario = clean_number(valor_unit)
                valor_mao_obra = clean_number(mao_obra)
                valor_desloc = clean_number(desloc)
                valor_estadia = clean_number(estadia)
                valor_total_item = clean_number(total)
                
                c.execute("""
                    INSERT INTO itens_cotacao (cotacao_id, tipo, item_nome, quantidade,
                                             valor_unitario, valor_total_item, descricao,
                                             mao_obra, deslocamento, estadia, tipo_operacao)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (cotacao_id, tipo, nome, quantidade, valor_unitario,
                     valor_total_item, desc, valor_mao_obra, valor_desloc, valor_estadia, tipo_operacao))
            
            conn.commit()
            self.show_success("Cotação salva com sucesso!")
            
            # Emitir evento para atualizar outros módulos
            self.emit_event('cotacao_created')
            
            # Recarregar lista
            self.carregar_cotacoes()
            
        except sqlite3.Error as e:
            self.show_error(f"Erro ao salvar cotação: {e}")
        finally:
            conn.close()
            
    def gerar_pdf(self):
        """Gerar PDF da cotação atual"""
        if not self.current_cotacao_id:
            self.show_warning("Salve a cotação antes de gerar o PDF.")
            return
            
        # Obter username do usuário atual para template personalizado
        current_username = self._get_current_username()
        
        sucesso, resultado = gerar_pdf_cotacao_nova(self.current_cotacao_id, DB_NAME, current_username)
        
        if sucesso:
            self.show_success(f"PDF gerado com sucesso!\nLocal: {resultado}")
        else:
            self.show_error(f"Erro ao gerar PDF: {resultado}")
            
    def _get_current_username(self):
        """Obter o username do usuário atual"""
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT username FROM usuarios WHERE id = ?", (self.user_id,))
            result = c.fetchone()
            return result[0] if result else None
        except:
            return None
        finally:
            if 'conn' in locals():
                conn.close()
            
    def carregar_cotacoes(self):
        """Carregar lista de cotações"""
        # Verificar e atualizar cotações expiradas automaticamente
        cotações_expiradas = verificar_e_atualizar_status_cotacoes()
        
        # Limpar lista atual
        for item in self.cotacoes_tree.get_children():
            self.cotacoes_tree.delete(item)
            
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        try:
            c.execute("""
                SELECT c.id, c.numero_proposta, cl.nome, c.data_criacao, c.valor_total, c.status
                FROM cotacoes c
                JOIN clientes cl ON c.cliente_id = cl.id
                ORDER BY c.created_at DESC
            """)
            
            for row in c.fetchall():
                cotacao_id, numero, cliente, data, valor, status = row
                self.cotacoes_tree.insert("", "end", values=(
                    numero,
                    cliente,
                    format_date(data),
                    format_currency(valor) if valor else "R$ 0,00",
                    status
                ), tags=(cotacao_id,))
                
        except sqlite3.Error as e:
            self.show_error(f"Erro ao carregar cotações: {e}")
        finally:
            conn.close()
            
    def buscar_cotacoes(self):
        """Buscar cotações com filtro"""
        termo = self.search_var.get().strip()
        
        # Limpar lista atual
        for item in self.cotacoes_tree.get_children():
            self.cotacoes_tree.delete(item)
            
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        try:
            if termo:
                c.execute("""
                    SELECT c.id, c.numero_proposta, cl.nome, c.data_criacao, c.valor_total, c.status
                    FROM cotacoes c
                    JOIN clientes cl ON c.cliente_id = cl.id
                    WHERE c.numero_proposta LIKE ? OR cl.nome LIKE ?
                    ORDER BY c.created_at DESC
                """, (f"%{termo}%", f"%{termo}%"))
            else:
                c.execute("""
                    SELECT c.id, c.numero_proposta, cl.nome, c.data_criacao, c.valor_total, c.status
                    FROM cotacoes c
                    JOIN clientes cl ON c.cliente_id = cl.id
                    ORDER BY c.created_at DESC
                """)
            
            for row in c.fetchall():
                cotacao_id, numero, cliente, data, valor, status = row
                self.cotacoes_tree.insert("", "end", values=(
                    numero,
                    cliente,
                    format_date(data),
                    format_currency(valor) if valor else "R$ 0,00",
                    status
                ), tags=(cotacao_id,))
                
        except sqlite3.Error as e:
            self.show_error(f"Erro ao buscar cotações: {e}")
        finally:
            conn.close()
            
    def editar_cotacao(self):
        """Editar cotação selecionada"""
        selected = self.cotacoes_tree.selection()
        if not selected:
            self.show_warning("Selecione uma cotação para editar.")
            return
            
        # Obter ID da cotação
        tags = self.cotacoes_tree.item(selected[0])['tags']
        if not tags:
            return
            
        cotacao_id = tags[0]
        self.carregar_cotacao_para_edicao(cotacao_id)
        
        # Layout único: permanecer na mesma tela
        
    def carregar_cotacao_para_edicao(self, cotacao_id):
        """Carregar dados da cotação para edição"""
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        try:
            # Carregar dados da cotação
            c.execute("""
                SELECT c.*, cl.nome
                FROM cotacoes c
                JOIN clientes cl ON c.cliente_id = cl.id
                WHERE c.id = ?
            """, (cotacao_id,))
            
            cotacao = c.fetchone()
            if not cotacao:
                self.show_error("Cotação não encontrada.")
                return
                
            # Preencher campos
            self.current_cotacao_id = cotacao_id
            self.numero_var.set(cotacao[1])  # numero_proposta
            
            # Encontrar cliente no combo
            cliente_nome = cotacao[17]  # nome do cliente
            for key, value in self.clientes_dict.items():
                if value == cotacao[2]:  # cliente_id
                    self.cliente_var.set(key)
                    break
                    
            self.modelo_var.set(cotacao[6] or "")
            self.serie_var.set(cotacao[7] or "")
            self.status_var.set(cotacao[15] or "Em Aberto")
            self.data_validade_var.set(cotacao[5] or "")
            self.condicao_pagamento_var.set(cotacao[12] or "")
            self.prazo_entrega_var.set(cotacao[13] or "")
            
            # Observações
            self.observacoes_text.delete("1.0", tk.END)
            if cotacao[9]:  # observacoes
                self.observacoes_text.insert("1.0", cotacao[9])
            
            # Carregar itens
            self.carregar_itens_cotacao(cotacao_id)
            
        except sqlite3.Error as e:
            self.show_error(f"Erro ao carregar cotação: {e}")
        finally:
            conn.close()
            
    def carregar_itens_cotacao(self, cotacao_id):
        """Carregar itens da cotação"""
        # Limpar lista atual
        for item in self.itens_tree.get_children():
            self.itens_tree.delete(item)
            
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        try:
            c.execute("""
                SELECT tipo, item_nome, quantidade, valor_unitario, valor_total_item,
                       descricao, mao_obra, deslocamento, estadia
                FROM itens_cotacao
                WHERE cotacao_id = ?
                ORDER BY id
            """, (cotacao_id,))
            
            for row in c.fetchall():
                tipo, nome, qtd, valor_unit, total, desc, mao_obra, desloc, estadia = row
                self.itens_tree.insert("", "end", values=(
                    tipo,
                    nome,
                    f"{qtd:.2f}",
                    format_currency(valor_unit),
                    format_currency(mao_obra or 0),
                    format_currency(desloc or 0),
                    format_currency(estadia or 0),
                    format_currency(total),
                    desc or ""
                ))
                
            self.atualizar_total()
            
        except sqlite3.Error as e:
            self.show_error(f"Erro ao carregar itens: {e}")
        finally:
            conn.close()
            
    def duplicar_cotacao(self):
        """Duplicar cotação selecionada"""
        selected = self.cotacoes_tree.selection()
        if not selected:
            self.show_warning("Selecione uma cotação para duplicar.")
            return
            
        # Obter ID da cotação
        tags = self.cotacoes_tree.item(selected[0])['tags']
        if not tags:
            return
            
        cotacao_id = tags[0]
        self.carregar_cotacao_para_edicao(cotacao_id)
        
        # Limpar ID e gerar novo número
        self.current_cotacao_id = None
        numero = f"PROP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.numero_var.set(numero)
        
        # Layout único: permanecer na mesma tela
        
    def gerar_pdf_selecionado(self):
        """Gerar PDF da cotação selecionada"""
        selected = self.cotacoes_tree.selection()
        if not selected:
            self.show_warning("Selecione uma cotação para gerar PDF.")
            return
            
        # Obter ID da cotação
        tags = self.cotacoes_tree.item(selected[0])['tags']
        if not tags:
            return
            
        cotacao_id = tags[0]
        # Obter username do usuário atual para template personalizado
        current_username = self._get_current_username()
        sucesso, resultado = gerar_pdf_cotacao_nova(cotacao_id, DB_NAME, current_username)
        
        if sucesso:
            self.show_success(f"PDF gerado com sucesso!\nLocal: {resultado}")
        else:
            self.show_error(f"Erro ao gerar PDF: {resultado}")
            
    def handle_event(self, event_type, data=None):
        """Manipular eventos do sistema"""
        if event_type == 'cliente_created':
            self.refresh_clientes()
            print("Lista de clientes atualizada automaticamente!")
        elif event_type == 'produto_created':
            self.refresh_produtos()
            print("Lista de produtos atualizada automaticamente!")