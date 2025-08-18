import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import sqlite3
import os
from datetime import datetime

from .base_module import BaseModule
from database import DB_NAME
from assets.filiais.filiais_config import listar_filiais
from pdf_generators.locacao_contrato import gerar_pdf_locacao


class LocacaoModule(BaseModule):
    def setup_ui(self):
        self.current_locacao_id = None

        container = tk.Frame(self.frame, bg='#f8fafc')
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # Header
        header = tk.Frame(container, bg='#f8fafc')
        header.pack(fill="x", pady=(0, 10))
        tk.Label(header, text="Gestão de Locação", font=('Arial', 16, 'bold'), bg='#f8fafc', fg='#1e293b').pack(side="left")

        # Layout principal em 2 colunas, igual cotações
        main_frame = tk.Frame(container, bg='#f8fafc')
        main_frame.pack(fill="both", expand=True)
        main_frame.grid_columnconfigure(0, weight=1, uniform="cols")
        main_frame.grid_columnconfigure(1, weight=1, uniform="cols")
        main_frame.grid_rowconfigure(0, weight=1)

        # Painel de formulário (esquerda)
        form_panel = tk.Frame(main_frame, bg='#f8fafc')
        form_panel.grid(row=0, column=0, sticky="nsew", padx=(10, 10), pady=(10, 10))

        form_card = tk.Frame(form_panel, bg='white', bd=0, relief='ridge', highlightthickness=0)
        form_card.pack(fill="both", expand=True)

        form = tk.Frame(form_card, bg='white')
        form.pack(fill="both", expand=True, padx=12, pady=12)

        # Vars
        self.numero_var = tk.StringVar(value="")
        self.filial_var = tk.StringVar(value="2 - WORLD COMP DO BRASIL COMPRESSORES LTDA")
        self.cliente_var = tk.StringVar()
        self.contato_var = tk.StringVar()
        self.marca_var = tk.StringVar()
        self.modelo_var = tk.StringVar()
        self.serie_var = tk.StringVar()
        self.data_inicio_var = tk.StringVar(value=datetime.today().strftime('%d/%m/%Y'))
        self.data_fim_var = tk.StringVar()
        self.valor_mensal_var = tk.StringVar()
        self.moeda_var = tk.StringVar(value="BRL")
        self.vencimento_dia_var = tk.StringVar(value="10")
        self.condicoes_pagamento_text = scrolledtext.ScrolledText(form, height=5, width=40, font=('Arial', 10))
        self.imagem_compressor_var = tk.StringVar()

        # Grid
        row = 0
        def add_row(label, widget):
            nonlocal row
            tk.Label(form, text=label, font=('Arial', 10, 'bold'), bg='white').grid(row=row, column=0, sticky="w", pady=5)
            widget.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
            row += 1

        form.grid_columnconfigure(1, weight=1)

        add_row("Número da Proposta:", tk.Entry(form, textvariable=self.numero_var, font=('Arial', 10)))

        # Filial
        filiais = [f"{fid} - {nome}" for fid, nome in listar_filiais()]
        filial_combo = ttk.Combobox(form, textvariable=self.filial_var, values=filiais, state="readonly", width=50)
        add_row("Filial:", filial_combo)

        # Cliente
        cliente_frame = tk.Frame(form, bg='white')
        self.cliente_combo = ttk.Combobox(cliente_frame, textvariable=self.cliente_var, width=40)
        # Forçar atualização sempre que abrir o dropdown
        try:
            self.cliente_combo.configure(postcommand=self.refresh_clientes)
        except Exception:
            pass
        self.cliente_combo.pack(side="left", fill="x", expand=True)
        self.cliente_combo.bind("<<ComboboxSelected>>", self.on_cliente_selected)
        tk.Button(cliente_frame, text="🔄", bg='#10b981', fg='white', relief='flat', command=self.refresh_clientes).pack(side="left", padx=(8, 0))
        add_row("Cliente:", cliente_frame)

        add_row("Contato:", tk.Entry(form, textvariable=self.contato_var, font=('Arial', 10)))
        add_row("Marca do Equipamento:", tk.Entry(form, textvariable=self.marca_var, font=('Arial', 10)))
        add_row("Modelo do Equipamento:", tk.Entry(form, textvariable=self.modelo_var, font=('Arial', 10)))
        add_row("Número de Série:", tk.Entry(form, textvariable=self.serie_var, font=('Arial', 10)))
        add_row("Data de Início:", tk.Entry(form, textvariable=self.data_inicio_var, font=('Arial', 10)))
        add_row("Data de Fim:", tk.Entry(form, textvariable=self.data_fim_var, font=('Arial', 10)))

        valor_frame = tk.Frame(form, bg='white')
        ttk.Combobox(valor_frame, textvariable=self.moeda_var, values=["BRL", "USD", "EUR"], width=6, state="readonly").pack(side="left")
        tk.Entry(valor_frame, textvariable=self.valor_mensal_var, font=('Arial', 10)).pack(side="left", fill="x", expand=True, padx=(8, 0))
        add_row("Valor Mensal:", valor_frame)

        add_row("Dia de Vencimento:", tk.Entry(form, textvariable=self.vencimento_dia_var, font=('Arial', 10), width=10))

        # Condições de pagamento
        tk.Label(form, text="Condições de Pagamento:", font=('Arial', 10, 'bold'), bg='white').grid(row=row, column=0, sticky="nw", pady=5)
        self.condicoes_pagamento_text.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=5)
        row += 1

        # Imagem do compressor
        img_frame = tk.Frame(form, bg='white')
        tk.Entry(img_frame, textvariable=self.imagem_compressor_var, font=('Arial', 10)).pack(side="left", fill="x", expand=True)
        tk.Button(img_frame, text="Selecionar Imagem", bg='#3b82f6', fg='white', relief='flat', command=self._selecionar_imagem).pack(side="left", padx=(8, 0))
        add_row("Imagem do Compressor:", img_frame)

        # Ações
        actions = tk.Frame(form_card, bg='white')
        actions.pack(fill="x", padx=12, pady=(0, 12))
        gerar_btn = self.create_button(actions, "Gerar PDF", self._gerar_pdf, bg='#10b981')
        gerar_btn.pack(side="right")
        salvar_btn = self.create_button(actions, "Salvar Locação", self._salvar_locacao, bg='#3b82f6')
        salvar_btn.pack(side="right", padx=(0, 10))
        nova_btn = self.create_button(actions, "Nova Locação", self.nova_locacao, bg='#e2e8f0', fg='#475569')
        nova_btn.pack(side="left")

        # Painel de lista (direita)
        lista_panel = tk.Frame(main_frame, bg='#f8fafc')
        lista_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 10), pady=(10, 10))
        lista_panel.grid_columnconfigure(0, weight=1)
        lista_panel.grid_rowconfigure(2, weight=1)

        lista_card = tk.Frame(lista_panel, bg='white', bd=0, relief='ridge', highlightthickness=0)
        lista_card.pack(fill="both", expand=True)

        tk.Label(lista_card, text="📋 Lista de Locações", font=("Arial", 12, "bold"), bg='white', anchor="w").pack(fill="x", padx=12, pady=(12, 8))

        lista_inner = tk.Frame(lista_card, bg='white')
        lista_inner.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # Busca
        search_frame, self.search_var = self.create_search_frame(lista_inner, command=self.buscar_locacoes)
        search_frame.pack(fill="x", pady=(0, 10))

        # Rodapé de botões da lista
        lista_buttons = tk.Frame(lista_inner, bg='white')
        lista_buttons.pack(side="bottom", fill="x", pady=(10, 0))

        # Treeview de locações
        columns = ("numero", "cliente", "periodo", "valor")
        self.locacoes_tree = ttk.Treeview(lista_inner, columns=columns, show="headings")
        self.locacoes_tree.heading("numero", text="Número")
        self.locacoes_tree.heading("cliente", text="Cliente")
        self.locacoes_tree.heading("periodo", text="Período")
        self.locacoes_tree.heading("valor", text="Valor/Mês")
        self.locacoes_tree.column("numero", width=150)
        self.locacoes_tree.column("cliente", width=250)
        self.locacoes_tree.column("periodo", width=160)
        self.locacoes_tree.column("valor", width=120)

        lista_scrollbar = ttk.Scrollbar(lista_inner, orient="vertical", command=self.locacoes_tree.yview)
        self.locacoes_tree.configure(yscrollcommand=lista_scrollbar.set)
        self.locacoes_tree.pack(side="left", fill="both", expand=True)
        lista_scrollbar.pack(side="right", fill="y")

        editar_btn = self.create_button(lista_buttons, "Editar", self.editar_locacao)
        editar_btn.pack(side="left", padx=(0, 10))
        gerar_pdf_lista_btn = self.create_button(lista_buttons, "Gerar PDF", self.gerar_pdf_selecionado, bg='#10b981')
        gerar_pdf_lista_btn.pack(side="right")

        # Dados iniciais
        self.refresh_all_data()
        # Preencher número sequencial automático
        try:
            if not self.current_locacao_id:
                self.numero_var.set(self.gerar_numero_sequencial_locacao())
        except Exception as e:
            print(f"Aviso ao gerar número sequencial inicial de locação: {e}")

    def _selecionar_imagem(self):
        path = filedialog.askopenfilename(title="Selecione a imagem do compressor",
                                          filetypes=[("Imagens", "*.jpg *.jpeg *.png"), ("Todos", "*.*")])
        if path:
            self.imagem_compressor_var.set(path)

    def gerar_numero_sequencial_locacao(self) -> str:
        """Gerar número sequencial para locação (formato LOC-000001)."""
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT MAX(CAST(SUBSTR(numero_proposta, 5) AS INTEGER)) FROM locacoes WHERE numero_proposta LIKE 'LOC-%'")
            result = c.fetchone()
            proximo = (result[0] + 1) if result and result[0] else 1
            return f"LOC-{proximo:06d}"
        except sqlite3.Error as e:
            print(f"Erro ao gerar número sequencial de locação: {e}")
            return f"LOC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def refresh_clientes(self):
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT id, nome FROM clientes ORDER BY nome")
            rows = c.fetchall()
            self._clientes_cache = rows
            # Mapa idêntico ao de cotações: "Nome (ID: X)" -> id
            self.clientes_dict = {f"{nome} (ID: {cid})": cid for cid, nome in rows}
            self.cliente_combo['values'] = list(self.clientes_dict.keys())
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar clientes: {e}")
        finally:
            try:
                conn.close()
            except:
                pass

    def on_cliente_selected(self, event=None):
        """Preencher condição de pagamento conforme cadastro do cliente."""
        cliente_str = self.cliente_var.get()
        if not cliente_str:
            return
        cliente_id = getattr(self, 'clientes_dict', {}).get(cliente_str)
        if not cliente_id:
            return
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT prazo_pagamento FROM clientes WHERE id = ?", (cliente_id,))
            result = c.fetchone()
            if result and result[0]:
                self.condicoes_pagamento_text.delete('1.0', 'end')
                self.condicoes_pagamento_text.insert('1.0', str(result[0]))
        except Exception as e:
            print(f"Erro ao buscar prazo de pagamento do cliente: {e}")
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def _obter_cliente_id_por_nome(self, nome):
        if not getattr(self, '_clientes_cache', None):
            return None
        for cid, n in self._clientes_cache:
            if n == nome:
                return cid
        return None

    def _salvar_locacao(self):
        dados = self._coletar_dados()
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("""
                INSERT INTO locacoes (
                    numero_proposta, cliente_id, filial_id, responsavel_id,
                    data_inicio, data_fim, marca, modelo, numero_serie,
                    valor_mensal, moeda, vencimento_dia, condicoes_pagamento,
                    imagem_compressor, caminho_pdf
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
            """, (
                dados['numero'], dados['cliente_id'], dados['filial_id'], dados['responsavel_id'],
                dados['data_inicio'], dados['data_fim'], dados['marca'], dados['modelo'], dados['serie'],
                dados['valor_mensal'], dados['moeda'], dados['vencimento_dia'], dados['condicoes_pagamento'],
                dados['imagem_compressor']
            ))
            conn.commit()
            messagebox.showinfo("Sucesso", "Locação salva com sucesso!")
            # Emitir evento e atualizar lista
            self.emit_event('locacao_created')
            self.refresh_lista_locacoes()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar locação: {e}")
        finally:
            try:
                conn.close()
            except:
                pass

    def _coletar_dados(self):
        filial_str = self.filial_var.get() or "2 - WORLD COMP DO BRASIL COMPRESSORES LTDA"
        filial_id = int(filial_str.split(' - ')[0]) if ' - ' in filial_str else 2
        cliente_id = getattr(self, 'clientes_dict', {}).get(self.cliente_var.get())
        condicoes_pg = (self.condicoes_pagamento_text.get('1.0', 'end') or '').strip()
        return {
            'numero': (self.numero_var.get() or self._gerar_numero_sugerido()).strip(),
            'filial_id': filial_id,
            'cliente_id': cliente_id,
            'responsavel_id': getattr(self.main_window, 'user_id', None),
            'contato': self.contato_var.get().strip(),
            'marca': (self.marca_var.get() or '').strip(),
            'modelo': (self.modelo_var.get() or '').strip(),
            'serie': (self.serie_var.get() or '').strip(),
            'data_inicio': (self.data_inicio_var.get() or '').strip(),
            'data_fim': (self.data_fim_var.get() or '').strip(),
            'valor_mensal': (self.valor_mensal_var.get() or '').strip(),
            'moeda': (self.moeda_var.get() or 'BRL').strip(),
            'vencimento_dia': (self.vencimento_dia_var.get() or '').strip(),
            'condicoes_pagamento': condicoes_pg,
            'imagem_compressor': (self.imagem_compressor_var.get() or '').strip(),
            'cliente_nome': self.cliente_var.get().strip()
        }

    def _gerar_pdf(self):
        dados = self._coletar_dados()
        if not dados['cliente_id']:
            messagebox.showwarning("Aviso", "Selecione um cliente válido para gerar o PDF.")
            return
        try:
            output_dir = os.path.join('data', 'locacoes')
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"contrato_locacao_{dados['numero'].replace('/', '-')}.pdf")
            gerar_pdf_locacao(dados, output_path)

            # Persistir caminho no banco, criando/atualizando registro
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT id FROM locacoes WHERE numero_proposta = ?", (dados['numero'],))
            row = c.fetchone()
            if row:
                c.execute("UPDATE locacoes SET caminho_pdf = ? WHERE id = ?", (output_path, row[0]))
            else:
                c.execute("""
                    INSERT INTO locacoes (
                        numero_proposta, cliente_id, filial_id, responsavel_id,
                        data_inicio, data_fim, marca, modelo, numero_serie,
                        valor_mensal, moeda, vencimento_dia, condicoes_pagamento,
                        imagem_compressor, caminho_pdf
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    dados['numero'], dados['cliente_id'], dados['filial_id'], dados['responsavel_id'],
                    dados['data_inicio'], dados['data_fim'], dados['marca'], dados['modelo'], dados['serie'],
                    dados['valor_mensal'], dados['moeda'], dados['vencimento_dia'], dados['condicoes_pagamento'],
                    dados['imagem_compressor'], output_path
                ))
            conn.commit()
            messagebox.showinfo("PDF Gerado", f"Contrato de locação gerado com sucesso:\n{output_path}")
            self.refresh_lista_locacoes()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar PDF: {e}")
        finally:
            try:
                conn.close()
            except:
                pass

    def refresh_all_data(self):
        self.refresh_clientes()
        self.refresh_lista_locacoes()

    def buscar_locacoes(self):
        termo = (self.search_var.get() or '').strip()
        self.refresh_lista_locacoes(termo)

    def refresh_lista_locacoes(self, termo_busca: str = ""):
        # Limpar lista
        for item in self.locacoes_tree.get_children():
            self.locacoes_tree.delete(item)
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            base_sql = (
                "SELECT l.id, l.numero_proposta, COALESCE(c.nome_fantasia, c.nome) as cliente, "
                "COALESCE(l.data_inicio, '') as di, COALESCE(l.data_fim, '') as df, COALESCE(l.valor_mensal, 0) as vm "
                "FROM locacoes l JOIN clientes c ON c.id = l.cliente_id"
            )
            params = []
            if termo_busca:
                base_sql += " WHERE l.numero_proposta LIKE ? OR cliente LIKE ?"
                like = f"%{termo_busca}%"
                params.extend([like, like])
            base_sql += " ORDER BY l.id DESC"
            c.execute(base_sql, params)
            rows = c.fetchall()
            for rid, numero, cliente, di, df, vm in rows:
                periodo = f"{di} a {df}".strip()
                self.locacoes_tree.insert("", "end", values=(numero, cliente, periodo, str(vm)), tags=(rid,))
        except Exception as e:
            print(f"Erro ao carregar lista de locações: {e}")
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def editar_locacao(self):
        selected = self.locacoes_tree.selection()
        if not selected:
            self.show_warning("Selecione uma locação para editar.")
            return
        tags = self.locacoes_tree.item(selected[0]).get('tags')
        if not tags:
            return
        locacao_id = tags[0]
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute(
                "SELECT numero_proposta, cliente_id, filial_id, data_inicio, data_fim, marca, modelo, numero_serie, valor_mensal, moeda, vencimento_dia, condicoes_pagamento, imagem_compressor FROM locacoes WHERE id = ?",
                (locacao_id,)
            )
            row = c.fetchone()
            if not row:
                return
            (numero, cliente_id, filial_id, di, df, marca, modelo, serie, vm, moeda, venc, cond_pg, img) = row
            # Setar campos
            self.current_locacao_id = locacao_id
            self.numero_var.set(numero or "")
            # Selecionar filial por id
            try:
                # Reconstruir string "id - nome" a partir da lista
                filiais = [f"{fid} - {nome}" for fid, nome in listar_filiais()]
                for s in filiais:
                    if s.startswith(f"{filial_id} - "):
                        self.filial_var.set(s)
                        break
            except Exception:
                pass
            # Selecionar cliente (chave do dict é "Nome (ID: X)")
            self.refresh_clientes()
            if hasattr(self, 'clientes_dict'):
                for display, cid in self.clientes_dict.items():
                    if cid == cliente_id:
                        self.cliente_var.set(display)
                        break
            self.data_inicio_var.set(di or "")
            self.data_fim_var.set(df or "")
            self.marca_var.set(marca or "")
            self.modelo_var.set(modelo or "")
            self.serie_var.set(serie or "")
            self.valor_mensal_var.set(str(vm) if vm is not None else "")
            self.moeda_var.set(moeda or "BRL")
            self.vencimento_dia_var.set(venc or "")
            self.condicoes_pagamento_text.delete('1.0', 'end')
            if cond_pg:
                self.condicoes_pagamento_text.insert('1.0', cond_pg)
            self.imagem_compressor_var.set(img or "")
        except Exception as e:
            self.show_error(f"Erro ao carregar locação: {e}")
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def gerar_pdf_selecionado(self):
        selected = self.locacoes_tree.selection()
        if not selected:
            self.show_warning("Selecione uma locação para gerar PDF.")
            return
        tags = self.locacoes_tree.item(selected[0]).get('tags')
        if not tags:
            return
        locacao_id = tags[0]
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute(
                "SELECT numero_proposta, cliente_id, filial_id, data_inicio, data_fim, marca, modelo, numero_serie, valor_mensal, moeda, vencimento_dia, condicoes_pagamento, imagem_compressor FROM locacoes WHERE id = ?",
                (locacao_id,)
            )
            row = c.fetchone()
            if not row:
                return
            (numero, cliente_id, filial_id, di, df, marca, modelo, serie, vm, moeda, venc, cond_pg, img) = row
            # Obter nome do cliente
            c.execute("SELECT COALESCE(nome_fantasia, nome) FROM clientes WHERE id = ?", (cliente_id,))
            cliente_nome = (c.fetchone() or [""])[0]
            dados = {
                'numero': numero,
                'cliente_id': cliente_id,
                'filial_id': filial_id,
                'data_inicio': di,
                'data_fim': df,
                'marca': marca,
                'modelo': modelo,
                'serie': serie,
                'valor_mensal': vm,
                'moeda': moeda,
                'vencimento_dia': venc,
                'condicoes_pagamento': cond_pg,
                'imagem_compressor': img,
                'cliente_nome': cliente_nome,
                'responsavel_id': getattr(self.main_window, 'user_id', None)
            }
            output_dir = os.path.join('data', 'locacoes')
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"contrato_locacao_{numero.replace('/', '-')}.pdf")
            gerar_pdf_locacao(dados, output_path)
            c.execute("UPDATE locacoes SET caminho_pdf = ? WHERE id = ?", (output_path, locacao_id))
            conn.commit()
            self.show_success(f"PDF gerado com sucesso!\nLocal: {output_path}")
        except Exception as e:
            self.show_error(f"Erro ao gerar PDF: {e}")
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def handle_event(self, event_type, data=None):
        if event_type == 'cliente_created':
            self.refresh_clientes()
        elif event_type == 'locacao_created':
            self.refresh_lista_locacoes()

    def nova_locacao(self):
        """Limpar formulário e gerar novo número sequencial, similar a Cotações."""
        self.current_locacao_id = None
        self.numero_var.set(self.gerar_numero_sequencial_locacao())
        self.filial_var.set("2 - WORLD COMP DO BRASIL COMPRESSORES LTDA")
        self.cliente_var.set("")
        self.contato_var.set("")
        self.marca_var.set("")
        self.modelo_var.set("")
        self.serie_var.set("")
        self.data_inicio_var.set(datetime.today().strftime('%d/%m/%Y'))
        self.data_fim_var.set("")
        self.valor_mensal_var.set("")
        self.moeda_var.set("BRL")
        self.vencimento_dia_var.set("10")
        self.condicoes_pagamento_text.delete('1.0', 'end')
        self.imagem_compressor_var.set("")

