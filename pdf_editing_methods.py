"""
Métodos para edição funcional de PDF
"""
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
import sqlite3


def create_quick_edit_panel(self, parent):
    """Criar painel de edições rápidas"""
    try:
        # Frame para edições
        edit_frame = tk.LabelFrame(parent, text="🛠️ Edições Rápidas", 
                                 font=('Arial', 10, 'bold'),
                                 bg='#f8fafc', padx=10, pady=10)
        edit_frame.pack(fill="x", pady=10)
        
        # Botões principais
        btn_frame = tk.Frame(edit_frame)
        btn_frame.pack(fill="x", padx=5, pady=5)
        
        tk.Button(btn_frame, text="📝 Editar Textos",
                 command=self.open_text_editor,
                 bg='#3b82f6', fg='white').pack(side="left", padx=2)
        
        tk.Button(btn_frame, text="🎨 Gerenciar Capas",
                 command=self.open_cover_manager,
                 bg='#f59e0b', fg='white').pack(side="left", padx=2)
        
        tk.Button(btn_frame, text="🔄 Atualizar Preview",
                 command=self.refresh_pdf_preview,
                 bg='#10b981', fg='white').pack(side="left", padx=2)
        
    except Exception as e:
        print(f"Erro ao criar painel de edições: {e}")


def open_text_editor(self):
    """Abrir editor de textos em janela separada"""
    try:
        if hasattr(self, 'text_editor_window') and self.text_editor_window.winfo_exists():
            self.text_editor_window.lift()
            return
        
        # Criar janela do editor
        self.text_editor_window = tk.Toplevel(self.frame)
        self.text_editor_window.title("Editor de Textos PDF")
        self.text_editor_window.geometry("500x400")
        self.text_editor_window.configure(bg='#f8fafc')
        
        # Campos de edição
        fields = [
            ("nome_empresa", "Nome da Empresa"),
            ("endereco_empresa", "Endereço da Empresa"),
            ("telefone_empresa", "Telefone da Empresa"),
            ("email_empresa", "E-mail da Empresa"),
            ("responsavel_tecnico", "Responsável Técnico")
        ]
        
        self.text_edit_vars = {}
        
        # Criar campos
        for field_name, field_label in fields:
            frame = tk.Frame(self.text_editor_window)
            frame.pack(fill="x", padx=10, pady=5)
            
            tk.Label(frame, text=field_label + ":", 
                    font=('Arial', 9, 'bold')).pack(anchor="w")
            
            var = tk.StringVar()
            entry = tk.Entry(frame, textvariable=var, font=('Arial', 10))
            entry.pack(fill="x", pady=2)
            
            self.text_edit_vars[field_name] = var
        
        # Botões
        btn_frame = tk.Frame(self.text_editor_window)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Button(btn_frame, text="💾 Salvar",
                 command=self.save_text_edits,
                 bg='#10b981', fg='white').pack(side="left", padx=5)
        
        tk.Button(btn_frame, text="❌ Fechar",
                 command=self.text_editor_window.destroy,
                 bg='#ef4444', fg='white').pack(side="right", padx=5)
        
        # Carregar valores atuais
        self.load_text_edits()
        
    except Exception as e:
        print(f"Erro ao abrir editor de textos: {e}")


def load_text_edits(self):
    """Carregar edições de texto atuais"""
    try:
        if not hasattr(self, 'text_edit_vars'):
            return
            
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        for field_name, var in self.text_edit_vars.items():
            c.execute("""
                SELECT field_value FROM pdf_edit_config 
                WHERE user_id = ? AND field_name = ?
            """, (self.user_info['user_id'], field_name))
            
            result = c.fetchone()
            if result:
                var.set(result[0] or "")
            else:
                var.set("")
        
        conn.close()
        
    except Exception as e:
        print(f"Erro ao carregar edições de texto: {e}")


def save_text_edits(self):
    """Salvar edições de texto"""
    try:
        if not hasattr(self, 'text_edit_vars'):
            return
            
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        for field_name, var in self.text_edit_vars.items():
            value = var.get().strip()
            
            c.execute("""
                INSERT OR REPLACE INTO pdf_edit_config 
                (user_id, field_name, field_value, field_type, last_modified)
                VALUES (?, ?, ?, 'text', CURRENT_TIMESTAMP)
            """, (self.user_info['user_id'], field_name, value))
        
        conn.commit()
        conn.close()
        
        self.safe_update_status("✅ Edições de texto salvas!")
        print("✅ Edições de texto salvas com sucesso")
        
        # Fechar janela se existir
        if hasattr(self, 'text_editor_window'):
            try:
                self.text_editor_window.destroy()
            except:
                pass
        
    except Exception as e:
        print(f"Erro ao salvar edições de texto: {e}")
        self.safe_update_status("❌ Erro ao salvar edições")
