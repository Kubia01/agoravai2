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

        header = tk.Frame(container, bg='#f8fafc')
        header.pack(fill="x", pady=(0, 10))
        tk.Label(header, text="Gestão de Locação", font=('Arial', 16, 'bold'), bg='#f8fafc', fg='#1e293b').pack(side="left")

        form_card = tk.Frame(container, bg='white', bd=0, relief='ridge', highlightthickness=0)
        form_card.pack(fill="both", expand=True)

        form = tk.Frame(form_card, bg='white')
        form.pack(fill="both", expand=True, padx=12, pady=12)

        # Vars
        self.numero_var = tk.StringVar(value=self._gerar_numero_sugerido())
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
        self.cliente_combo.pack(side="left", fill="x", expand=True)
        tk.Button(cliente_frame, text="🔄", bg='#10b981', fg='white', relief='flat', command=self._carregar_clientes).pack(side="left", padx=(8, 0))
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
        gerar_btn = self.create_button(actions, "Gerar PDF de Locação", self._gerar_pdf, bg='#10b981')
        gerar_btn.pack(side="right")
        salvar_btn = self.create_button(actions, "Salvar Dados", self._salvar_locacao, bg='#3b82f6')
        salvar_btn.pack(side="right", padx=(0, 10))

        # carregar clientes inicialmente
        self._carregar_clientes()

    def _selecionar_imagem(self):
        path = filedialog.askopenfilename(title="Selecione a imagem do compressor",
                                          filetypes=[("Imagens", "*.jpg *.jpeg *.png"), ("Todos", "*.*")])
        if path:
            self.imagem_compressor_var.set(path)

    def _gerar_numero_sugerido(self) -> str:
        now = datetime.now()
        return f"LOC-{now.strftime('%Y%m%d-%H%M%S')}"

    def _carregar_clientes(self):
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT id, COALESCE(nome_fantasia, nome) FROM clientes ORDER BY nome")
            rows = c.fetchall()
            self._clientes_cache = rows
            nomes = [r[1] for r in rows]
            self.cliente_combo['values'] = nomes
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar clientes: {e}")
        finally:
            try:
                conn.close()
            except:
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
        cliente_id = self._obter_cliente_id_por_nome(self.cliente_var.get())
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
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar PDF: {e}")
        finally:
            try:
                conn.close()
            except:
                pass

