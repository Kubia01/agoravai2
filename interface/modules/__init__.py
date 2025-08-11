from .dashboard import DashboardModule
from .clientes import ClientesModule
from .produtos import ProdutosModule
from .cotacoes import CotacoesModule
from .relatorios import RelatoriosModule
from .usuarios import UsuariosModule
from .permissoes import PermissoesModule
from .consultas import ConsultasModule

__all__ = [
    'DashboardModule',
    'ClientesModule',
    'ProdutosModule',
        'CotacoesModule',
    'RelatoriosModule',
    'UsuariosModule',
    'PermissoesModule',
    'ConsultasModule'
]