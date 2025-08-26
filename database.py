import sqlite3
import os
import hashlib

DB_NAME = "crm_compressores.db"
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def verificar_banco():
	"""Verificar se o banco existe e tem tamanho válido"""
	if not os.path.exists(DB_NAME) or os.path.getsize(DB_NAME) == 0:
		print(f"⚠️ Banco {DB_NAME} não existe ou está vazio. Criando...")
		criar_banco()
		return True
	return False

def criar_banco():
	"""Criar banco de dados com todas as tabelas necessárias"""
	print(f"🔧 Criando banco de dados: {DB_NAME}")
	
	# Remover banco existente se estiver vazio
	if os.path.exists(DB_NAME) and os.path.getsize(DB_NAME) == 0:
		os.remove(DB_NAME)
		print("🗑️ Banco vazio removido")
	
	conn = sqlite3.connect(DB_NAME)
	c = conn.cursor()
	
	print("📋 Criando tabelas...")
	
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
		created_at TIMESTAMP DEFAULT (datetime('now'))
	)''')
	
	# Tabela Clientes
	c.execute('''CREATE TABLE IF NOT EXISTS clientes (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		nome TEXT NOT NULL,
		nome_fantasia TEXT,
		cnpj TEXT UNIQUE,
		inscricao_estadual TEXT,
		inscricao_municipal TEXT,
		endereco TEXT,
		numero TEXT,
		complemento TEXT,
		bairro TEXT,
		cidade TEXT,
		estado TEXT,
		cep TEXT,
		telefone TEXT,
		email TEXT,
		site TEXT,
		prazo_pagamento TEXT,
		ativo BOOLEAN DEFAULT 1,
		prazo_pagamento TEXT,
		created_at TIMESTAMP DEFAULT (datetime('now'))
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
		created_at TIMESTAMP DEFAULT (datetime('now')),
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
		created_at TIMESTAMP DEFAULT (datetime('now'))
	)''')
	
	# Tabela Itens de Kit
	c.execute('''CREATE TABLE IF NOT EXISTS kit_items (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		kit_id INTEGER NOT NULL,
		produto_id INTEGER NOT NULL,
		quantidade REAL NOT NULL DEFAULT 1,
		created_at TIMESTAMP DEFAULT (datetime('now')),
		FOREIGN KEY (kit_id) REFERENCES produtos(id),
		FOREIGN KEY (produto_id) REFERENCES produtos(id)
	)''')
	
	# Tabela Cotações
	c.execute('''CREATE TABLE IF NOT EXISTS cotacoes (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		numero_proposta TEXT NOT NULL UNIQUE,
		cliente_id INTEGER NOT NULL,
		responsavel_id INTEGER NOT NULL,
		filial_id INTEGER DEFAULT 1,
		data_criacao DATE NOT NULL,
		data_validade DATE,
		modelo_compressor TEXT,
		numero_serie_compressor TEXT,
		descricao_atividade TEXT,
		observacoes TEXT,
		valor_total REAL DEFAULT 0,
		tipo_frete TEXT,
		condicao_pagamento TEXT,
		prazo_entrega TEXT,
		moeda TEXT DEFAULT 'BRL',
		status TEXT DEFAULT 'Em Aberto',
		caminho_arquivo_pdf TEXT,
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
		created_at TIMESTAMP DEFAULT (datetime('now')),
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
		created_at TIMESTAMP DEFAULT (datetime('now')),
		FOREIGN KEY (cotacao_id) REFERENCES cotacoes(id),
		FOREIGN KEY (produto_id) REFERENCES produtos(id),
		FOREIGN KEY (kit_id) REFERENCES itens_cotacao(id)
	)''')
	
	# Tabela Relatórios Técnicos
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
		condicao_encontrada TEXT,
		placa_identificacao TEXT,
		acoplamento TEXT,
		aspectos_rotores TEXT,
		valvulas_acopladas TEXT,
		data_recebimento_equip TEXT,
		parafusos_pinos TEXT,
		superficie_vedacao TEXT,
		engrenagens TEXT,
		bico_injetor TEXT,
		rolamentos TEXT,
		aspecto_oleo TEXT,
		data_peritagem TEXT,
		interf_desmontagem TEXT,
		aspecto_rotores_aba3 TEXT,
		aspecto_carcaca TEXT,
		interf_mancais TEXT,
		galeria_hidraulica TEXT,
		data_desmembracao TEXT,
		servicos_propostos TEXT,
		pecas_recomendadas TEXT,
		data_pecas TEXT,
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
		created_at TIMESTAMP DEFAULT (datetime('now')),
		FOREIGN KEY (cliente_id) REFERENCES clientes(id),
		FOREIGN KEY (responsavel_id) REFERENCES usuarios(id)
	)''')
	
	# Tabela de Permissões de Usuários
	c.execute('''CREATE TABLE IF NOT EXISTS permissoes_usuarios (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		usuario_id INTEGER NOT NULL,
		modulo TEXT NOT NULL,
		nivel_acesso TEXT NOT NULL DEFAULT 'sem_acesso',
		created_at TIMESTAMP DEFAULT (datetime('now')),
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
		created_at TIMESTAMP DEFAULT (datetime('now')),
		FOREIGN KEY (relatorio_id) REFERENCES relatorios_tecnicos(id),
		FOREIGN KEY (tecnico_id) REFERENCES usuarios(id)
	)''')
	
	# Tabela Filiais
	c.execute('''CREATE TABLE IF NOT EXISTS filiais (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		nome TEXT NOT NULL,
		cnpj TEXT,
		endereco TEXT,
		cidade TEXT,
		estado TEXT,
		cep TEXT,
		telefones TEXT,
		email TEXT,
		ativo BOOLEAN DEFAULT 1,
		created_at TIMESTAMP DEFAULT (datetime('now'))
	)''')
	
	# Inserir dados iniciais
	print("📝 Inserindo dados iniciais...")
	
	# Usuário admin padrão
	try:
		password_hash = hashlib.sha256("admin123".encode()).hexdigest()
		c.execute('''INSERT INTO usuarios (username, password, role, nome_completo, email, template_personalizado)
					 VALUES (?, ?, ?, ?, ?, ?)''', 
				  ('admin', password_hash, 'admin', 'Administrador', 'admin@worldcomp.com.br', 0))
		print("✅ Usuário admin criado")
	except sqlite3.IntegrityError:
		print("ℹ️ Usuário admin já existe")
	
	# Filial padrão
	try:
		c.execute('''INSERT INTO filiais (id, nome, cnpj, endereco, cidade, estado, cep, telefones, email)
					 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
				  (1, 'World Comp Brasil', '12.345.678/0001-90', 'Rua das Flores, 123', 'São Paulo', 'SP', '01234-567', '(11) 99999-9999', 'contato@worldcomp.com.br'))
		print("✅ Filial padrão criada")
	except sqlite3.IntegrityError:
		print("ℹ️ Filial padrão já existe")
	
	# Cliente de teste
	try:
		c.execute('''INSERT INTO clientes (nome, cnpj, email, telefone, endereco, cidade, estado, cep, prazo_pagamento)
					 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
				  ('Cliente Teste', '98.765.432/0001-10', 'teste@cliente.com', '(11) 88888-8888', 'Rua Teste, 456', 'São Paulo', 'SP', '04567-890', '30 dias'))
		print("✅ Cliente de teste criado")
	except sqlite3.IntegrityError:
		print("ℹ️ Cliente de teste já existe")
	
	# Produto de teste
	try:
		c.execute('''INSERT INTO produtos (nome, tipo, valor_unitario, descricao)
					 VALUES (?, ?, ?, ?)''',
				  ('Compressor Teste', 'Produto', 1000.00, 'Compressor para testes'))
		print("✅ Produto de teste criado")
	except sqlite3.IntegrityError:
		print("ℹ️ Produto de teste já existe")
	
	conn.commit()
	conn.close()
	
	print(f"🎉 Banco de dados {DB_NAME} criado com sucesso!")
	print(f"📁 Localização: {os.path.abspath(DB_NAME)}")
	
	# Verificar tamanho do arquivo
	if os.path.exists(DB_NAME):
		size = os.path.getsize(DB_NAME)
		print(f"📊 Tamanho do arquivo: {size} bytes")
		if size > 0:
			print("✅ Banco de dados válido e funcional!")
		else:
			print("❌ Banco de dados está vazio!")

if __name__ == "__main__":
	criar_banco()
	print("Banco de dados criado com sucesso!")
