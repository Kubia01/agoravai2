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
			# Remover widgets do campo "Tipo de Cotação"
			self._remove_tipo_cotacao_widgets(self._cotacoes.frame)
		except Exception as e:
			print(f"LocacoesModule: erro ao configurar modo Locação: {e}")

	def _remove_tipo_cotacao_widgets(self, root_widget):
		for child in root_widget.winfo_children():
			try:
				if isinstance(child, tk.Label):
					text = child.cget('text') if 'text' in child.keys() else ''
					if isinstance(text, str) and 'Tipo de Cotação' in text:
						child.destroy()
				elif isinstance(child, ttk.Combobox):
					values = child.cget('values') if 'values' in child.keys() else ()
					vals = tuple(values) if isinstance(values, (list, tuple)) else ()
					if ('Compra' in vals and 'Locação' in vals) or ('Locacao' in vals and 'Compra' in vals):
						child.destroy()
			except Exception:
				pass
			# Recursão
			self._remove_tipo_cotacao_widgets(child)

	def handle_event(self, event_type, data=None):
		# Encaminhar para o módulo interno
		if hasattr(self, '_cotacoes') and hasattr(self._cotacoes, 'handle_event'):
			self._cotacoes.handle_event(event_type, data)

