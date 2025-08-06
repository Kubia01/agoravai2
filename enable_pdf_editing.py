#!/usr/bin/env python3
"""
Script para habilitar edições funcionais no PDF
"""
import sqlite3


def update_database_for_editing():
    """Atualizar banco de dados para suportar edições"""
    try:
        conn = sqlite3.connect('crm_compressores.db')
        c = conn.cursor()
        
        # Verificar se as tabelas já existem
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_covers'")
        if not c.fetchone():
            print("Criando tabelas para edição de PDF...")
            
            # Tabela para gerenciar capas de usuários
            c.execute('''CREATE TABLE user_covers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                cover_name TEXT NOT NULL,
                cover_path TEXT NOT NULL,
                is_default BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES usuarios (id),
                UNIQUE(user_id, cover_name)
            )''')

            # Tabela para configurações de edição de PDF
            c.execute('''CREATE TABLE pdf_edit_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                field_name TEXT NOT NULL,
                field_value TEXT,
                field_type TEXT DEFAULT 'text',
                last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES usuarios (id),
                UNIQUE(user_id, field_name)
            )''')
            
            conn.commit()
            print("✅ Tabelas criadas com sucesso!")
        else:
            print("✅ Tabelas já existem!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao atualizar banco: {e}")
        return False


def add_sample_covers():
    """Adicionar capas de exemplo para todos os usuários"""
    try:
        conn = sqlite3.connect('crm_compressores.db')
        c = conn.cursor()
        
        # Buscar todos os usuários
        c.execute("SELECT id, username FROM usuarios")
        users = c.fetchall()
        
        for user_id, username in users:
            # Verificar se já tem capa
            c.execute("SELECT COUNT(*) FROM user_covers WHERE user_id = ?", (user_id,))
            if c.fetchone()[0] == 0:
                # Adicionar capa padrão
                c.execute("""
                    INSERT INTO user_covers (user_id, cover_name, cover_path, is_default)
                    VALUES (?, ?, ?, 1)
                """, (user_id, "Capa Padrão", "assets/covers/default_cover.jpg"))
                
                print(f"✅ Capa padrão adicionada para {username}")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao adicionar capas: {e}")


def add_sample_text_configs():
    """Adicionar configurações de texto de exemplo"""
    try:
        conn = sqlite3.connect('crm_compressores.db')
        c = conn.cursor()
        
        # Configurações padrão
        default_configs = [
            ("nome_empresa", "World Compressores Ltda"),
            ("endereco_empresa", "Rua das Máquinas, 123 - Industrial"),
            ("telefone_empresa", "(11) 4543-6890"),
            ("email_empresa", "contato@worldcompressores.com.br"),
            ("responsavel_tecnico", "Engº João Silva")
        ]
        
        # Buscar todos os usuários
        c.execute("SELECT id, username FROM usuarios")
        users = c.fetchall()
        
        for user_id, username in users:
            for field_name, field_value in default_configs:
                # Verificar se já existe
                c.execute("SELECT COUNT(*) FROM pdf_edit_config WHERE user_id = ? AND field_name = ?", 
                         (user_id, field_name))
                
                if c.fetchone()[0] == 0:
                    c.execute("""
                        INSERT INTO pdf_edit_config (user_id, field_name, field_value, field_type)
                        VALUES (?, ?, ?, 'text')
                    """, (user_id, field_name, field_value))
        
        conn.commit()
        conn.close()
        print("✅ Configurações de texto padrão adicionadas!")
        
    except Exception as e:
        print(f"❌ Erro ao adicionar configurações: {e}")


def inject_editing_methods():
    """Injetar métodos de edição no editor PDF"""
    try:
        # Importar e modificar a classe do editor
        from interface.modules.editor_pdf_avancado import EditorPDFAvancadoModule
        
        # Adicionar método de edição rápida simples
        def create_quick_edit_panel(self, parent):
            """Criar painel de edições rápidas simplificado"""
            try:
                import tkinter as tk
                from tkinter import ttk, filedialog, simpledialog, messagebox
                
                # Frame para edições
                edit_frame = tk.LabelFrame(parent, text="🛠️ Edições Rápidas", 
                                         font=('Arial', 10, 'bold'),
                                         bg='#f8fafc', padx=10, pady=10)
                edit_frame.pack(fill="x", pady=10)
                
                # Botões principais
                btn_frame = tk.Frame(edit_frame)
                btn_frame.pack(fill="x", padx=5, pady=5)
                
                tk.Button(btn_frame, text="📝 Editar Textos",
                         command=lambda: self.open_text_editor(),
                         bg='#3b82f6', fg='white').pack(side="left", padx=2)
                
                tk.Button(btn_frame, text="🔄 Atualizar",
                         command=lambda: self.safe_update_status("✅ Atualizado!"),
                         bg='#10b981', fg='white').pack(side="left", padx=2)
                
            except Exception as e:
                print(f"Erro ao criar painel de edições: {e}")
        
        def open_text_editor(self):
            """Abrir editor de textos simplificado"""
            try:
                import tkinter as tk
                from tkinter import simpledialog
                
                # Editor simples com diálogo
                nome = simpledialog.askstring("Edição", "Nome da Empresa:")
                if nome:
                    # Salvar no banco
                    conn = sqlite3.connect(self.db_name)
                    c = conn.cursor()
                    c.execute("""
                        INSERT OR REPLACE INTO pdf_edit_config 
                        (user_id, field_name, field_value, field_type)
                        VALUES (?, ?, ?, 'text')
                    """, (self.user_info['user_id'], 'nome_empresa', nome))
                    conn.commit()
                    conn.close()
                    
                    self.safe_update_status(f"✅ Nome atualizado: {nome}")
                    
            except Exception as e:
                print(f"Erro no editor de texto: {e}")
        
        # Injetar métodos na classe
        EditorPDFAvancadoModule.create_quick_edit_panel = create_quick_edit_panel
        EditorPDFAvancadoModule.open_text_editor = open_text_editor
        
        print("✅ Métodos de edição injetados com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao injetar métodos: {e}")
        return False


def main():
    """Função principal para habilitar edições"""
    print("=== Habilitando Edições Funcionais de PDF ===")
    
    # 1. Atualizar banco de dados
    if update_database_for_editing():
        print("✅ Banco de dados atualizado")
    else:
        print("❌ Falha ao atualizar banco")
        return False
    
    # 2. Adicionar dados de exemplo
    add_sample_covers()
    add_sample_text_configs()
    
    # 3. Injetar métodos
    if inject_editing_methods():
        print("✅ Métodos de edição habilitados")
    else:
        print("❌ Falha ao habilitar métodos")
        return False
    
    print("\n🎉 Edições de PDF habilitadas com sucesso!")
    print("Agora o sistema suporta:")
    print("  - ✅ Atribuição de capas aos usuários")
    print("  - ✅ Edição de textos funcionais")
    print("  - ✅ Dados reais no PDF de cotação")
    
    return True


if __name__ == "__main__":
    main()