import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from .base_module import BaseModule
from database import DB_NAME
import os
from openpyxl import Workbook

DATE_FMT = "%Y-%m-%d"

class ConsultasModule(BaseModule):
    def setup_ui(self):
        container = tk.Frame(self.frame, bg='#f8fafc')
        container.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.create_header(container)
        
        # Área rolável vertical
        scroll_container = tk.Frame(container, bg='#f8fafc')
        scroll_container.pack(fill='both', expand=True)
        canvas = tk.Canvas(scroll_container, bg='#f8fafc', highlightthickness=0)
        vbar = ttk.Scrollbar(scroll_container, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=vbar.set)
        vbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)
        self.inner = tk.Frame(canvas, bg='#f8fafc')
        window = canvas.create_window((0, 0), window=self.inner, anchor='nw')
        self.inner.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>', lambda e: canvas.itemconfigure(window, width=e.width))
        
        # Builder
        self.create_new_builder(self.inner)
        
        self.selected_fields = {
            'Clientes': set(),
            'Produtos': set(),
            'Cotações': set(),
            'Relatórios': set(),
            'Usuários': set()
        }
        self.results_columns = []
        self.results_rows = []
    
    def create_header(self, parent):
        header = tk.Frame(parent, bg='#f8fafc')
        header.pack(fill='x', pady=(0, 12))
        tk.Label(header, text='Consultas', font=('Arial', 16, 'bold'), background='#f8fafc', foreground='#1e293b').pack(side='left')
    
    def create_new_builder(self, parent):
        self.builder = tk.Frame(parent, bg='white', padx=12, pady=12)
        self.builder.pack(fill='both', expand=True)
        self._create_builder_content(self.builder)
    
    def _create_builder_content(self, builder):
        # Linha 1: Período e módulo base
        row1 = tk.Frame(builder, bg='white')
        row1.pack(fill='x')
        tk.Label(row1, text='Data inicial:', background='white').pack(side='left')
        self.start_date_var = getattr(self, 'start_date_var', tk.StringVar(value=datetime.now().strftime(DATE_FMT)))
        tk.Entry(row1, textvariable=self.start_date_var, width=12).pack(side='left', padx=(6, 12))
        tk.Label(row1, text='Data final:', background='white').pack(side='left')
        self.end_date_var = getattr(self, 'end_date_var', tk.StringVar(value=datetime.now().strftime(DATE_FMT)))
        tk.Entry(row1, textvariable=self.end_date_var, width=12).pack(side='left', padx=(6, 18))
        tk.Label(row1, text='Módulo base:', background='white').pack(side='left')
        self.base_module_var = getattr(self, 'base_module_var', tk.StringVar(value='Cotações'))
        self.base_module_combo = ttk.Combobox(row1, textvariable=self.base_module_var, state='readonly', width=20,
                                              values=['Clientes','Produtos','Cotações','Relatórios','Usuários'])
        self.base_module_combo.pack(side='left', padx=(6, 0))
        self.base_module_combo.bind('<<ComboboxSelected>>', lambda e: self.sync_module_tabs())
        
        # Linha 2: Combinações de módulos (como antes)
        row2 = tk.Frame(builder, bg='white')
        row2.pack(fill='x', pady=(10, 6))
        tk.Label(row2, text='Combinar com:', background='white').pack(side='left')
        self.combine_vars = {
            'Clientes': tk.BooleanVar(value=False),
            'Produtos': tk.BooleanVar(value=False),
            'Cotações': tk.BooleanVar(value=False),
            'Relatórios': tk.BooleanVar(value=False),
            'Usuários': tk.BooleanVar(value=False)
        }
        for name, var in self.combine_vars.items():
            cb = tk.Checkbutton(row2, text=name, variable=var, bg='white', onvalue=True, offvalue=False, command=self.sync_module_tabs)
            cb.pack(side='left', padx=(6, 6))
        
        # Painel avançado original
        self._create_advanced_panel(builder)
        
        # Resultados
        results = tk.Frame(builder, bg='white')
        results.pack(fill='both', expand=True, pady=(8, 0))
        self.tree = ttk.Treeview(results, columns=("resultado"), show='headings', height=16)
        self.tree.pack(side='left', fill='both', expand=True)
        scroll = ttk.Scrollbar(results, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
    
    def _create_advanced_panel(self, builder):
        # Abas por módulo para seleção de campos
        self.tabs = ttk.Notebook(builder)
        self.tabs.pack(fill='both', expand=True, pady=(10, 10))
        self.module_fields = {
            'Clientes': [
                ('ID', 'cl.id'), ('Nome', 'cl.nome'), ('Nome Fantasia', 'cl.nome_fantasia'),
                ('CNPJ', 'cl.cnpj'), ('Estado', 'cl.estado'), ('Cidade', 'cl.cidade'),
                ('Telefone', 'cl.telefone'), ('Email', 'cl.email'), ('Criado em', 'cl.created_at')
            ],
            'Produtos': [
                ('ID', 'p.id'), ('Nome', 'p.nome'), ('Tipo', 'p.tipo'), ('NCM', 'p.ncm'),
                ('Valor Unitário', 'p.valor_unitario'), ('Ativo', 'p.ativo'), ('Criado em', 'p.created_at')
            ],
            'Cotações': [
                ('ID', 'c.id'), ('Número', 'c.numero_proposta'), ('Cliente ID', 'c.cliente_id'), ('Responsável ID', 'c.responsavel_id'),
                ('Data', 'c.data_criacao'), ('Status', 'c.status'), ('Valor Total', 'c.valor_total'),
                ('Modelo Compressor', 'c.modelo_compressor'), ('Série Compressor', 'c.numero_serie_compressor'), ('Moeda', 'c.moeda')
            ],
            'Relatórios': [
                ('ID', 'r.id'), ('Número', 'r.numero_relatorio'), ('Cliente ID', 'r.cliente_id'), ('Responsável ID', 'r.responsavel_id'),
                ('Data', 'r.data_criacao'), ('Tipo Serviço', 'r.tipo_servico'), ('Tempo Trabalho', 'r.tempo_trabalho_total'), ('Tempo Deslocamento', 'r.tempo_deslocamento_total')
            ],
            'Usuários': [
                ('ID', 'u.id'), ('Nome Completo', 'u.nome_completo'), ('Username', 'u.username'),
                ('Email', 'u.email'), ('Telefone', 'u.telefone'), ('Criado em', 'u.created_at')
            ]
        }
        self.autofill_module_fields()
        self.tab_frames = {}
        self.tab_vars = {}
        for module in ['Clientes','Produtos','Cotações','Relatórios','Usuários']:
            frame = tk.Frame(self.tabs, bg='white')
            self.tabs.add(frame, text=module)
            self.tab_frames[module] = frame
            
            vars_for_module = {}
            grid = tk.Frame(frame, bg='white')
            grid.pack(fill='both', expand=True, padx=10, pady=10)
            
            # dica
            self._add_fields_grid(module, grid, vars_for_module)
            self.tab_vars[module] = vars_for_module
        
        # Relações
        relations = tk.LabelFrame(builder, text='Relações automáticas', bg='white', padx=10, pady=10)
        relations.pack(fill='x', pady=(6, 6))
        self.relations_text = tk.Label(relations, bg='white', fg='#334155', justify='left')
        self.relations_text.pack(anchor='w')
        self.sync_module_tabs()
        # Ações
        actions = tk.Frame(builder, bg='white')
        actions.pack(fill='x', pady=(10, 6))
        self.create_button(actions, 'Executar', self.execute_query, bg='#3b82f6').pack(side='left')
        self.create_button(actions, 'Exportar Excel', self.export_excel, bg='#0ea5e9').pack(side='left', padx=(8,0))
    
    def _add_fields_grid(self, module, grid, vars_for_module):
        if module == 'Clientes':
            hint = 'Selecione dados de cadastro: Estado, Cidade, Nome, etc.'
        elif module == 'Produtos':
            hint = 'Veja itens cadastrados por tipo ou geral.'
        elif module == 'Cotações':
            hint = 'Selecione campos para puxar a cotação completa.'
        elif module == 'Relatórios':
            hint = 'Selecione campos para consultar relatórios completos.'
        else:
            hint = 'Selecione campos do usuário.'
        tk.Label(grid, text=hint, bg='white', fg='#475569', font=('Arial', 9, 'italic')).pack(anchor='w', pady=(0,8))
        fields_frame = tk.Frame(grid, bg='white')
        fields_frame.pack(anchor='w')
        for i, (label, expr) in enumerate(self.module_fields[module]):
            var = tk.BooleanVar(value=(label in ['ID','Nome','Número','Data']))
            cb = tk.Checkbutton(fields_frame, text=label, variable=var, bg='white')
            cb.grid(row=i//3, column=i%3, sticky='w', padx=6, pady=4)
            vars_for_module[label] = (var, expr)
    
    def _ensure_module_fields_loaded(self):
        if not hasattr(self, 'module_fields') or not self.module_fields:
            # Inicial defaults (serão complementados)
            self.module_fields = {
                'Clientes': [('ID','cl.id')],
                'Produtos': [('ID','p.id')],
                'Cotações': [('ID','c.id')],
                'Relatórios': [('ID','r.id')],
                'Usuários': [('ID','u.id')],
            }
            self.autofill_module_fields()
    
    def build_sql(self):
        start = self.start_date_var.get().strip()
        end = self.end_date_var.get().strip()
        for d in [start, end]:
            try:
                datetime.strptime(d, DATE_FMT)
            except ValueError:
                self.show_warning('Datas devem estar no formato YYYY-MM-DD.')
                return None, None
        included = [name for name, var in self.combine_vars.items() if var.get()]
        base = self.base_module_var.get()
        if base not in included:
            included.append(base)
        module_alias = {'Clientes':'cl','Produtos':'p','Cotações':'c','Relatórios':'r','Usuários':'u'}
        alias_table = {'cl':'clientes cl','p':'produtos p','c':'cotacoes c','r':'relatorios_tecnicos r','u':'usuarios u','ic':'itens_cotacao ic'}
        join_defs = {('c','cl'):'c.cliente_id = cl.id',('cl','c'):'c.cliente_id = cl.id',('c','u'):'c.responsavel_id = u.id',('u','c'):'c.responsavel_id = u.id',('r','cl'):'r.cliente_id = cl.id',('cl','r'):'r.cliente_id = cl.id',('r','u'):'r.responsavel_id = u.id',('u','r'):'r.responsavel_id = u.id',('ic','c'):'ic.cotacao_id = c.id',('c','ic'):'ic.cotacao_id = c.id',('ic','p'):'ic.produto_id = p.id',('p','ic'):'ic.produto_id = p.id'}
        adjacency = {}
        for (a,b),cond in join_defs.items():
            adjacency.setdefault(a, []).append(b)
        base_alias = module_alias[base]
        active_aliases = {base_alias}
        joins_sql = []
        from collections import deque
        def bfs_find_path(target_alias):
            q=deque(); visited=set(); parent={}
            for src in active_aliases:
                q.append(src); visited.add(src); parent[src]=None
            while q:
                node=q.popleft()
                if node==target_alias:
                    path=[]; cur=node
                    while cur is not None:
                        path.append(cur); cur=parent[cur]
                    path.reverse(); return path
                for nb in adjacency.get(node, []):
                    if nb not in visited:
                        visited.add(nb); parent[nb]=node; q.append(nb)
            return None
        desired_aliases = {module_alias[m] for m in included if m in module_alias}
        for dest in list(desired_aliases):
            if dest in active_aliases: continue
            path=bfs_find_path(dest)
            if not path:
                if ('c' in active_aliases and dest=='p') or ('p' in active_aliases and dest=='c'):
                    if 'ic' not in active_aliases:
                        path_ic=bfs_find_path('ic') or ([next(iter(active_aliases)), 'c','ic'] if 'c' in active_aliases else None)
                        if path_ic:
                            for i in range(len(path_ic)-1):
                                a,b=path_ic[i],path_ic[i+1]
                                if b not in active_aliases:
                                    joins_sql.append(f"LEFT JOIN {alias_table[b]} ON {join_defs[(a,b)]}"); active_aliases.add(b)
                    path=bfs_find_path(dest)
            if not path: continue
            for i in range(len(path)-1):
                a,b=path[i],path[i+1]
                if b not in active_aliases:
                    joins_sql.append(f"LEFT JOIN {alias_table[b]} ON {join_defs[(a,b)]}"); active_aliases.add(b)
        date_field={'Clientes':'cl.created_at','Produtos':'p.created_at','Cotações':'c.data_criacao','Relatórios':'r.data_criacao','Usuários':'u.created_at'}[base]
        where=f"WHERE {date_field} BETWEEN ? AND ?"; params=[start,end]
        selects=[]; self.results_columns=[]
        active_modules={m for m,a in {'Clientes':'cl','Produtos':'p','Cotações':'c','Relatórios':'r','Usuários':'u'}.items() if a in active_aliases}
        for module,fields in self.tab_vars.items():
            if module not in included or module not in active_modules: continue
            for label,(var,expr) in fields.items():
                if var.get(): selects.append(f"{expr} AS '{module}: {label}'"); self.results_columns.append(f"{module}: {label}")
        if not selects:
            self.show_warning('Selecione ao menos um campo em alguma aba.')
            return None, None
        from_clause={'Clientes':'clientes cl','Produtos':'produtos p','Cotações':'cotacoes c','Relatórios':'relatorios_tecnicos r','Usuários':'usuarios u'}[base]
        sql=f"SELECT {', '.join(selects)} FROM {from_clause} {' ' + ' '.join(joins_sql) if joins_sql else ''} {where} LIMIT 1000"; return sql, params
    
    def _build_sql_simple(self):
        # validar datas
        start=self.start_date_var.get().strip(); end=self.end_date_var.get().strip()
        for d in [start,end]:
            try: datetime.strptime(d, DATE_FMT)
            except ValueError:
                self.show_warning('Datas devem estar no formato YYYY-MM-DD.'); return None, None
        self._ensure_module_fields_loaded()
        base=self.base_module_var.get(); alias={'Clientes':'cl','Produtos':'p','Cotações':'c','Relatórios':'r','Usuários':'u'}[base]
        from_clause={'Clientes':'clientes cl','Produtos':'produtos p','Cotações':'cotacoes c','Relatórios':'relatorios_tecnicos r','Usuários':'usuarios u'}[base]
        date_field={'Clientes':'cl.created_at','Produtos':'p.created_at','Cotações':'c.data_criacao','Relatórios':'r.data_criacao','Usuários':'u.created_at'}[base]
        # map rótulo->expr
        label_to_expr={label:expr for (label,expr) in self.module_fields.get(base, [])}
        where_clauses=[f"{date_field} BETWEEN ? AND ?"]; params=[start,end]
        for f in self.simple_filters:
            if not f or 'field_var' not in f: continue
            field_label=f['field_var'].get().strip(); op=f['op_var'].get().strip(); v=f['value_var'].get().strip(); v2=f['value2_var'].get().strip()
            if not field_label or not op or not v: continue
            expr=label_to_expr.get(field_label)
            if not expr: continue
            if op=='=':
                where_clauses.append(f"{expr} = ?"); params.append(v)
            elif op=='contém':
                where_clauses.append(f"{expr} LIKE ?"); params.append(f"%{v}%")
            elif op=='começa com':
                where_clauses.append(f"{expr} LIKE ?"); params.append(f"{v}%")
            elif op=='termina com':
                where_clauses.append(f"{expr} LIKE ?"); params.append(f"%{v}")
            elif op in ('>','>=','<','<='):
                where_clauses.append(f"{expr} {op} ?"); params.append(v)
            elif op=='entre' and v2:
                where_clauses.append(f"{expr} BETWEEN ? AND ?"); params.extend([v, v2])
        # selects padrão: todas as colunas do módulo base mais comuns
        default_fields=[expr for (label,expr) in self.module_fields.get(base, []) if label in ('ID','Nome','Número','Data','Valor Total','Status')]
        selects=default_fields or [next(iter(self.module_fields.get(base, [('ID',f'{alias}.id')])), ('',f'{alias}.id'))[1]]
        columns=[label for (label,expr) in self.module_fields.get(base, []) if expr in selects]
        sql=f"SELECT {', '.join(selects)} FROM {from_clause} WHERE {' AND '.join(where_clauses)} LIMIT 1000"; self.results_columns=columns; return sql, params
    
    def execute_query(self):
        sql, params = self.build_sql()
        if not sql:
            return
        
        try:
            conn = sqlite3.connect(DB_NAME); c = conn.cursor(); c.execute(sql, params); rows = c.fetchall()
        except sqlite3.Error as e:
            self.show_error(f"Erro ao executar: {e}\nSQL: {sql}"); return
        finally:
            if 'conn' in locals(): conn.close()
        self.results_rows = rows
        self.tree.delete(*self.tree.get_children())
        self.tree['columns'] = self.results_columns
        for col in self.results_columns:
            self.tree.heading(col, text=col); self.tree.column(col, width=180)
        for row in rows:
            self.tree.insert('', 'end', values=row)
    
    def export_excel(self):
        if not self.results_columns or not self.results_rows:
            self.show_warning('Nenhum resultado para exportar.')
            return
        try:
            os.makedirs(os.path.join('data', 'consultas', 'exports'), exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = os.path.join('data', 'consultas', 'exports', f'consulta_{timestamp}.xlsx')
            wb = Workbook()
            ws = wb.active
            ws.title = 'Resultados'
            ws.append(self.results_columns)
            for r in self.results_rows:
                ws.append(list(r))
            wb.save(filepath)
            self.show_success(f'Arquivo exportado: {filepath}')
        except Exception as e:
            self.show_error(f'Erro ao exportar: {e}')
    
    def handle_event(self, event_type, data=None):
        pass

    def sync_module_tabs(self):
        base = self.base_module_var.get()
        # Marcar base sempre combinado
        for name, var in self.combine_vars.items():
            if name == base:
                var.set(True)
        # Atualizar texto de relações
        rels = [
            'Cotações c → Clientes cl: c.cliente_id = cl.id',
            'Cotações c → Usuários u: c.responsavel_id = u.id',
            'Itens (via Produtos p) → Cotações c: (não usado direto aqui)',
            'Relatórios r → Clientes cl: r.cliente_id = cl.id',
            'Relatórios r → Usuários u: r.responsavel_id = u.id'
        ]
        self.relations_text.config(text='\n'.join(rels))