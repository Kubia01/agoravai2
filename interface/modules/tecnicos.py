import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from .base_module import BaseModule
from database import DB_NAME
from utils.formatters import format_phone, validate_email

class TecnicosModule(BaseModule):
    def setup_ui(self):
        container = tk.Frame(self.frame, bg='#f8fafc')
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        self.create_header(container)
        
        # Notebook
        self.notebook = ttk.Notebook(container)
        self.notebook.pack(fill="both", expand=True, pady=(20, 0))
        
        # Abas
        self.create_novo_tecnico_tab()
        self.create_lista_tecnicos_tab()
        
        self.current_tecnico_id = None
        self.carregar_tecnicos()
        
    def create_header(self, parent):
        header_frame = tk.Frame(parent, bg='#f8fafc')
        header_frame.pack(fill="x", pady=(0, 20))
        
        title_label = tk.Label(header_frame, text="Gestão de Técnicos", 
                               font=('Arial', 18, 'bold'), bg='#f8fafc', fg='#1e293b')
        title_label.pack(side="left")
        
    def create_novo_tecnico_tab(self):
        tecnico_frame = tk.Frame(self.notebook, bg='white')
        self.notebook.add(tecnico_frame, text="Novo Técnico")
        
        content_frame = tk.Frame(tecnico_frame, bg='white', padx=20, pady=20)
        content_frame.pack(fill="both", expand=True)
        
        # Seção principal
        section_frame = self.create_section_frame(content_frame, "Dados do Técnico")
        section_frame.pack(fill="x", pady=(0, 15))
        
        fields_frame = tk.Frame(section_frame, bg='white')
        fields_frame.pack(fill="x")
        
        # Variáveis
        self.nome_var = tk.StringVar()
        self.especialidade_var = tk.StringVar()
        self.telefone_var = tk.StringVar()
        self.email_var = tk.StringVar()
        
        row = 0
        
        # Nome
        tk.Label(fields_frame, text="Nome *:", font=('Arial', 10, 'bold'), bg='white').grid(row=row, column=0, sticky="w", pady=5)
        tk.Entry(fields_frame, textvariable=self.nome_var, font=('Arial', 10), width=40).grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        row += 1
        
        # Especialidade
        tk.Label(fields_frame, text="Especialidade:", font=('Arial', 10, 'bold'), bg='white').grid(row=row, column=0, sticky="w", pady=5)
        especialidade_combo = ttk.Combobox(fields_frame, textvariable=self.especialidade_var, 
                                          values=["Compressores", "Refrigeração", "Manutenção Geral", "Elétrica", "Mecânica"],
                                          width=37)
        especialidade_combo.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        row += 1
        
        # Telefone
        tk.Label(fields_frame, text="Telefone:", font=('Arial', 10, 'bold'), bg='white').grid(row=row, column=0, sticky="w", pady=5)
        telefone_entry = tk.Entry(fields_frame, textvariable=self.telefone_var, font=('Arial', 10), width=40)
        telefone_entry.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        telefone_entry.bind('<FocusOut>', self.format_telefone)
        row += 1
        
        # Email
        tk.Label(fields_frame, text="Email:", font=('Arial', 10, 'bold'), bg='white').grid(row=row, column=0, sticky="w", pady=5)
        tk.Entry(fields_frame, textvariable=self.email_var, font=('Arial', 10), width=40).grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        
        fields_frame.grid_columnconfigure(1, weight=1)
        
        # Botões
        buttons_frame = tk.Frame(content_frame, bg='white')
        buttons_frame.pack(fill="x", pady=(20, 0))
        
        novo_btn = self.create_button(buttons_frame, "Novo Técnico", self.novo_tecnico, bg='#e2e8f0', fg='#475569')
        novo_btn.pack(side="left", padx=(0, 10))
        
        salvar_btn = self.create_button(buttons_frame, "Salvar Técnico", self.salvar_tecnico)
        salvar_btn.pack(side="left")
        
    def create_lista_tecnicos_tab(self):
        lista_frame = tk.Frame(self.notebook, bg='white')
        self.notebook.add(lista_frame, text="Lista de Técnicos")
        
        container = tk.Frame(lista_frame, bg='white', padx=20, pady=20)
        container.pack(fill="both", expand=True)
        
        # Frame de busca
        search_frame, self.search_var = self.create_search_frame(container, command=self.buscar_tecnicos)
        search_frame.pack(fill="x", pady=(0, 15))
        
        # Treeview
        columns = ("nome", "especialidade", "telefone", "email")
        self.tecnicos_tree = ttk.Treeview(container, columns=columns, show="headings", height=15)
        
        self.tecnicos_tree.heading("nome", text="Nome")
        self.tecnicos_tree.heading("especialidade", text="Especialidade")
        self.tecnicos_tree.heading("telefone", text="Telefone")
        self.tecnicos_tree.heading("email", text="Email")
        
        self.tecnicos_tree.column("nome", width=200)
        self.tecnicos_tree.column("especialidade", width=150)
        self.tecnicos_tree.column("telefone", width=120)
        self.tecnicos_tree.column("email", width=200)
        
        # Scrollbar
        lista_scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.tecnicos_tree.yview)
        self.tecnicos_tree.configure(yscrollcommand=lista_scrollbar.set)
        
        self.tecnicos_tree.pack(side="left", fill="both", expand=True)
        lista_scrollbar.pack(side="right", fill="y")
        
        # Botões
        lista_buttons = tk.Frame(container, bg='white')
        lista_buttons.pack(fill="x", pady=(15, 0))
        
        editar_btn = self.create_button(lista_buttons, "Editar", self.editar_tecnico)
        editar_btn.pack(side="left", padx=(0, 10))
        
        excluir_btn = self.create_button(lista_buttons, "Excluir", self.excluir_tecnico, bg='#dc2626')
        excluir_btn.pack(side="left")
        
    def format_telefone(self, event=None):
        telefone = self.telefone_var.get()
        if telefone:
            self.telefone_var.set(format_phone(telefone))
            
    def novo_tecnico(self):
        self.current_tecnico_id = None
        self.nome_var.set("")
        self.especialidade_var.set("")
        self.telefone_var.set("")
        self.email_var.set("")
        
    def salvar_tecnico(self):
        nome = self.nome_var.get().strip()
        if not nome:
            self.show_warning("O nome é obrigatório.")
            return
            
        email = self.email_var.get().strip()
        if email and not validate_email(email):
            self.show_warning("Email inválido.")
            return
            
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        try:
            dados = (
                nome,
                self.especialidade_var.get().strip(),
                self.telefone_var.get().strip(),
                email if email else None
            )
            
            if self.current_tecnico_id:
                c.execute("""
                    UPDATE tecnicos SET nome = ?, especialidade = ?, telefone = ?, email = ?
                    WHERE id = ?
                """, dados + (self.current_tecnico_id,))
            else:
                c.execute("""
                    INSERT INTO tecnicos (nome, especialidade, telefone, email)
                    VALUES (?, ?, ?, ?)
                """, dados)
                self.current_tecnico_id = c.lastrowid
            
            conn.commit()
            self.show_success("Técnico salvo com sucesso!")
            
            # Emitir evento
            self.emit_event('tecnico_created')
            
            self.carregar_tecnicos()
            
        except sqlite3.Error as e:
            self.show_error(f"Erro ao salvar técnico: {e}")
        finally:
            conn.close()
            
    def carregar_tecnicos(self):
        for item in self.tecnicos_tree.get_children():
            self.tecnicos_tree.delete(item)
            
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        try:
            c.execute("""
                SELECT id, nome, especialidade, telefone, email
                FROM tecnicos
                ORDER BY nome
            """)
            
            for row in c.fetchall():
                tecnico_id, nome, especialidade, telefone, email = row
                self.tecnicos_tree.insert("", "end", values=(
                    nome,
                    especialidade or "",
                    format_phone(telefone) if telefone else "",
                    email or ""
                ), tags=(tecnico_id,))
                
        except sqlite3.Error as e:
            self.show_error(f"Erro ao carregar técnicos: {e}")
        finally:
            conn.close()
            
    def buscar_tecnicos(self):
        termo = self.search_var.get().strip()
        
        for item in self.tecnicos_tree.get_children():
            self.tecnicos_tree.delete(item)
            
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        try:
            if termo:
                c.execute("""
                    SELECT id, nome, especialidade, telefone, email
                    FROM tecnicos
                    WHERE nome LIKE ? OR especialidade LIKE ?
                    ORDER BY nome
                """, (f"%{termo}%", f"%{termo}%"))
            else:
                c.execute("""
                    SELECT id, nome, especialidade, telefone, email
                    FROM tecnicos
                    ORDER BY nome
                """)
            
            for row in c.fetchall():
                tecnico_id, nome, especialidade, telefone, email = row
                self.tecnicos_tree.insert("", "end", values=(
                    nome,
                    especialidade or "",
                    format_phone(telefone) if telefone else "",
                    email or ""
                ), tags=(tecnico_id,))
                
        except sqlite3.Error as e:
            self.show_error(f"Erro ao buscar técnicos: {e}")
        finally:
            conn.close()
            
    def editar_tecnico(self):
        selected = self.tecnicos_tree.selection()
        if not selected:
            self.show_warning("Selecione um técnico para editar.")
            return
            
        tags = self.tecnicos_tree.item(selected[0])['tags']
        if not tags:
            return
            
        tecnico_id = tags[0]
        self.carregar_tecnico_para_edicao(tecnico_id)
        self.notebook.select(0)
        
    def carregar_tecnico_para_edicao(self, tecnico_id):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        try:
            c.execute("SELECT * FROM tecnicos WHERE id = ?", (tecnico_id,))
            tecnico = c.fetchone()
            
            if not tecnico:
                self.show_error("Técnico não encontrado.")
                return
                
            self.current_tecnico_id = tecnico_id
            self.nome_var.set(tecnico[1] or "")  # nome
            self.especialidade_var.set(tecnico[2] or "")  # especialidade
            self.telefone_var.set(format_phone(tecnico[3]) if tecnico[3] else "")  # telefone
            self.email_var.set(tecnico[4] or "")  # email
            
        except sqlite3.Error as e:
            self.show_error(f"Erro ao carregar técnico: {e}")
        finally:
            conn.close()
            
    def excluir_tecnico(self):
        selected = self.tecnicos_tree.selection()
        if not selected:
            self.show_warning("Selecione um técnico para excluir.")
            return
            
        if not messagebox.askyesno("Confirmar Exclusão", 
                                   "Tem certeza que deseja excluir este técnico?"):
            return
            
        tags = self.tecnicos_tree.item(selected[0])['tags']
        if not tags:
            return
            
        tecnico_id = tags[0]
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        try:
            # Verificar se técnico tem eventos
            c.execute("SELECT COUNT(*) FROM eventos_campo WHERE tecnico_id = ?", (tecnico_id,))
            eventos_count = c.fetchone()[0]
            
            if eventos_count > 0:
                self.show_warning(f"Este técnico possui {eventos_count} eventos registrados.\n"
                                 "Não é possível excluir.")
                return
            
            c.execute("DELETE FROM tecnicos WHERE id = ?", (tecnico_id,))
            conn.commit()
            
            self.show_success("Técnico excluído com sucesso!")
            
            # Emitir evento
            self.emit_event('tecnico_deleted')
            
            self.carregar_tecnicos()
            
        except sqlite3.Error as e:
            self.show_error(f"Erro ao excluir técnico: {e}")
        finally:
            conn.close()