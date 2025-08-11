import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import hashlib
from .base_module import BaseModule
from database import DB_NAME
from utils.formatters import format_phone, validate_email

class UsuariosModule(BaseModule):
    def setup_ui(self):
        container = tk.Frame(self.frame, bg='#f8fafc')
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        self.create_header(container)
        
        # Notebook
        self.notebook = ttk.Notebook(container)
        self.notebook.pack(fill="both", expand=True, pady=(20, 0))
        
        # Abas
        self.create_novo_usuario_tab()
        self.create_lista_usuarios_tab()
        
        self.current_usuario_id = None
        self.carregar_usuarios()
        
    def create_header(self, parent):
        header_frame = tk.Frame(parent, bg='#f8fafc')
        header_frame.pack(fill="x", pady=(0, 20))
        
        title_label = tk.Label(header_frame, text="Gestão de Usuários", 
                               font=('Arial', 18, 'bold'), bg='#f8fafc', fg='#1e293b')
        title_label.pack(side="left")
        
    def create_novo_usuario_tab(self):
        usuario_frame = tk.Frame(self.notebook, bg='white')
        self.notebook.add(usuario_frame, text="Novo Usuário")
        
        content_frame = tk.Frame(usuario_frame, bg='white', padx=20, pady=20)
        content_frame.pack(fill="both", expand=True)
        
        # Seção principal
        section_frame = self.create_section_frame(content_frame, "Dados do Usuário")
        section_frame.pack(fill="x", pady=(0, 15))
        
        fields_frame = tk.Frame(section_frame, bg='white')
        fields_frame.pack(fill="x")
        
        # Variáveis
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.confirm_password_var = tk.StringVar()
        self.role_var = tk.StringVar(value="operador")
        self.role_admin_var = tk.BooleanVar(value=False)
        self.role_operador_var = tk.BooleanVar(value=True)
        self.role_tecnico_var = tk.BooleanVar(value=False)
        self.nome_completo_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.telefone_var = tk.StringVar()
        self.template_personalizado_var = tk.BooleanVar()
        self.template_image_path_var = tk.StringVar()
        
        row = 0
        
        # Username
        tk.Label(fields_frame, text="Username *:", font=('Arial', 10, 'bold'), bg='white').grid(row=row, column=0, sticky="w", pady=5)
        tk.Entry(fields_frame, textvariable=self.username_var, font=('Arial', 10), width=30).grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        row += 1
        
        # Password
        tk.Label(fields_frame, text="Senha *:", font=('Arial', 10, 'bold'), bg='white').grid(row=row, column=0, sticky="w", pady=5)
        tk.Entry(fields_frame, textvariable=self.password_var, font=('Arial', 10), width=30, show="*").grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        row += 1
        
        # Confirm Password
        tk.Label(fields_frame, text="Confirmar Senha *:", font=('Arial', 10, 'bold'), bg='white').grid(row=row, column=0, sticky="w", pady=5)
        tk.Entry(fields_frame, textvariable=self.confirm_password_var, font=('Arial', 10), width=30, show="*").grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        row += 1
        
        # Roles (múltiplos)
        tk.Label(fields_frame, text="Perfis *:", font=('Arial', 10, 'bold'), bg='white').grid(row=row, column=0, sticky="nw", pady=5)
        roles_frame = tk.Frame(fields_frame, bg='white')
        roles_frame.grid(row=row, column=1, sticky="w", padx=(10, 0), pady=5)
        tk.Checkbutton(roles_frame, text="Admin", variable=self.role_admin_var, bg='white').pack(side='left', padx=(0, 10))
        tk.Checkbutton(roles_frame, text="Operador", variable=self.role_operador_var, bg='white').pack(side='left', padx=(0, 10))
        tk.Checkbutton(roles_frame, text="Técnico", variable=self.role_tecnico_var, bg='white').pack(side='left', padx=(0, 10))
        row += 1
        
        # Nome Completo
        tk.Label(fields_frame, text="Nome Completo:", font=('Arial', 10, 'bold'), bg='white').grid(row=row, column=0, sticky="w", pady=5)
        tk.Entry(fields_frame, textvariable=self.nome_completo_var, font=('Arial', 10), width=30).grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        row += 1
        
        # Email
        tk.Label(fields_frame, text="Email:", font=('Arial', 10, 'bold'), bg='white').grid(row=row, column=0, sticky="w", pady=5)
        tk.Entry(fields_frame, textvariable=self.email_var, font=('Arial', 10), width=30).grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        row += 1
        
        # Telefone
        tk.Label(fields_frame, text="Telefone:", font=('Arial', 10, 'bold'), bg='white').grid(row=row, column=0, sticky="w", pady=5)
        telefone_entry = tk.Entry(fields_frame, textvariable=self.telefone_var, font=('Arial', 10), width=30)
        telefone_entry.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        telefone_entry.bind('<FocusOut>', self.format_telefone)
        row += 1
        
        # Template Personalizado
        tk.Label(fields_frame, text="Template Personalizado:", font=('Arial', 10, 'bold'), bg='white').grid(row=row, column=0, sticky="w", pady=5)
        template_frame = tk.Frame(fields_frame, bg='white')
        template_frame.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        
        template_check = tk.Checkbutton(template_frame, text="Ativar template personalizado para PDFs", 
                                       variable=self.template_personalizado_var, bg='white', font=('Arial', 10),
                                       command=self.toggle_template_upload)
        template_check.pack(anchor="w")
        
        # Frame para upload de imagem
        self.upload_frame = tk.Frame(template_frame, bg='white')
        self.upload_frame.pack(fill="x", pady=(5, 0))
        
        tk.Label(self.upload_frame, text="Imagem do Template:", font=('Arial', 9), bg='white').pack(anchor="w")
        
        upload_controls = tk.Frame(self.upload_frame, bg='white')
        upload_controls.pack(fill="x")
        
        self.template_path_entry = tk.Entry(upload_controls, textvariable=self.template_image_path_var, 
                                           font=('Arial', 9), width=40, state='readonly')
        self.template_path_entry.pack(side="left", fill="x", expand=True)
        
        self.browse_btn = tk.Button(upload_controls, text="📁 Procurar", command=self.browse_template_image,
                                   bg='#3b82f6', fg='white', font=('Arial', 8))
        self.browse_btn.pack(side="right", padx=(5, 0))
        
        # Inicialmente oculto
        self.upload_frame.pack_forget()
        
        fields_frame.grid_columnconfigure(1, weight=1)
        
        # Botões
        buttons_frame = tk.Frame(content_frame, bg='white')
        buttons_frame.pack(fill="x", pady=(20, 0))
        
        novo_btn = self.create_button(buttons_frame, "Novo Usuário", self.novo_usuario, bg='#e2e8f0', fg='#475569')
        novo_btn.pack(side="left", padx=(0, 10))
        
        salvar_btn = self.create_button(buttons_frame, "Salvar Usuário", self.salvar_usuario)
        salvar_btn.pack(side="left")
        
    def create_lista_usuarios_tab(self):
        lista_frame = tk.Frame(self.notebook, bg='white')
        self.notebook.add(lista_frame, text="Lista de Usuários")
        
        container = tk.Frame(lista_frame, bg='white', padx=20, pady=20)
        container.pack(fill="both", expand=True)
        
        # Frame de busca
        search_frame, self.search_var = self.create_search_frame(container, command=self.buscar_usuarios)
        search_frame.pack(fill="x", pady=(0, 15))
        
        # Treeview
        columns = ("username", "nome_completo", "role", "email", "telefone")
        self.usuarios_tree = ttk.Treeview(container, columns=columns, show="headings", height=15)
        
        self.usuarios_tree.heading("username", text="Username")
        self.usuarios_tree.heading("nome_completo", text="Nome Completo")
        self.usuarios_tree.heading("role", text="Perfil")
        self.usuarios_tree.heading("email", text="Email")
        self.usuarios_tree.heading("telefone", text="Telefone")
        
        self.usuarios_tree.column("username", width=120)
        self.usuarios_tree.column("nome_completo", width=200)
        self.usuarios_tree.column("role", width=150)
        self.usuarios_tree.column("email", width=200)
        self.usuarios_tree.column("telefone", width=120)
        
        # Scrollbar
        lista_scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.usuarios_tree.yview)
        self.usuarios_tree.configure(yscrollcommand=lista_scrollbar.set)
        
        self.usuarios_tree.pack(side="left", fill="both", expand=True)
        lista_scrollbar.pack(side="right", fill="y")
        
        # Botões
        lista_buttons = tk.Frame(container, bg='white')
        lista_buttons.pack(fill="x", pady=(15, 0))
        
        editar_btn = self.create_button(lista_buttons, "Editar", self.editar_usuario)
        editar_btn.pack(side="left", padx=(0, 10))
        
        resetar_btn = self.create_button(lista_buttons, "Resetar Senha", self.resetar_senha, bg='#f59e0b')
        resetar_btn.pack(side="left", padx=(0, 10))
        
        excluir_btn = self.create_button(lista_buttons, "Excluir", self.excluir_usuario, bg='#dc2626')
        excluir_btn.pack(side="left")
        
    def format_telefone(self, event=None):
        telefone = self.telefone_var.get()
        if telefone:
            self.telefone_var.set(format_phone(telefone))
            
    def novo_usuario(self):
        self.current_usuario_id = None
        self.username_var.set("")
        self.password_var.set("")
        self.confirm_password_var.set("")
        # Papéis padrão: operador marcado
        self.role_admin_var.set(False)
        self.role_operador_var.set(True)
        self.role_tecnico_var.set(False)
        self.role_var.set("operador")
        self.nome_completo_var.set("")
        self.email_var.set("")
        self.telefone_var.set("")
        self.template_personalizado_var.set(False)
        self.template_image_path_var.set("")
        self.upload_frame.pack_forget()
        
    def _construir_roles_string(self) -> str:
        roles = []
        if self.role_admin_var.get():
            roles.append('admin')
        if self.role_operador_var.get():
            roles.append('operador')
        if self.role_tecnico_var.get():
            roles.append('tecnico')
        if not roles:
            roles = ['operador']
        return ','.join(roles)
        
    def salvar_usuario(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()
        confirm_password = self.confirm_password_var.get()
        role = self._construir_roles_string()
        
        if not username:
            self.show_warning("O username é obrigatório.")
            return
            
        if not self.current_usuario_id:  # Novo usuário
            if not password:
                self.show_warning("A senha é obrigatória.")
                return
                
            if password != confirm_password:
                self.show_warning("As senhas não coincidem.")
                return
                
            if len(password) < 6:
                self.show_warning("A senha deve ter pelo menos 6 caracteres.")
                return
                
        email = self.email_var.get().strip()
        if email and not validate_email(email):
            self.show_warning("Email inválido.")
            return
            
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        try:
            if self.current_usuario_id:
                # Atualizar usuário existente (sem senha)
                c.execute("""
                    UPDATE usuarios SET username = ?, role = ?, nome_completo = ?, 
                                      email = ?, telefone = ?, template_personalizado = ?, template_image_path = ?
                    WHERE id = ?
                """, (username, role, self.nome_completo_var.get().strip(),
                     email if email else None, self.telefone_var.get().strip(),
                     self.template_personalizado_var.get(), self.template_image_path_var.get().strip() or None,
                     self.current_usuario_id))
            else:
                # Novo usuário
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                c.execute("""
                    INSERT INTO usuarios (username, password, role, nome_completo, email, telefone, template_personalizado, template_image_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (username, password_hash, role, self.nome_completo_var.get().strip(),
                     email if email else None, self.telefone_var.get().strip(), 
                     self.template_personalizado_var.get(), self.template_image_path_var.get().strip() or None))
                self.current_usuario_id = c.lastrowid
            
            conn.commit()
            self.show_success("Usuário salvo com sucesso!")
            
            self.carregar_usuarios()
            
        except sqlite3.IntegrityError as e:
            self.show_error(f"Erro ao salvar usuário: {e}")
        finally:
            conn.close()
            
    def carregar_usuarios(self):
        for item in self.usuarios_tree.get_children():
            self.usuarios_tree.delete(item)
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        try:
            termo = self.search_var.get().strip() if hasattr(self, 'search_var') else ''
            if termo:
                c.execute("""
                    SELECT id, username, nome_completo, role, email, telefone
                    FROM usuarios
                    WHERE username LIKE ? OR nome_completo LIKE ?
                    ORDER BY username
                """, (f"%{termo}%", f"%{termo}%"))
            else:
                c.execute("""
                    SELECT id, username, nome_completo, role, email, telefone
                    FROM usuarios
                    ORDER BY username
                """)
            
            for row in c.fetchall():
                usuario_id, username, nome_completo, role, email, telefone = row
                self.usuarios_tree.insert("", "end", values=(
                    username,
                    nome_completo or "",
                    role,
                    email or "",
                    format_phone(telefone) if telefone else ""
                ), tags=(usuario_id,))
                
        except sqlite3.Error as e:
            self.show_error(f"Erro ao buscar usuários: {e}")
        finally:
            conn.close()
            
    def buscar_usuarios(self):
        termo = self.search_var.get().strip()
        
        for item in self.usuarios_tree.get_children():
            self.usuarios_tree.delete(item)
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        try:
            if termo:
                c.execute("""
                    SELECT id, username, nome_completo, role, email, telefone
                    FROM usuarios
                    WHERE username LIKE ? OR nome_completo LIKE ?
                    ORDER BY username
                """, (f"%{termo}%", f"%{termo}%"))
            else:
                c.execute("""
                    SELECT id, username, nome_completo, role, email, telefone
                    FROM usuarios
                    ORDER BY username
                """)
            
            for row in c.fetchall():
                usuario_id, username, nome_completo, role, email, telefone = row
                self.usuarios_tree.insert("", "end", values=(
                    username,
                    nome_completo or "",
                    role,
                    email or "",
                    format_phone(telefone) if telefone else ""
                ), tags=(usuario_id,))
                
        except sqlite3.Error as e:
            self.show_error(f"Erro ao buscar usuários: {e}")
        finally:
            conn.close()
            
    def editar_usuario(self):
        selected = self.usuarios_tree.selection()
        if not selected:
            self.show_warning("Selecione um usuário para editar.")
            return
            
        tags = self.usuarios_tree.item(selected[0])['tags']
        if not tags:
            return
            
        usuario_id = tags[0]
        self.carregar_usuario_para_edicao(usuario_id)
        self.notebook.select(0)
        
    def carregar_usuario_para_edicao(self, usuario_id):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        try:
            c.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
            usuario = c.fetchone()
            
            if not usuario:
                self.show_error("Usuário não encontrado.")
                return
                
            self.current_usuario_id = usuario_id
            self.username_var.set(usuario[1] or "")  # username
            self.password_var.set("")  # Não mostrar senha
            self.confirm_password_var.set("")
            role_str = usuario[3] or "operador"
            self.role_var.set(role_str)
            roles = set([r.strip().lower() for r in role_str.split(',') if r.strip()])
            self.role_admin_var.set('admin' in roles)
            self.role_operador_var.set('operador' in roles)
            self.role_tecnico_var.set('tecnico' in roles)
            self.nome_completo_var.set(usuario[4] or "")  # nome_completo
            self.email_var.set(usuario[5] or "")  # email
            self.telefone_var.set(format_phone(usuario[6]) if usuario[6] else "")  # telefone
            # template_personalizado está na posição 7 (após telefone)
            self.template_personalizado_var.set(bool(usuario[7]) if len(usuario) > 7 and usuario[7] is not None else False)
            # template_image_path está na posição 8
            self.template_image_path_var.set(usuario[8] if len(usuario) > 8 and usuario[8] else "")
            
            # Mostrar/ocultar upload baseado no checkbox
            self.toggle_template_upload()
            
        except sqlite3.Error as e:
            self.show_error(f"Erro ao carregar usuário: {e}")
        finally:
            conn.close()
        
    def resetar_senha(self):
        selected = self.usuarios_tree.selection()
        if not selected:
            self.show_warning("Selecione um usuário para resetar a senha.")
            return
            
        if not messagebox.askyesno("Confirmar Reset", 
                                   "Tem certeza que deseja resetar a senha para '123456'?"):
            return
            
        tags = self.usuarios_tree.item(selected[0])['tags']
        if not tags:
            return
            
        usuario_id = tags[0]
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        try:
            nova_senha = "123456"
            password_hash = hashlib.sha256(nova_senha.encode()).hexdigest()
            
            c.execute("UPDATE usuarios SET password = ? WHERE id = ?", (password_hash, usuario_id))
            conn.commit()
            
            self.show_success(f"Senha resetada para '{nova_senha}' com sucesso!")
            
        except sqlite3.Error as e:
            self.show_error(f"Erro ao resetar senha: {e}")
        finally:
            conn.close()
        
    def excluir_usuario(self):
        selected = self.usuarios_tree.selection()
        if not selected:
            self.show_warning("Selecione um usuário para excluir.")
            return
            
        if not messagebox.askyesno("Confirmar Exclusão", 
                                   "Tem certeza que deseja excluir este usuário?"):
            return
            
        tags = self.usuarios_tree.item(selected[0])['tags']
        if not tags:
            return
            
        usuario_id = tags[0]
        
        # Não permitir excluir o próprio usuário
        if usuario_id == self.user_id:
            self.show_warning("Você não pode excluir seu próprio usuário.")
            return
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        try:
            # Verificar se usuário tem cotações ou relatórios
            c.execute("SELECT COUNT(*) FROM cotacoes WHERE responsavel_id = ?", (usuario_id,))
            cotacoes_count = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM relatorios_tecnicos WHERE responsavel_id = ?", (usuario_id,))
            relatorios_count = c.fetchone()[0]
            
            if cotacoes_count > 0 or relatorios_count > 0:
                self.show_warning(f"Este usuário possui {cotacoes_count} cotações e {relatorios_count} relatórios.\n"
                                 "Não é possível excluir.")
                return
            
            c.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
            conn.commit()
            
            self.show_success("Usuário excluído com sucesso!")
            
            self.carregar_usuarios()
            
        except sqlite3.Error as e:
            self.show_error(f"Erro ao excluir usuário: {e}")
        finally:
            conn.close()    
    def toggle_template_upload(self):
        """Mostrar/ocultar campo de upload quando checkbox é marcado"""
        if self.template_personalizado_var.get():
            self.upload_frame.pack(fill="x", pady=(5, 0))
        else:
            self.upload_frame.pack_forget()
            self.template_image_path_var.set("")
    
    def browse_template_image(self):
        """Procurar arquivo de imagem para template"""
        from tkinter import filedialog
        
        filetypes = [
            ("Imagens", "*.jpg *.jpeg *.png *.bmp *.gif"),
            ("JPEG", "*.jpg *.jpeg"),
            ("PNG", "*.png"),
            ("Todos os arquivos", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Selecionar Imagem do Template",
            filetypes=filetypes
        )
        
        if filename:
            self.template_image_path_var.set(filename)
