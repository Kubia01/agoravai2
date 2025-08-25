import tkinter as tk
from tkinter import ttk

from .base_module import BaseModule


class CotacoesModule(BaseModule):
	def setup_ui(self):
		# Importar e instanciar o módulo original de cotações (compra)
		from .cotacoes_backup import CotacoesModule as _CotacoesModule
		self.inner_frame = tk.Frame(self.frame, bg='#f8fafc')
		self.inner_frame.pack(fill='both', expand=True)
		self._compras = _CotacoesModule(self.inner_frame, self.user_id, self.role, self.main_window)
		# Forçar modo Compra e remover campo "Tipo de Cotação"
		try:
			if hasattr(self._compras, 'tipo_cotacao_var'):
				self._compras.tipo_cotacao_var.set('Compra')
				if hasattr(self._compras, 'on_tipo_cotacao_changed'):
					self._compras.on_tipo_cotacao_changed()
			# Remover combobox "Tipo de Cotação" de forma segura após a construção do layout
			self.frame.after_idle(self._remove_tipo_cotacao_combobox_safe)
		except Exception as e:
			print(f"CotacoesModule: erro ao configurar modo Compra: {e}")

	def _remove_tipo_cotacao_combobox_safe(self):
		# Coletar todas as combobox candidatas primeiro
		candidates = []
		self._collect_tipo_combobox(self._compras.frame, candidates)
		# Destruir com segurança
		for cb in candidates:
			try:
				cb.destroy()
			except Exception:
				pass

	def _collect_tipo_combobox(self, root_widget, out_list):
		for child in root_widget.winfo_children():
			try:
				if isinstance(child, ttk.Combobox):
					values = child.cget('values') if 'values' in child.keys() else ()
					vals = tuple(values) if isinstance(values, (list, tuple)) else ()
					if ('Compra' in vals and ('Locação' in vals or 'Locacao' in vals)):
						out_list.append(child)
			except Exception:
				pass
			self._collect_tipo_combobox(child, out_list)

	def handle_event(self, event_type, data=None):
		if hasattr(self, '_compras') and hasattr(self._compras, 'handle_event'):
			self._compras.handle_event(event_type, data)