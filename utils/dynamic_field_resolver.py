import sqlite3
from typing import Dict, Any, Optional, List
import json
from datetime import datetime

class DynamicFieldResolver:
    """
    Classe para resolver campos dinâmicos baseados em dados do banco de dados.
    Permite mapear referências como 'cliente.nome' para valores reais dos registros.
    """
    
    def __init__(self, db_name: str):
        self.db_name = db_name
        self.current_data = {}
        self.field_mappings = self._initialize_field_mappings()
    
    def _initialize_field_mappings(self) -> Dict[str, Dict[str, str]]:
        """Inicializar mapeamentos de campos disponíveis"""
        return {
            'cliente': {
                'nome': 'Nome/Razão Social',
                'nome_fantasia': 'Nome Fantasia', 
                'cnpj': 'CNPJ',
                'inscricao_estadual': 'Inscrição Estadual',
                'inscricao_municipal': 'Inscrição Municipal',
                'endereco': 'Endereço',
                'numero': 'Número',
                'complemento': 'Complemento',
                'bairro': 'Bairro',
                'cidade': 'Cidade',
                'estado': 'Estado',
                'cep': 'CEP',
                'telefone': 'Telefone',
                'email': 'Email',
                'site': 'Site',
                'prazo_pagamento': 'Prazo de Pagamento'
            },
            'responsavel': {
                'nome_completo': 'Nome Completo',
                'username': 'Nome de Usuário',
                'email': 'Email',
                'telefone': 'Telefone',
                'role': 'Função'
            },
            'tecnico': {
                'nome': 'Nome do Técnico',
                'especialidade': 'Especialidade',
                'telefone': 'Telefone',
                'email': 'Email'
            },
            'cotacao': {
                'numero_proposta': 'Número da Proposta',
                'data_criacao': 'Data de Criação',
                'data_validade': 'Data de Validade',
                'modelo_compressor': 'Modelo do Compressor',
                'numero_serie_compressor': 'Número de Série',
                'descricao_atividade': 'Descrição da Atividade',
                'observacoes': 'Observações',
                'valor_total': 'Valor Total',
                'tipo_frete': 'Tipo de Frete',
                'condicao_pagamento': 'Condição de Pagamento',
                'prazo_entrega': 'Prazo de Entrega',
                'moeda': 'Moeda',
                'status': 'Status',
                'relacao_pecas': 'Relação de Peças'
            },
            'item': {
                'item_nome': 'Nome do Item',
                'tipo': 'Tipo',
                'quantidade': 'Quantidade',
                'descricao': 'Descrição',
                'valor_unitario': 'Valor Unitário',
                'valor_total_item': 'Valor Total',
                'eh_kit': 'É Kit',
                'mao_obra': 'Mão de Obra',
                'deslocamento': 'Deslocamento',
                'estadia': 'Estadia'
            },
            'empresa': {
                'nome': 'Nome da Empresa',
                'endereco': 'Endereço',
                'cep': 'CEP',
                'cnpj': 'CNPJ',
                'inscricao_estadual': 'Inscrição Estadual',
                'telefones': 'Telefones',
                'email': 'Email',
                'site': 'Site'
            },
            'contato': {
                'nome': 'Nome do Contato',
                'cargo': 'Cargo',
                'telefone': 'Telefone',
                'email': 'Email',
                'observacoes': 'Observações'
            }
        }
    
    def load_cotacao_data(self, cotacao_id: int) -> bool:
        """
        Carregar dados completos de uma cotação específica
        """
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Buscar dados da cotação com cliente e responsável
            cursor.execute("""
                SELECT 
                    c.*,
                    cl.nome as cliente_nome,
                    cl.nome_fantasia as cliente_nome_fantasia,
                    cl.cnpj as cliente_cnpj,
                    cl.inscricao_estadual as cliente_inscricao_estadual,
                    cl.inscricao_municipal as cliente_inscricao_municipal,
                    cl.endereco as cliente_endereco,
                    cl.numero as cliente_numero,
                    cl.complemento as cliente_complemento,
                    cl.bairro as cliente_bairro,
                    cl.cidade as cliente_cidade,
                    cl.estado as cliente_estado,
                    cl.cep as cliente_cep,
                    cl.telefone as cliente_telefone,
                    cl.email as cliente_email,
                    cl.site as cliente_site,
                    cl.prazo_pagamento as cliente_prazo_pagamento,
                    u.nome_completo as responsavel_nome_completo,
                    u.username as responsavel_username,
                    u.email as responsavel_email,
                    u.telefone as responsavel_telefone,
                    u.role as responsavel_role
                FROM cotacoes c
                LEFT JOIN clientes cl ON c.cliente_id = cl.id
                LEFT JOIN usuarios u ON c.responsavel_id = u.id
                WHERE c.id = ?
            """, (cotacao_id,))
            
            row = cursor.fetchone()
            if not row:
                return False
            
            # Obter nomes das colunas
            columns = [description[0] for description in cursor.description]
            cotacao_data = dict(zip(columns, row))
            
            # Buscar itens da cotação
            cursor.execute("""
                SELECT 
                    ic.*,
                    p.nome as produto_nome,
                    p.tipo as produto_tipo,
                    p.ncm as produto_ncm
                FROM itens_cotacao ic
                LEFT JOIN produtos p ON ic.produto_id = p.id
                WHERE ic.cotacao_id = ?
                ORDER BY ic.id
            """, (cotacao_id,))
            
            itens_rows = cursor.fetchall()
            itens_columns = [description[0] for description in cursor.description]
            itens_data = [dict(zip(itens_columns, row)) for row in itens_rows]
            
            # Buscar contatos do cliente se disponível
            contatos_data = []
            if cotacao_data.get('cliente_id'):
                cursor.execute("""
                    SELECT nome, cargo, telefone, email, observacoes
                    FROM contatos
                    WHERE cliente_id = ?
                    ORDER BY id
                """, (cotacao_data['cliente_id'],))
                
                contatos_rows = cursor.fetchall()
                contatos_columns = [description[0] for description in cursor.description]
                contatos_data = [dict(zip(contatos_columns, row)) for row in contatos_rows]
            
            # Organizar dados por categoria
            self.current_data = {
                'cotacao': {k: v for k, v in cotacao_data.items() if not k.startswith(('cliente_', 'responsavel_'))},
                'cliente': {k.replace('cliente_', ''): v for k, v in cotacao_data.items() if k.startswith('cliente_')},
                'responsavel': {k.replace('responsavel_', ''): v for k, v in cotacao_data.items() if k.startswith('responsavel_')},
                'itens': itens_data,
                'contatos': contatos_data,
                'empresa': self._load_empresa_data(),
                'meta': {
                    'loaded_at': datetime.now().isoformat(),
                    'cotacao_id': cotacao_id,
                    'total_itens': len(itens_data),
                    'valor_total_calculado': sum(item.get('valor_total_item', 0) or 0 for item in itens_data)
                }
            }
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"Erro ao carregar dados da cotação {cotacao_id}: {e}")
            return False
    
    def _load_empresa_data(self) -> Dict[str, Any]:
        """Carregar dados padrão da empresa"""
        # Dados fixos da empresa - podem ser configuráveis no futuro
        return {
            'nome': 'WORLD COMP COMPRESSORES LTDA',
            'endereco': 'Rua Fernando Pessoa, nº 11 – Batistini – São Bernardo do Campo – SP',
            'cep': '09844-390',
            'cnpj': '10.644.944/0001-55',
            'inscricao_estadual': '635.970.206.110',
            'telefones': '(11) 4543-6893 / 4543-6857',
            'email': 'contato@worldcompressores.com.br',
            'site': 'www.worldcompressores.com.br'
        }
    
    def resolve_field(self, field_reference: str, item_index: Optional[int] = None) -> str:
        """
        Resolver uma referência de campo para seu valor real
        
        Args:
            field_reference: Referência no formato 'categoria.campo' (ex: 'cliente.nome')
            item_index: Índice do item (para campos de itens)
        
        Returns:
            Valor resolvido ou placeholder se não encontrado
        """
        try:
            if '.' not in field_reference:
                return f"[ERRO: {field_reference}]"
            
            category, field = field_reference.split('.', 1)
            
            # Casos especiais
            if category == 'item' and item_index is not None:
                return self._resolve_item_field(field, item_index)
            elif category == 'contato':
                return self._resolve_contato_field(field)
            elif category == 'meta':
                return self._resolve_meta_field(field)
            
            # Casos normais
            if category not in self.current_data:
                return f"[{field_reference}]"
            
            data = self.current_data[category]
            
            if field not in data:
                return f"[{field_reference}]"
            
            value = data[field]
            
            # Formatação especial para alguns campos
            if field in ['valor_total', 'valor_unitario', 'valor_total_item', 'mao_obra', 'deslocamento', 'estadia']:
                if value is not None:
                    return f"R$ {float(value):.2f}"
                return "R$ 0,00"
            elif field in ['data_criacao', 'data_validade']:
                if value:
                    return self._format_date(value)
                return ""
            elif field == 'cnpj' and value:
                return self._format_cnpj(value)
            elif field in ['telefone', 'telefones'] and value:
                return self._format_phone(value)
            
            return str(value) if value is not None else ""
            
        except Exception as e:
            print(f"Erro ao resolver campo {field_reference}: {e}")
            return f"[ERRO: {field_reference}]"
    
    def _resolve_item_field(self, field: str, item_index: int) -> str:
        """Resolver campo de item específico"""
        itens = self.current_data.get('itens', [])
        
        if item_index >= len(itens):
            return f"[item.{field}]"
        
        item = itens[item_index]
        
        if field not in item:
            return f"[item.{field}]"
        
        value = item[field]
        
        # Formatação especial
        if field in ['valor_unitario', 'valor_total_item', 'mao_obra', 'deslocamento', 'estadia']:
            if value is not None:
                return f"R$ {float(value):.2f}"
            return "R$ 0,00"
        elif field == 'quantidade':
            return str(float(value)) if value is not None else "0"
        
        return str(value) if value is not None else ""
    
    def _resolve_contato_field(self, field: str) -> str:
        """Resolver campo do primeiro contato disponível"""
        contatos = self.current_data.get('contatos', [])
        
        if not contatos:
            return f"[contato.{field}]"
        
        contato = contatos[0]  # Usar primeiro contato
        
        if field not in contato:
            return f"[contato.{field}]"
        
        value = contato[field]
        return str(value) if value is not None else ""
    
    def _resolve_meta_field(self, field: str) -> str:
        """Resolver campos meta/calculados"""
        meta = self.current_data.get('meta', {})
        
        if field == 'total_itens':
            return str(meta.get('total_itens', 0))
        elif field == 'valor_total_calculado':
            value = meta.get('valor_total_calculado', 0)
            return f"R$ {float(value):.2f}"
        elif field == 'data_hoje':
            return datetime.now().strftime('%d/%m/%Y')
        elif field == 'hora_atual':
            return datetime.now().strftime('%H:%M')
        
        return f"[meta.{field}]"
    
    def _format_date(self, date_str: str) -> str:
        """Formatar data para exibição"""
        try:
            if len(date_str) == 10 and date_str.count('-') == 2:
                # Formato YYYY-MM-DD
                year, month, day = date_str.split('-')
                return f"{day}/{month}/{year}"
            return date_str
        except:
            return date_str
    
    def _format_cnpj(self, cnpj: str) -> str:
        """Formatar CNPJ"""
        try:
            # Remove caracteres não numéricos
            numbers = ''.join(filter(str.isdigit, cnpj))
            if len(numbers) == 14:
                return f"{numbers[:2]}.{numbers[2:5]}.{numbers[5:8]}/{numbers[8:12]}-{numbers[12:]}"
            return cnpj
        except:
            return cnpj
    
    def _format_phone(self, phone: str) -> str:
        """Formatar telefone (retorna como está - pode ser expandido)"""
        return phone
    
    def get_available_fields(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Retornar lista de campos disponíveis organizados por categoria
        """
        result = {}
        
        for category, fields in self.field_mappings.items():
            result[category] = [
                {
                    'field': field_name,
                    'label': field_label,
                    'reference': f"{category}.{field_name}",
                    'example': self.resolve_field(f"{category}.{field_name}") if self.current_data else f"[{category}.{field_name}]"
                }
                for field_name, field_label in fields.items()
            ]
        
        # Adicionar campos especiais
        result['meta'] = [
            {'field': 'total_itens', 'label': 'Total de Itens', 'reference': 'meta.total_itens', 'example': '[meta.total_itens]'},
            {'field': 'valor_total_calculado', 'label': 'Valor Total Calculado', 'reference': 'meta.valor_total_calculado', 'example': '[meta.valor_total_calculado]'},
            {'field': 'data_hoje', 'label': 'Data de Hoje', 'reference': 'meta.data_hoje', 'example': '[meta.data_hoje]'},
            {'field': 'hora_atual', 'label': 'Hora Atual', 'reference': 'meta.hora_atual', 'example': '[meta.hora_atual]'}
        ]
        
        return result
    
    def resolve_template_text(self, text: str, item_index: Optional[int] = None) -> str:
        """
        Resolver todas as referências de campos em um texto
        Substitui padrões como {cliente.nome} pelos valores reais
        """
        try:
            import re
            
            # Padrão para encontrar referências: {categoria.campo}
            pattern = r'\{([^}]+)\}'
            
            def replace_reference(match):
                reference = match.group(1)
                return self.resolve_field(reference, item_index)
            
            return re.sub(pattern, replace_reference, text)
            
        except Exception as e:
            print(f"Erro ao resolver template de texto: {e}")
            return text
    
    def validate_field_reference(self, reference: str) -> bool:
        """
        Validar se uma referência de campo é válida
        """
        try:
            if '.' not in reference:
                return False
            
            category, field = reference.split('.', 1)
            
            # Verificar categoria especial
            if category in ['meta']:
                return field in ['total_itens', 'valor_total_calculado', 'data_hoje', 'hora_atual']
            
            # Verificar categoria normal
            return category in self.field_mappings and field in self.field_mappings[category]
            
        except:
            return False
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Retornar resumo dos dados carregados
        """
        if not self.current_data:
            return {'status': 'no_data'}
        
        return {
            'status': 'loaded',
            'cotacao_id': self.current_data.get('meta', {}).get('cotacao_id'),
            'numero_proposta': self.current_data.get('cotacao', {}).get('numero_proposta'),
            'cliente_nome': self.current_data.get('cliente', {}).get('nome'),
            'responsavel_nome': self.current_data.get('responsavel', {}).get('nome_completo'),
            'total_itens': len(self.current_data.get('itens', [])),
            'valor_total': self.current_data.get('cotacao', {}).get('valor_total'),
            'loaded_at': self.current_data.get('meta', {}).get('loaded_at')
        }