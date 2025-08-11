import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sqlite3
from datetime import datetime, timedelta
from .base_module import BaseModule
from database import DB_NAME
from utils.formatters import format_currency, format_date
import os
from openpyxl import Workbook

class ConsultasModule(BaseModule):
    def setup_ui(self):
        # Container principal
        container = tk.Frame(self.frame, bg='#f8fafc')
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        self.create_header(container)
        
        # Builder visual (uma única aba)
        self.create_visual_query_ui(container)
        
        # Estado
        self.current_user_id = None
        self.query_result_rows = []
        self.query_result_columns = []
    
    def create_header(self, parent):
        header_frame = tk.Frame(parent, bg='#f8fafc')
        header_frame.pack(fill="x", pady=(0, 20))
        
        title_label = tk.Label(header_frame, text="Consultas (Construtor Visual)", 
                               font=('Arial', 18, 'bold'),
                               bg='#f8fafc',
                               fg='#1e293b')
        title_label.pack(side="left")
    
    def create_visual_query_ui(self, parent):
        # Config da área principal
        content = tk.Frame(parent, bg='white', padx=20, pady=20)
        content.pack(fill='both', expand=True)
        
        # Configuração das tabelas, campos e relações
        self.tables_config = {
            'Cotações': {
                'table': 'cotacoes c',
                'joins': {
                    'Cliente': 'JOIN clientes cl ON c.cliente_id = cl.id',
                    'Responsável': 'JOIN usuarios u ON c.responsavel_id = u.id',
                    'Itens da Cotação': 'LEFT JOIN itens_cotacao ic ON ic.cotacao_id = c.id'
                },
                'fields': {
                    'Número': 'c.numero_proposta',
                    'Data': 'c.data_criacao',
                    'Status': 'c.status',
                    'Valor Total': 'c.valor_total',
                    'Cliente': 'cl.nome',
                    'CNPJ Cliente': 'cl.cnpj',
                    'Cidade Cliente': 'cl.cidade',
                    'Responsável': 'u.nome_completo',
                    'Tipo Item (ic)': 'ic.tipo',
                    'Descrição Item (ic)': 'ic.item_nome',
                    'Qtd Item (ic)': 'ic.quantidade',
                    'Vlr Unit Item (ic)': 'ic.valor_unitario',
                    'Vlr Total Item (ic)': 'ic.valor_total_item'
                }
            },
            'Clientes': {
                'table': 'clientes cl',
                'joins': {
                    'Cotações': 'LEFT JOIN cotacoes c ON c.cliente_id = cl.id',
                    'Responsável (Cotação)': 'LEFT JOIN usuarios u ON u.id = c.responsavel_id'
                },
                'fields': {
                    'ID Cliente': 'cl.id',
                    'Nome': 'cl.nome',
                    'Nome Fantasia': 'cl.nome_fantasia',
                    'CNPJ': 'cl.cnpj',
                    'Cidade': 'cl.cidade',
                    'Estado': 'cl.estado',
                    'Telefone': 'cl.telefone',
                    'Email': 'cl.email',
                    'Número Proposta (c)': 'c.numero_proposta',
                    'Data Cotação (c)': 'c.data_criacao',
                    'Status Cotação (c)': 'c.status',
                    'Responsável (u)': 'u.nome_completo'
                }
            },
            'Relatórios Técnicos': {
                'table': 'relatorios_tecnicos r',
                'joins': {
                    'Cliente': 'JOIN clientes cl ON r.cliente_id = cl.id',
                    'Responsável': 'JOIN usuarios u ON r.responsavel_id = u.id',
                    'Eventos de Campo': 'LEFT JOIN eventos_campo e ON e.relatorio_id = r.id'
                },
                'fields': {
                    'Número Relatório': 'r.numero_relatorio',
                    'Data Criação': 'r.data_criacao',
                    'Cliente': 'cl.nome',
                    'Responsável': 'u.nome_completo',
                    'Tipo Serviço': 'r.tipo_servico',
                    'Tempo Trabalho Total': 'r.tempo_trabalho_total',
                    'Tempo Deslocamento Total': 'r.tempo_deslocamento_total',
                    'Evento (e)': 'e.evento',
                    'Tipo Evento (e)': 'e.tipo',
                    'Data/Hora Evento (e)': 'e.data_hora'
                }
            },
            'Itens de Cotação': {
                'table': 'itens_cotacao ic',
                'joins': {
                    'Cotação': 'JOIN cotacoes c ON ic.cotacao_id = c.id',
                    'Cliente': 'JOIN clientes cl ON c.cliente_id = cl.id'
                },
                'fields': {
                    'ID Item': 'ic.id',
                    'Tipo': 'ic.tipo',
                    'Item Nome': 'ic.item_nome',
                    'Quantidade': 'ic.quantidade',
                    'Valor Unitário': 'ic.valor_unitario',
                    'Valor Total Item': 'ic.valor_total_item',
                    'Número Proposta (c)': 'c.numero_proposta',
                    'Cliente (cl)': 'cl.nome',
                    'Data Cotação (c)': 'c.data_criacao'
                }
            },
            'Usuários': {
                'table': 'usuarios u',
                'joins': {
                    'Cotações': 'LEFT JOIN cotacoes c ON c.responsavel_id = u.id',
                    'Relatórios': 'LEFT JOIN relatorios_tecnicos r ON r.responsavel_id = u.id'
                },
                'fields': {
                    'ID Usuário': 'u.id',
                    'Nome Completo': 'u.nome_completo',
                    'Username': 'u.username',
                    'Email': 'u.email',
                    'Telefone': 'u.telefone',
                    'Qtd Cotações (c)': 'COUNT(DISTINCT c.id)',
                    'Qtd Relatórios (r)': 'COUNT(DISTINCT r.id)'
                }
            },
            'Eventos de Campo': {
                'table': 'eventos_campo e',
                'joins': {
                    'Relatório': 'JOIN relatorios_tecnicos r ON e.relatorio_id = r.id',
                    'Técnico (Usuários)': 'JOIN usuarios u ON e.tecnico_id = u.id',
                    'Cliente': 'JOIN clientes cl ON r.cliente_id = cl.id'
                },
                'fields': {
                    'ID Evento': 'e.id',
                    'Técnico': 'u.nome_completo',
                    'Data/Hora': 'e.data_hora',
                    'Tipo': 'e.tipo',
                    'Evento': 'e.evento',
                    'Nº Relatório (r)': 'r.numero_relatorio',
                    'Cliente (cl)': 'cl.nome'
                }
            }
        }
        
        # Linha de seleção de base e relações
        top_bar = tk.Frame(content, bg='white')
        top_bar.pack(fill='x', pady=(0, 10))
        
        tk.Label(top_bar, text='Base:', font=('Arial', 10, 'bold'), bg='white').pack(side='left')
        self.base_table_var = tk.StringVar(value='Cotações')
        self.base_combo = ttk.Combobox(top_bar, textvariable=self.base_table_var, values=list(self.tables_config.keys()), state='readonly', width=25)
        self.base_combo.pack(side='left', padx=(8, 20))
        self.base_combo.bind('<<ComboboxSelected>>', lambda e: self.on_base_change())
        
        self.relations_frame = tk.Frame(content, bg='white')
        self.relations_frame.pack(fill='x', pady=(0, 10))
        
        # Seleção de campos
        fields_section = tk.Frame(content, bg='white')
        fields_section.pack(fill='x', pady=(0, 10))
        tk.Label(fields_section, text='Campos:', font=('Arial', 10, 'bold'), bg='white').pack(anchor='w')
        
        list_frame = tk.Frame(fields_section, bg='white')
        list_frame.pack(fill='x')
        
        self.fields_listbox = tk.Listbox(list_frame, selectmode='extended', width=70, height=8)
        self.fields_listbox.pack(side='left', fill='x', expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.fields_listbox.yview)
        self.fields_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='left', fill='y')
        
        buttons_side = tk.Frame(list_frame, bg='white')
        buttons_side.pack(side='left', padx=(10, 0))
        self.create_button(buttons_side, 'Selecionar Todos', self.select_all_fields, bg='#64748b').pack(fill='x')
        self.create_button(buttons_side, 'Limpar Seleção', self.clear_field_selection, bg='#94a3b8').pack(fill='x', pady=(6,0))
        
        # Filtros
        filters_section = tk.Frame(content, bg='white')
        filters_section.pack(fill='x', pady=(10, 10))
        
        header_filters = tk.Frame(filters_section, bg='white')
        header_filters.pack(fill='x')
        tk.Label(header_filters, text='Filtros:', font=('Arial', 10, 'bold'), bg='white').pack(side='left')
        self.create_button(header_filters, '+ Adicionar filtro', self.add_filter_row, bg='#10b981').pack(side='left', padx=(10,0))
        
        self.filters_rows_frame = tk.Frame(filters_section, bg='white')
        self.filters_rows_frame.pack(fill='x', pady=(6, 0))
        self.filter_rows = []
        
        # Ordenação e Limite
        order_section = tk.Frame(content, bg='white')
        order_section.pack(fill='x', pady=(10, 10))
        
        tk.Label(order_section, text='Ordenar por:', font=('Arial', 10, 'bold'), bg='white').pack(side='left')
        self.order_field_var = tk.StringVar()
        self.order_field_combo = ttk.Combobox(order_section, textvariable=self.order_field_var, state='readonly', width=30)
        self.order_field_combo.pack(side='left', padx=(8, 10))
        
        self.order_dir_var = tk.StringVar(value='ASC')
        ttk.Combobox(order_section, textvariable=self.order_dir_var, state='readonly', values=['ASC', 'DESC'], width=6).pack(side='left')
        
        tk.Label(order_section, text='Limite:', font=('Arial', 10, 'bold'), bg='white').pack(side='left', padx=(20, 0))
        self.limit_var = tk.StringVar(value='200')
        tk.Entry(order_section, textvariable=self.limit_var, width=8).pack(side='left', padx=(8, 0))
        
        # Ações
        actions = tk.Frame(content, bg='white')
        actions.pack(fill='x', pady=(5, 10))
        self.create_button(actions, 'Executar', self.build_and_execute_query, bg='#3b82f6').pack(side='left')
        self.create_button(actions, 'Exportar Excel', self.export_to_excel, bg='#0ea5e9').pack(side='left', padx=(10,0))
        
        # Resultados
        results = tk.Frame(content, bg='white')
        results.pack(fill='both', expand=True)
        self.results_tree = ttk.Treeview(results, columns=("resultado"), show='headings', height=16)
        self.results_tree.pack(side='left', fill='both', expand=True)
        res_scroll = ttk.Scrollbar(results, orient='vertical', command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=res_scroll.set)
        res_scroll.pack(side='right', fill='y')
        
        # Inicializar UI
        self.on_base_change()
    
    def on_base_change(self):
        # Limpar relações e campos
        for child in self.relations_frame.winfo_children():
            child.destroy()
        self.fields_listbox.delete(0, tk.END)
        self.filter_rows.clear()
        for child in self.filters_rows_frame.winfo_children():
            child.destroy()
        
        base = self.base_table_var.get()
        cfg = self.tables_config.get(base, {})
        
        # Renderizar relações como checkbuttons
        self.selected_relations = {}
        joins = cfg.get('joins', {})
        if joins:
            tk.Label(self.relations_frame, text='Relações:', font=('Arial', 10, 'bold'), bg='white').pack(anchor='w')
            rels_bar = tk.Frame(self.relations_frame, bg='white')
            rels_bar.pack(fill='x', pady=(4,0))
            for rel_name in joins.keys():
                var = tk.BooleanVar(value=True if base in ['Cotações', 'Relatórios Técnicos'] and rel_name in ['Cliente', 'Responsável'] else False)
                chk = tk.Checkbutton(rels_bar, text=rel_name, variable=var, bg='white', onvalue=True, offvalue=False, command=self.update_fields_and_relations)
                chk.pack(side='left', padx=(0, 10))
                self.selected_relations[rel_name] = var
        
        self.update_fields_and_relations()
    
    def update_fields_and_relations(self):
        # Atualiza campos disponíveis e opções de ordenação conforme relações marcadas
        base = self.base_table_var.get()
        cfg = self.tables_config.get(base, {})
        base_fields = cfg.get('fields', {})
        joins_selected = {name for name, var in self.selected_relations.items() if var.get()} if hasattr(self, 'selected_relations') else set()
        
        # Regra simples: campos cujo identificador contém apelido de join ausente serão ocultados
        def field_allowed(label, expr):
            if ' cl.' in f' {expr}' and 'Cliente' not in joins_selected and base != 'Clientes':
                return False
            if ' u.' in f' {expr}' and not any(rel in joins_selected for rel in ['Responsável', 'Responsável (Cotação)', 'Técnico (Usuários)']) and base != 'Usuários':
                return False
            if ' ic.' in f' {expr}' and 'Itens da Cotação' not in joins_selected and base != 'Itens de Cotação':
                return False
            if ' e.' in f' {expr}' and 'Eventos de Campo' not in joins_selected and base != 'Eventos de Campo':
                return False
            if ' r.' in f' {expr}' and 'Relatório' not in joins_selected and base != 'Relatórios Técnicos' and base != 'Eventos de Campo':
                # Permite r.* quando base é Relatórios Técnicos ou Eventos
                return False
            if ' c.' in f' {expr}' and 'Cotação' not in joins_selected and base != 'Cotações' and base != 'Itens de Cotação' and base != 'Clientes' and base != 'Usuários':
                return False
            return True
        
        # Repopular listbox de campos
        self.fields_listbox.delete(0, tk.END)
        self.current_field_map = {}
        for label, expr in base_fields.items():
            if field_allowed(label, expr):
                self.current_field_map[label] = expr
                self.fields_listbox.insert(tk.END, label)
        
        # Atualizar opções de ordenação
        self.order_field_combo['values'] = list(self.current_field_map.keys())
        if self.order_field_var.get() not in self.order_field_combo['values']:
            self.order_field_var.set('')
        
        # Se não houver filtro ainda, adicionar um por padrão
        if not self.filter_rows:
            self.add_filter_row()
    
    def select_all_fields(self):
        self.fields_listbox.select_set(0, tk.END)
    
    def clear_field_selection(self):
        self.fields_listbox.selection_clear(0, tk.END)
    
    def add_filter_row(self):
        row = tk.Frame(self.filters_rows_frame, bg='white')
        row.pack(fill='x', pady=3)
        
        field_var = tk.StringVar()
        field_combo = ttk.Combobox(row, textvariable=field_var, values=list(self.current_field_map.keys()), state='readonly', width=30)
        field_combo.pack(side='left')
        
        op_var = tk.StringVar(value='=')
        ops = ['=', '!=', 'contém', 'não contém', '>', '>=', '<', '<=', 'entre']
        op_combo = ttk.Combobox(row, textvariable=op_var, values=ops, state='readonly', width=12)
        op_combo.pack(side='left', padx=(8, 8))
        
        value_var = tk.StringVar()
        value_entry = tk.Entry(row, textvariable=value_var, width=30)
        value_entry.pack(side='left')
        
        remove_btn = self.create_button(row, 'Remover', lambda r=row: self.remove_filter_row(r), bg='#ef4444')
        remove_btn.pack(side='left', padx=(8, 0))
        
        self.filter_rows.append({'frame': row, 'field': field_var, 'op': op_var, 'value': value_var})
    
    def remove_filter_row(self, row_frame):
        for fr in list(self.filter_rows):
            if fr['frame'] == row_frame:
                fr['frame'].destroy()
                self.filter_rows.remove(fr)
                break
    
    def build_and_execute_query(self):
        base = self.base_table_var.get()
        cfg = self.tables_config.get(base, {})
        table = cfg.get('table')
        if not table:
            self.show_error('Tabela base inválida.')
            return
        
        # Campos selecionados
        selected_indices = self.fields_listbox.curselection()
        selected_labels = [self.fields_listbox.get(i) for i in selected_indices] if selected_indices else list(self.current_field_map.keys())[:6]
        if not selected_labels:
            self.show_warning('Selecione ao menos um campo.')
            return
        
        fields_exprs = [self.current_field_map[lbl] for lbl in selected_labels]
        
        # FROM + JOINS
        joins_sql = []
        for rel_name, var in getattr(self, 'selected_relations', {}).items():
            if var.get():
                join_clause = cfg['joins'].get(rel_name)
                if join_clause:
                    joins_sql.append(join_clause)
        
        # WHERE
        where_clauses = []
        params = []
        for fr in self.filter_rows:
            field_lbl = fr['field'].get()
            op = fr['op'].get()
            val = fr['value'].get().strip()
            if not field_lbl or not op or val == '':
                continue
            expr = self.current_field_map.get(field_lbl)
            if not expr:
                continue
            if op == 'contém':
                where_clauses.append(f"{expr} LIKE ?")
                params.append(f"%{val}%")
            elif op == 'não contém':
                where_clauses.append(f"{expr} NOT LIKE ?")
                params.append(f"%{val}%")
            elif op == 'entre':
                # aceitar 'v1;v2' ou 'v1,v2'
                sep = ';' if ';' in val else (',' if ',' in val else None)
                if not sep:
                    self.show_warning("Para operador 'entre', use 'valor1;valor2'.")
                    return
                v1, v2 = [v.strip() for v in val.split(sep, 1)]
                where_clauses.append(f"{expr} BETWEEN ? AND ?")
                params.extend([v1, v2])
            else:
                where_clauses.append(f"{expr} {op} ?")
                params.append(val)
        
        # ORDER
        order_sql = ''
        if self.order_field_var.get():
            order_expr = self.current_field_map.get(self.order_field_var.get())
            if order_expr:
                order_sql = f" ORDER BY {order_expr} {self.order_dir_var.get()}"
        
        # LIMIT
        limit_sql = ''
        try:
            limit_val = int(self.limit_var.get()) if self.limit_var.get().strip() else 0
            if limit_val > 0:
                limit_sql = f" LIMIT {limit_val}"
        except ValueError:
            self.show_warning('Limite inválido.')
            return
        
        # Montar SQL
        select_parts = []
        aliases = []
        for lbl, expr in zip(selected_labels, fields_exprs):
            select_parts.append(f"{expr} AS '{lbl}'")
            aliases.append(lbl)
        
        sql = f"SELECT {', '.join(select_parts)} FROM {table} " + ' '.join(joins_sql)
        if where_clauses:
            sql += ' WHERE ' + ' AND '.join(where_clauses)
        sql += order_sql + limit_sql
        
        # Executar
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute(sql, params)
            rows = c.fetchall()
            col_names = [d[0] for d in c.description]
        except sqlite3.Error as e:
            self.show_error(f"Erro ao executar consulta: {e}")
            return
        finally:
            if 'conn' in locals():
                conn.close()
        
        # Atualizar resultados
        self.query_result_rows = rows
        self.query_result_columns = col_names
        
        # Configurar treeview
        self.results_tree.delete(*self.results_tree.get_children())
        self.results_tree['columns'] = col_names
        for col in col_names:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=150)
        for row in rows:
            self.results_tree.insert('', 'end', values=row)
    
    def export_to_excel(self):
        if not self.query_result_rows or not self.query_result_columns:
            self.show_warning('Nenhum resultado para exportar.')
            return
        
        try:
            os.makedirs(os.path.join('data', 'consultas', 'exports'), exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base = self.base_table_var.get().replace(' ', '_').lower()
            filepath = os.path.join('data', 'consultas', 'exports', f'consulta_{base}_{timestamp}.xlsx')
            
            wb = Workbook()
            ws = wb.active
            ws.title = 'Resultados'
            
            # Cabeçalhos
            ws.append(self.query_result_columns)
            
            # Linhas
            for r in self.query_result_rows:
                ws.append(list(r))
            
            wb.save(filepath)
            self.show_success(f'Arquivo exportado: {filepath}')
        except Exception as e:
            self.show_error(f'Erro ao exportar: {e}')
    
    def calcular_data_limite(self, periodo):
        # Mantido para compatibilidade com possíveis usos
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
        if event_type == 'usuario_changed':
            self.current_user_id = data