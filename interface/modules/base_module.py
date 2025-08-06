import tkinter as tk
from tkinter import ttk

class BaseModule:
    """Classe base para todos os módulos do sistema"""
    
    def __init__(self, parent, user_id, role, main_window):
        self.parent = parent
        self.user_id = user_id
        self.role = role
        self.main_window = main_window
        
        # Registrar para receber eventos
        if hasattr(main_window, 'register_listener'):
            main_window.register_listener(self.handle_event)
        
        # Frame principal do módulo
        self.frame = tk.Frame(parent, bg='#f8fafc')
        self.frame.pack(fill="both", expand=True)
        
        # Configurar UI específica do módulo
        self.setup_ui()
        
    def setup_ui(self):
        """Método a ser implementado pelos módulos filhos"""
        pass
        
    def handle_event(self, event_type, data=None):
        """Manipular eventos recebidos do sistema"""
        pass
        
    def emit_event(self, event_type, data=None):
        """Emitir evento para outros módulos"""
        if hasattr(self.main_window, 'emit_event'):
            self.main_window.emit_event(event_type, data)
    
    def create_section_frame(self, parent, title, padx=15, pady=15):
        """Criar frame de seção com título"""
        section_frame = tk.LabelFrame(parent, text=title, 
                                      font=('Arial', 12, 'bold'),
                                      bg='white',
                                      padx=padx, pady=pady)
        return section_frame
    
    def create_button(self, parent, text, command, bg='#3b82f6', fg='white', **kwargs):
        """Criar botão estilizado"""
        button = tk.Button(parent, 
                          text=text,
                          command=command,
                          font=('Arial', 10),
                          bg=bg,
                          fg=fg,
                          relief='flat',
                          cursor='hand2',
                          padx=15,
                          pady=8,
                          **kwargs)
        return button
    
    def create_search_frame(self, parent, placeholder="Buscar...", command=None):
        """Criar frame de busca padronizado"""
        search_frame = tk.Frame(parent, bg='white')
        
        search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, 
                               textvariable=search_var,
                               font=('Arial', 10),
                               relief='solid',
                               bd=1)
        search_entry.pack(side="left", fill="x", expand=True, ipady=5)
        
        if command:
            search_btn = self.create_button(search_frame, "🔍 Buscar", command)
            search_btn.pack(side="right", padx=(10, 0))
            
            # Bind Enter key
            search_entry.bind('<Return>', lambda e: command())
        
        return search_frame, search_var
    
    def show_success(self, message):
        """Mostrar mensagem de sucesso"""
        from tkinter import messagebox
        messagebox.showinfo("Sucesso", message)
        
    def show_error(self, message):
        """Mostrar mensagem de erro"""
        from tkinter import messagebox
        messagebox.showerror("Erro", message)
        
    def show_warning(self, message):
        """Mostrar mensagem de aviso"""
        from tkinter import messagebox
        messagebox.showwarning("Aviso", message)
        
    def show_info(self, title, message):
        """Mostrar mensagem informativa"""
        from tkinter import messagebox
        messagebox.showinfo(title, message)