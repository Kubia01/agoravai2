#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import hashlib
import sys
import os

def main():
    try:
        print("=== Sistema CRM - Iniciando ===")
        print(f"Python: {sys.version}")
        print(f"Tkinter disponível: {tk.TkVersion}")
        
        # Verificar ambiente gráfico
        if os.environ.get('DISPLAY') is None and sys.platform.startswith('linux'):
            print("⚠️  Aviso: DISPLAY não está definido (ambiente sem interface gráfica)")
            print("Para usar em servidor, você precisa de X11 forwarding ou VNC")
        
        # Criar banco de dados
        print("Criando/verificando banco de dados...")
        from database import criar_banco, verificar_banco, DB_NAME
        
        # Verificar se o banco existe e é válido
        if verificar_banco():
            print("🔄 Banco recriado com sucesso!")
        else:
            print("✅ Banco de dados OK")
        
        # Importar após verificar banco
        print("Carregando interface...")
        from interface.login import LoginWindow
        
        # Criar janela principal
        root = tk.Tk()
        root.title("CRM - Sistema de Compressores")
        root.withdraw()  # Esconder janela principal inicialmente
        
        # Configurações para melhor compatibilidade
        root.attributes('-alpha', 0.0)  # Tornar transparente temporariamente
        
        print("Criando tela de login...")
        # Mostrar tela de login
        login_window = LoginWindow(root)
        
        # Restaurar opacidade
        root.attributes('-alpha', 1.0)
        
        # Forçar janela para frente (se possível)
        try:
            root.lift()
            if hasattr(root, 'wm_attributes'):
                root.wm_attributes("-topmost", True)
                root.after_idle(lambda: root.wm_attributes("-topmost", False))
        except:
            pass  # Ignorar se não suportado
        
        print("✅ Sistema iniciado! Aguardando login...")
        print("Se a janela não aparecer, pode ser problema de ambiente gráfico.")
        print("Teste com: python test_tkinter.py")
        
        root.mainloop()
        print("Sistema encerrado.")
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("Verifique se todos os arquivos estão presentes:")
        print("- database.py")
        print("- interface/login.py")
        print("- interface/main_window.py")
        return 1
        
    except tk.TclError as e:
        print(f"❌ Erro do Tkinter: {e}")
        print("Possíveis causas:")
        print("1. Não há servidor X rodando (ambiente sem interface gráfica)")
        print("2. DISPLAY não está configurado corretamente")
        print("3. Permissões de X11 não estão corretas")
        print("\nSoluções:")
        print("- Para SSH: use 'ssh -X' ou 'ssh -Y'")
        print("- Para WSL: instale um servidor X como VcXsrv")
        print("- Para servidor: use VNC ou X11 forwarding")
        return 1
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()
        
        # Tentar mostrar erro em janela se possível
        try:
            error_root = tk.Tk()
            error_root.withdraw()
            messagebox.showerror("Erro", f"Erro ao iniciar sistema:\n\n{str(e)}")
            error_root.destroy()
        except:
            print("Não foi possível mostrar janela de erro.")
        
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)