import tkinter as tk
from tkinter import ttk, messagebox
from interface.modules import CotacoesModule, RelatoriosModule, ClientesModule, ProdutosModule, UsuariosModule, DashboardModule, PermissoesModule, ConsultasModule, LocacaoModule

class MainWindow:
    def __init__(self, root, user_id, role, nome_completo):
        self.root = root
        self.user_id = user_id
        self.role = role
        self.nome_completo = nome_completo
        
        # Sistema de eventos para comunicação entre módulos
        self.event_listeners = []
        
        self.setup_main_window()
        self.create_main_ui()
        
        # Mostrar janela principal
        self.root.deiconify()
        
    def setup_main_window(self):
        """Configurar janela principal"""
        self.root.title(f"Sistema CRM Compressores - {self.nome_completo} ({self.role})")
        self.root.geometry("1400x800")
        self.root.configure(bg='#f8fafc')
        
        # Centralizar janela
        self.center_window()
        
    def center_window(self):
        """Centralizar a janela na tela"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def has_role(self, role_name: str) -> bool:
        """Verifica se o usuário possui o perfil informado (suporta múltiplos perfis separados por vírgula)."""
        try:
            roles = [r.strip().lower() for r in (self.role or '').split(',') if r.strip()]
            return role_name.lower() in roles
        except Exception:
            return self.role == role_name
        
    def register_listener(self, listener_func):
        """Registrar um listener para eventos do sistema"""
        self.event_listeners.append(listener_func)
        
    def emit_event(self, event_type, data=None):
        """Emitir um evento para todos os listeners"""
        for listener in self.event_listeners:
            try:
                listener(event_type, data)
            except Exception as e:
                print(f"Erro ao processar evento {event_type}: {e}")
        
    def create_main_ui(self):
        # Frame superior com menu
        self.create_header()
        
        # Notebook para abas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Criar módulos
        self.create_modules()
        
    def create_header(self):
        """Criar cabeçalho com informações do usuário e botões"""
        header_frame = tk.Frame(self.root, bg='#1e293b', height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        # Frame esquerdo - título
        left_frame = tk.Frame(header_frame, bg='#1e293b')
        left_frame.pack(side="left", fill="y", padx=20, pady=10)
        
        title_label = tk.Label(left_frame, 
                              text="Sistema CRM Compressores",
                              font=('Arial', 16, 'bold'),
                              bg='#1e293b',
                              fg='white')
        title_label.pack(anchor="w")
        
        # Frame direito - informações do usuário e logout
        right_frame = tk.Frame(header_frame, bg='#1e293b')
        right_frame.pack(side="right", fill="y", padx=20, pady=10)
        
        user_label = tk.Label(right_frame,
                             text=f"Usuário: {self.nome_completo} ({self.role})",
                             font=('Arial', 10),
                             bg='#1e293b',
                             fg='#e2e8f0')
        user_label.pack(anchor="e")
        
        logout_btn = tk.Button(right_frame,
                              text="Logout",
                              font=('Arial', 9),
                              bg='#ef4444',
                              fg='white',
                              relief='flat',
                              cursor='hand2',
                              command=self.logout)
        logout_btn.pack(anchor="e", pady=(5, 0))
        
    def create_modules(self):
        """Criar todos os módulos do sistema"""
        
        # Dashboard
        dashboard_frame = tk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="📊 Dashboard")
        self.dashboard_module = DashboardModule(dashboard_frame, self.user_id, self.role, self)
        
        # Clientes
        clientes_frame = tk.Frame(self.notebook)
        self.notebook.add(clientes_frame, text="👥 Clientes")
        self.clientes_module = ClientesModule(clientes_frame, self.user_id, self.role, self)
        
        # Produtos
        produtos_frame = tk.Frame(self.notebook)
        self.notebook.add(produtos_frame, text="📦 Produtos")
        self.produtos_module = ProdutosModule(produtos_frame, self.user_id, self.role, self)
        
        # Cotações
        cotacoes_frame = tk.Frame(self.notebook)
        self.notebook.add(cotacoes_frame, text="💰 Cotações")
        self.cotacoes_module = CotacoesModule(cotacoes_frame, self.user_id, self.role, self)
        
        # Locação
        locacao_frame = tk.Frame(self.notebook)
        self.notebook.add(locacao_frame, text="📝 Locação")
        self.locacao_module = LocacaoModule(locacao_frame, self.user_id, self.role, self)

        # Relatórios Técnicos
        relatorios_frame = tk.Frame(self.notebook)
        self.notebook.add(relatorios_frame, text="📋 Relatórios")
        self.relatorios_module = RelatoriosModule(relatorios_frame, self.user_id, self.role, self)
        
        # Consultas Avançadas
        consultas_frame = tk.Frame(self.notebook)
        self.notebook.add(consultas_frame, text="🔍 Consultas")
        self.consultas_module = ConsultasModule(consultas_frame, self.user_id, self.role, self)
        
        # Usuários e Permissões (apenas para admins)
        if self.has_role('admin'):
            usuarios_frame = tk.Frame(self.notebook)
            self.notebook.add(usuarios_frame, text="👤 Usuários")
            self.usuarios_module = UsuariosModule(usuarios_frame, self.user_id, self.role, self)
            
            permissoes_frame = tk.Frame(self.notebook)
            self.notebook.add(permissoes_frame, text="🔐 Permissões")
            self.permissoes_module = PermissoesModule(permissoes_frame, self.user_id, self.role, self)
        
    def logout(self):
        """Fazer logout e voltar para tela de login"""
        if messagebox.askyesno("Logout", "Tem certeza que deseja sair?"):
            self.root.withdraw()
            
            # Criar nova janela de login
            from interface.login import LoginWindow
            LoginWindow(self.root)