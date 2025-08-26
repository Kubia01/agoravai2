import sqlite3
import os
import hashlib

DB_NAME = "crm_compressores.db"
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def criar_banco():
	conn = sqlite3.connect(DB_NAME)
	c = conn.cursor()
	
	# Tabela Usuários
	c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		username TEXT UNIQUE NOT NULL,
		password TEXT NOT NULL,
		role TEXT DEFAULT 'operador',
		nome_completo TEXT,
		email TEXT,
		telefone TEXT,
		template_personalizado BOOLEAN DEFAULT 0,
		template_image_path TEXT,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	)''')
	
	# Tabela Clientes
	c.execute('''CREATE TABLE IF NOT EXISTS clientes (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		nome TEXT NOT NULL,
		cnpj TEXT UNIQUE,
		email TEXT,
		telefone TEXT,
		endereco TEXT,
		cidade TEXT,
		estado TEXT,
		cep TEXT,
		observacoes TEXT,
		ativo BOOLEAN DEFAULT 1,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	)''')
	
	# Tabela Contatos
	c.execute('''CREATE TABLE IF NOT EXISTS contatos (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		cliente_id INTEGER NOT NULL,
		nome TEXT NOT NULL,
		cargo TEXT,
		email TEXT,
		telefone TEXT,
		celular TEXT,
		observacoes TEXT,
		ativo BOOLEAN DEFAULT 1,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (cliente_id) REFERENCES clientes(id)
	)''')
	
	# Tabela Produtos
	c.execute('''CREATE TABLE IF NOT EXISTS produtos (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		nome TEXT NOT NULL,
		tipo TEXT NOT NULL,
		ncm TEXT,
		valor_unitario REAL DEFAULT 0,
		descricao TEXT,
		ativo BOOLEAN DEFAULT 1,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	)''')
	
	# Tabela Itens de Kit
	c.execute('''CREATE TABLE IF NOT EXISTS kit_items (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		kit_id INTEGER NOT NULL,
		produto_id INTEGER NOT NULL,
		quantidade REAL NOT NULL DEFAULT 1,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (kit_id) REFERENCES produtos(id),
		FOREIGN KEY (produto_id) REFERENCES produtos(id)
	)''')
	
	# Tabela Cotações
	c.execute('''CREATE TABLE IF NOT EXISTS cotacoes (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		numero_proposta TEXT NOT NULL UNIQUE,
		cliente_id INTEGER NOT NULL,
		responsavel_id INTEGER NOT NULL,
		data_criacao DATE NOT NULL,
		validade DATE,
		condicoes_pagamento TEXT,
		prazo_entrega TEXT,
		observacoes TEXT,
		status TEXT DEFAULT 'Pendente',
		total_geral REAL DEFAULT 0,
		desconto REAL DEFAULT 0,
		valor_final REAL DEFAULT 0,
		relacao_pecas TEXT,
		esboco_servico TEXT,
		relacao_pecas_substituir TEXT,
		tipo_cotacao TEXT DEFAULT 'Compra',
		locacao_valor_mensal REAL,
		locacao_data_inicio DATE,
		locacao_data_fim DATE,
		locacao_qtd_meses INTEGER,
		locacao_nome_equipamento TEXT,
		locacao_imagem_path TEXT,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (cliente_id) REFERENCES clientes(id),
		FOREIGN KEY (responsavel_id) REFERENCES usuarios(id)
	)''')

	# Tabela Itens da Cotação
	c.execute('''CREATE TABLE IF NOT EXISTS itens_cotacao (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		cotacao_id INTEGER NOT NULL,
		produto_id INTEGER,
		tipo TEXT NOT NULL,
		item_nome TEXT NOT NULL,
		quantidade REAL NOT NULL,
		descricao TEXT,
		valor_unitario REAL NOT NULL,
		valor_total_item REAL NOT NULL,
		eh_kit BOOLEAN DEFAULT 0,
		kit_id INTEGER,
		mao_obra REAL DEFAULT 0,
		deslocamento REAL DEFAULT 0,
		estadia REAL DEFAULT 0,
		tipo_operacao TEXT DEFAULT 'Compra',
		locacao_data_inicio DATE,
		locacao_data_fim DATE,
		locacao_qtd_meses INTEGER,
		locacao_imagem_path TEXT,
		FOREIGN KEY (cotacao_id) REFERENCES cotacoes(id),
		FOREIGN KEY (produto_id) REFERENCES produtos(id),
		FOREIGN KEY (kit_id) REFERENCES itens_cotacao(id)
	)''')

	# Tabela Relatórios Técnicos - ATUALIZADA com campos das abas 2 e 3
	c.execute('''CREATE TABLE IF NOT EXISTS relatorios_tecnicos (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		numero_relatorio TEXT NOT NULL UNIQUE,
		cliente_id INTEGER NOT NULL,
		responsavel_id INTEGER NOT NULL,
		data_criacao DATE NOT NULL,
		formulario_servico TEXT,
		tipo_servico TEXT,
		descricao_servico TEXT,
		data_recebimento DATE,
		
		-- Aba 1: Condição Inicial
		condicao_encontrada TEXT,
		placa_identificacao TEXT,
		acoplamento TEXT,
		aspectos_rotores TEXT,
		valvulas_acopladas TEXT,
		data_recebimento_equip TEXT,
		
		-- Aba 2: Peritagem do Subconjunto
		parafusos_pinos TEXT,
		superficie_vedacao TEXT,
		engrenagens TEXT,
		bico_injetor TEXT,
		rolamentos TEXT,
		aspecto_oleo TEXT,
		data_peritagem TEXT,
		
		-- Aba 3: Desmembrando Unidade Compressora
		interf_desmontagem TEXT,
		aspecto_rotores_aba3 TEXT,
		aspecto_carcaca TEXT,
		interf_mancais TEXT,
		galeria_hidraulica TEXT,
		data_desmembracao TEXT,
		
		-- Aba 4: Relação de Peças e Serviços
		servicos_propostos TEXT,
		pecas_recomendadas TEXT,
		data_pecas TEXT,
		
		-- Outros campos
		cotacao_id INTEGER,
		tempo_trabalho_total TEXT,
		tempo_deslocamento_total TEXT,
		fotos TEXT,
		assinaturas TEXT,
		anexos_aba1 TEXT,
		anexos_aba2 TEXT,
		anexos_aba3 TEXT,
		anexos_aba4 TEXT,
		filial_id INTEGER DEFAULT 2,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (cliente_id) REFERENCES clientes(id),
		FOREIGN KEY (responsavel_id) REFERENCES usuarios(id)
	)''')

	# Tabela de Permissões de Usuários
	c.execute('''CREATE TABLE IF NOT EXISTS permissoes_usuarios (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		usuario_id INTEGER NOT NULL,
		modulo TEXT NOT NULL,
		nivel_acesso TEXT NOT NULL DEFAULT 'sem_acesso',
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
		UNIQUE(usuario_id, modulo)
	)''')

	# Tabela de Eventos de Campo
	c.execute('''CREATE TABLE IF NOT EXISTS eventos_campo (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		relatorio_id INTEGER NOT NULL,
		tecnico_id INTEGER NOT NULL,
		data_hora TEXT NOT NULL,
		evento TEXT NOT NULL,
		tipo TEXT NOT NULL,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (relatorio_id) REFERENCES relatorios_tecnicos(id),
		FOREIGN KEY (tecnico_id) REFERENCES usuarios(id)
	)''')

	# Atualizar tabela relatorios_tecnicos existente se necessário
	try:
		c.execute("ALTER TABLE relatorios_tecnicos ADD COLUMN anexos_aba1 TEXT")
	except sqlite3.OperationalError:
		pass  # Coluna já existe
		
	try:
		c.execute("ALTER TABLE relatorios_tecnicos ADD COLUMN anexos_aba2 TEXT")
	except sqlite3.OperationalError:
		pass  # Coluna já existe
		
	try:
		c.execute("ALTER TABLE relatorios_tecnicos ADD COLUMN anexos_aba3 TEXT")
	except sqlite3.OperationalError:
		pass  # Coluna já existe
		
	try:
		c.execute("ALTER TABLE relatorios_tecnicos ADD COLUMN anexos_aba4 TEXT")
	except sqlite3.OperationalError:
		pass  # Coluna já existe
		
	try:
		c.execute("ALTER TABLE relatorios_tecnicos ADD COLUMN filial_id INTEGER DEFAULT 2")
	except sqlite3.OperationalError:
		pass  # Coluna já existe

	conn.commit()
	conn.close()

if __name__ == "__main__":
	criar_banco()
	print("Banco de dados criado com sucesso!")
