import tkinter as tk
from tkinter import ttk

from .base_module import BaseModule


class LocacoesModule(BaseModule):
	def setup_ui(self):
		# Importar CotacoesModule dinamicamente para reutilizar UI e lógica
		from .cotacoes_backup import CotacoesModule as _CotacoesModule
		# Instanciar um frame interno para isolar
		self.inner_frame = tk.Frame(self.frame, bg='#f8fafc')
		self.inner_frame.pack(fill='both', expand=True)
		# Criar instância do módulo de cotações sobre o frame interno
		self._cotacoes = _CotacoesModule(self.inner_frame, self.user_id, self.role, self.main_window)
		# Forçar modo Locação na UI
		try:
			if hasattr(self._cotacoes, 'tipo_cotacao_var'):
				self._cotacoes.tipo_cotacao_var.set('Locação')
				if hasattr(self._cotacoes, 'on_tipo_cotacao_changed'):
					self._cotacoes.on_tipo_cotacao_changed()
			# Remover combobox "Tipo de Cotação" de forma segura após a construção do layout
			self.frame.after_idle(self._remove_tipo_cotacao_combobox_safe)
		except Exception as e:
			print(f"LocacoesModule: erro ao configurar modo Locação: {e}")

	def _remove_tipo_cotacao_combobox_safe(self):
		candidates = []
		self._collect_tipo_combobox(self._cotacoes.frame, candidates)
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
		# Encaminhar para o módulo interno
		if hasattr(self, '_cotacoes') and hasattr(self._cotacoes, 'handle_event'):
			self._cotacoes.handle_event(event_type, data)

