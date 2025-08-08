import tkinter as tk
from tkinter import messagebox
import sqlite3
import hashlib
import os

# Nome do banco - igual ao seu database.py
DB_NAME = "crm_compressores.db"

def criar_banco_se_necessario():
    """Cria o banco e usuário admin se não existir"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Criar tabela usuarios se não existir
        c.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'operador',
                nome_completo TEXT,
                email TEXT,
                telefone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Verificar se admin existe
        c.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'admin'")
        if c.fetchone()[0] == 0:
            # Criar usuário admin
            admin_password = hashlib.sha256("admin123".encode()).hexdigest()
            c.execute('''
                INSERT INTO usuarios (username, password, role, nome_completo, email)
                VALUES (?, ?, ?, ?, ?)
            ''', ("admin", admin_password, "admin", "Administrador", "admin@empresa.com"))
            print("✅ Usuário admin criado: admin/admin123")
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"❌ Erro no banco: {e}")
        return False
    finally:
        conn.close()

class LoginWindow:
    def __init__(self, root=None):
        # Criar banco se necessário
        if not criar_banco_se_necessario():
            messagebox.showerror("Erro", "Erro ao inicializar banco de dados!")
            return
            
        # Criar janela principal se não foi passada
        if root is None:
            self.root = tk.Tk()
            self.root.withdraw()
        else:
            self.root = root
            
        # Criar janela de login
        self.login_window = tk.Toplevel(self.root)
        self.configurar_janela()
        self.criar_interface()
        self.centralizar_janela()
        
    def configurar_janela(self):
        """Configurar a janela de login"""
        self.login_window.title("Login - Sistema CRM Compressores")
        self.login_window.geometry("400x450")
        self.login_window.resizable(False, False)
        self.login_window.configure(bg='#f8fafc')
        self.login_window.protocol("WM_DELETE_WINDOW", self.fechar_aplicacao)
        
        # Focar na janela
        self.login_window.lift()
        self.login_window.focus_force()
        self.login_window.grab_set()
        
    def centralizar_janela(self):
        """Centralizar janela na tela"""
        self.login_window.update_idletasks()
        width = 400
        height = 450
        x = (self.login_window.winfo_screenwidth() - width) // 2
        y = (self.login_window.winfo_screenheight() - height) // 2
        self.login_window.geometry(f'{width}x{height}+{x}+{y}')
        
    def criar_interface(self):
        """Criar interface de login"""
        # Container principal
        main_frame = tk.Frame(self.login_window, bg='#f8fafc')
        main_frame.pack(fill="both", expand=True, padx=40, pady=40)
        
        # Título
        titulo = tk.Label(
            main_frame, 
            text="Sistema CRM\nCompressores", 
            font=('Arial', 18, 'bold'),
            bg='#f8fafc',
            fg='#1e293b',
            justify='center'
        )
        titulo.pack(pady=(0, 30))
        
        # Campo usuário
        tk.Label(main_frame, text="Usuário:", font=('Arial', 10, 'bold'),
                bg='#f8fafc', fg='#374151').pack(anchor="w", pady=(0, 5))
        
        self.usuario_var = tk.StringVar()
        self.usuario_entry = tk.Entry(
            main_frame, 
            textvariable=self.usuario_var,
            font=('Arial', 11),
            relief='solid',
            bd=1
        )
        self.usuario_entry.pack(fill="x", ipady=8, pady=(0, 15))
        
        # Campo senha
        tk.Label(main_frame, text="Senha:", font=('Arial', 10, 'bold'),
                bg='#f8fafc', fg='#374151').pack(anchor="w", pady=(0, 5))
        
        self.senha_var = tk.StringVar()
        self.senha_entry = tk.Entry(
            main_frame, 
            textvariable=self.senha_var,
            font=('Arial', 11),
            relief='solid',
            bd=1,
            show="*"
        )
        self.senha_entry.pack(fill="x", ipady=8, pady=(0, 20))
        
        # Botão entrar
        btn_entrar = tk.Button(
            main_frame, 
            text="Entrar",
            font=('Arial', 11, 'bold'),
            bg='#3b82f6',
            fg='white',
            relief='flat',
            cursor='hand2',
            command=self.fazer_login
        )
        btn_entrar.pack(fill="x", ipady=10, pady=(0, 20))
        
        # Enter para login
        self.login_window.bind('<Return>', lambda e: self.fazer_login())
        
        # Informações de teste
        info_frame = tk.Frame(main_frame, bg='#e0f2fe', relief='solid', bd=1)
        info_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(info_frame, text="🔑 Login de Teste", 
                font=('Arial', 10, 'bold'), bg='#e0f2fe', fg='#0277bd').pack(pady=(10, 5))
        tk.Label(info_frame, text="Usuário: admin\nSenha: admin123", 
                font=('Arial', 9), bg='#e0f2fe', fg='#01579b').pack(pady=(0, 10))
        
        # Botão preencher teste
        btn_teste = tk.Button(
            main_frame, 
            text="Preencher Login de Teste",
            font=('Arial', 9),
            bg='#e5e7eb',
            fg='#374151',
            command=self.preencher_teste
        )
        btn_teste.pack(pady=(0, 10))
        
        # Status
        self.status_label = tk.Label(main_frame, text="", font=('Arial', 9),
                                   bg='#f8fafc', fg='#ef4444')
        self.status_label.pack()
        
        # Focar no campo usuário
        self.login_window.after(200, lambda: self.usuario_entry.focus())
        
    def preencher_teste(self):
        """Preencher com dados de teste"""
        self.usuario_var.set("admin")
        self.senha_var.set("admin123")
        self.status_label.config(text="✅ Dados de teste preenchidos", fg='#10b981')
        
    def fazer_login(self):
        """Processar login"""
        usuario = self.usuario_var.get().strip()
        senha = self.senha_var.get().strip()
        
        if not usuario or not senha:
            self.status_label.config(text="❌ Preencha todos os campos!", fg='#ef4444')
            messagebox.showerror("Erro", "Preencha todos os campos!")
            return
            
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            
            # Verificar credenciais
            senha_hash = hashlib.sha256(senha.encode()).hexdigest()
            c.execute(
                "SELECT id, role, nome_completo FROM usuarios WHERE username=? AND password=?", 
                (usuario, senha_hash)
            )
            user = c.fetchone()
            
            if user:
                user_id, role, nome_completo = user
                self.status_label.config(text="✅ Login realizado!", fg='#10b981')
                
                messagebox.showinfo("Sucesso", f"Bem-vindo, {nome_completo}!")
                
                # Tentar abrir a janela principal; só destruir o login após sucesso
                try:
                    self.abrir_sistema_principal(user_id, role, nome_completo)
                except Exception as e:
                    # Em caso de falha ao abrir o sistema, manter a janela de login e exibir erro
                    if self.status_label and self.status_label.winfo_exists():
                        self.status_label.config(text="❌ Erro ao abrir o sistema", fg='#ef4444')
                    messagebox.showerror("Erro", f"Erro ao abrir o sistema: {e}")
                    return
                
                # Se chegou aqui, o sistema abriu com sucesso: destruir janela de login
                if self.login_window and self.login_window.winfo_exists():
                    self.login_window.destroy()
                
                # Encerrar processamento após sucesso
                return
            else:
                self.status_label.config(text="❌ Usuário ou senha incorretos!", fg='#ef4444')
                messagebox.showerror("Erro", "Usuário ou senha incorretos!")
                self.senha_var.set("")
                self.senha_entry.focus()
                
        except Exception as e:
            self.status_label.config(text="❌ Erro no banco de dados", fg='#ef4444')
            messagebox.showerror("Erro", f"Erro no banco: {e}")
        finally:
            conn.close()
            
    def abrir_sistema_principal(self, user_id, role, nome_completo):
        """Abrir sistema principal"""
        try:
            # Tentar importar sua janela principal
            from interface.main_window import MainWindow
            MainWindow(self.root, user_id, role, nome_completo)
        except ImportError:
            # Se não conseguir importar, mostrar janela simples
            self.criar_janela_principal_simples(user_id, role, nome_completo)
            
    def criar_janela_principal_simples(self, user_id, role, nome_completo):
        """Criar janela principal simples se a original não funcionar"""
        self.root.deiconify()
        self.root.title(f"Sistema CRM - {nome_completo}")
        self.root.geometry("800x600")
        self.root.configure(bg='#f8fafc')
        
        # Limpar janela
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # Cabeçalho
        header = tk.Frame(self.root, bg='#1e293b', height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(header, text="Sistema CRM Compressores", 
                font=('Arial', 16, 'bold'), bg='#1e293b', fg='white').pack(side="left", padx=20, pady=15)
        
        # Botão logout
        tk.Button(header, text="Logout", bg='#ef4444', fg='white',
                 command=self.logout).pack(side="right", padx=20, pady=15)
        
        # Conteúdo
        content = tk.Frame(self.root, bg='#f8fafc')
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(content, text=f"Bem-vindo, {nome_completo}!", 
                font=('Arial', 18, 'bold'), bg='#f8fafc').pack(pady=50)
        
        tk.Label(content, text=f"Usuário: {nome_completo}\nPerfil: {role}\nID: {user_id}", 
                font=('Arial', 12), bg='#f8fafc').pack()
        
    def logout(self):
        """Fazer logout"""
        if messagebox.askyesno("Logout", "Deseja sair?"):
            self.root.withdraw()
            LoginWindow(self.root)
            
    def fechar_aplicacao(self):
        """Fechar aplicação"""
        self.root.quit()
        
    def executar(self):
        """Executar aplicação"""
        self.root.mainloop()

# Para testar diretamente
if __name__ == "__main__":
    print("🚀 Iniciando Sistema CRM...")
    app = LoginWindow()
    app.executar()
