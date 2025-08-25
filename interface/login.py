import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import hashlib

from database import DB_NAME, criar_banco
from interface.main_window import MainWindow


class LoginWindow:
    def __init__(self, root):
        self.root = root

        # Garantir banco criado e usuário admin padrão
        try:
            criar_banco()
            self._ensure_default_admin()
        except Exception as e:
            print(f"Erro ao preparar banco de dados: {e}")

        # Janela de login como Toplevel
        self.window = tk.Toplevel(self.root)
        self.window.title("Login - CRM Compressores")
        self.window.configure(bg="#f8fafc")
        self.window.geometry("420x320")
        self.window.resizable(False, False)
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

        # Centralizar
        self.window.update_idletasks()
        w = self.window.winfo_width()
        h = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (w // 2)
        y = (self.window.winfo_screenheight() // 2) - (h // 2)
        self.window.geometry(f"{w}x{h}+{x}+{y}")

        # Variáveis
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()

        self._build_ui()

        # Foco inicial
        self.window.after(50, lambda: self.username_entry.focus_set())

    def _build_ui(self):
        container = tk.Frame(self.window, bg="#f8fafc")
        container.pack(fill="both", expand=True, padx=24, pady=24)

        title = tk.Label(
            container,
            text="Acesse o sistema",
            font=("Arial", 16, "bold"),
            bg="#f8fafc",
            fg="#1e293b",
        )
        title.pack(anchor="center", pady=(0, 16))

        form = tk.Frame(container, bg="#f8fafc")
        form.pack(fill="x")

        # Usuário
        tk.Label(form, text="Usuário", font=("Arial", 10), bg="#f8fafc").pack(
            anchor="w"
        )
        self.username_entry = tk.Entry(
            form, textvariable=self.username_var, font=("Arial", 11), relief="solid", bd=1
        )
        self.username_entry.pack(fill="x", ipady=6, pady=(2, 12))

        # Senha
        tk.Label(form, text="Senha", font=("Arial", 10), bg="#f8fafc").pack(anchor="w")
        self.password_entry = tk.Entry(
            form,
            textvariable=self.password_var,
            font=("Arial", 11),
            relief="solid",
            bd=1,
            show="*",
        )
        self.password_entry.pack(fill="x", ipady=6, pady=(2, 4))

        # Bind Enter
        self.window.bind("<Return>", lambda _e: self._attempt_login())

        # Ações
        actions = tk.Frame(container, bg="#f8fafc")
        actions.pack(fill="x", pady=(12, 0))

        login_btn = tk.Button(
            actions,
            text="Entrar",
            font=("Arial", 10),
            bg="#3b82f6",
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=8,
            command=self._attempt_login,
        )
        login_btn.pack(side="left")

        quick_btn = tk.Button(
            actions,
            text="Login rápido (admin)",
            font=("Arial", 10),
            bg="#10b981",
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=8,
            command=self._quick_login_admin,
        )
        quick_btn.pack(side="right")

        helper = tk.Label(
            container,
            text="Padrão: admin / admin123",
            font=("Arial", 9),
            bg="#f8fafc",
            fg="#64748b",
        )
        helper.pack(anchor="w", pady=(12, 0))

    def _on_close(self):
        try:
            # Encerrar toda a aplicação se fechar a tela de login
            self.root.destroy()
        except Exception:
            pass

    def _ensure_default_admin(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        try:
            c.execute("SELECT COUNT(*) FROM usuarios")
            count = c.fetchone()[0] or 0
            if count == 0:
                password_hash = hashlib.sha256("admin123".encode()).hexdigest()
                c.execute(
                    """
                    INSERT INTO usuarios (username, password, role, nome_completo, email)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    ("admin", password_hash, "admin", "Administrador", "admin@empresa.com"),
                )
                conn.commit()
                print("Usuário admin padrão criado: admin / admin123")
        finally:
            conn.close()

    def _attempt_login(self):
        username = (self.username_var.get() or "").strip()
        password = self.password_var.get() or ""

        if not username or not password:
            messagebox.showwarning("Login", "Informe usuário e senha.")
            return

        password_hash = hashlib.sha256(password.encode()).hexdigest()

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        try:
            c.execute(
                "SELECT id, role, COALESCE(nome_completo, username) FROM usuarios WHERE username = ? AND password = ?",
                (username, password_hash),
            )
            row = c.fetchone()
        finally:
            conn.close()

        if not row:
            messagebox.showerror("Login", "Usuário ou senha inválidos.")
            return

        user_id, role, nome_completo = row

        # Fechar janela de login e abrir a principal
        try:
            self.window.destroy()
        except Exception:
            pass

        MainWindow(self.root, user_id, role, nome_completo)

    def _quick_login_admin(self):
        self.username_var.set("admin")
        self.password_var.set("admin123")
        self._attempt_login()

