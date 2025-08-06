# Sistema CRM Compressores

Sistema de gestão para empresa de manutenção de compressores, desenvolvido em Python com interface Tkinter.

## 📋 Funcionalidades

### ✅ Módulos Implementados

- **Login e Autenticação**: Sistema de login com usuários admin/operador
- **Dashboard**: Visão geral do sistema com estatísticas
- **Gestão de Clientes**: 
  - Cadastro completo de clientes com dados comerciais
  - **NOVO**: Múltiplos contatos por cliente
  - **NOVO**: Busca automática de CEP
  - Validação de CNPJ e e-mail
- **Gestão de Produtos/Serviços/Kits**:
  - Cadastro de produtos e serviços
  - **NOVO**: Criação de kits (composição de produtos + serviços)
  - **MELHORADO**: Limpeza automática de campos ao criar novo item
  - Controle de ativo/inativo
- **Gestão de Técnicos**: Cadastro de técnicos de campo
- **Cotações**: Criação e gestão de propostas comerciais
- **Relatórios Técnicos**: 
  - Relatórios de campo com 4 abas
  - Registro de eventos por técnico
  - **MELHORADO**: Geração de PDF com anexos das abas
  - **MELHORADO**: Layout aprimorado do PDF
- **Gestão de Usuários**: Administração de usuários do sistema

### 🆕 Principais Melhorias Implementadas

1. **Sistema de Login Aprimorado**:
   - Nova interface mais moderna
   - Melhor controle de janelas
   - Inicialização automática do banco de dados
   - Login de teste facilitado

2. **Cadastro de Clientes Completo**:
   - Aba dedicada para contatos do cliente
   - Múltiplos contatos por cliente (nome, cargo, telefone, email)
   - Busca automática de endereço por CEP
   - Campos expandidos (inscrições, endereço completo)
   - Validações aprimoradas

3. **Sistema de Kits Funcional**:
   - Criação de kits compostos por produtos e serviços
   - Cálculo automático do valor total do kit
   - Interface intuitiva para adicionar/remover itens
   - Separação clara entre produtos, serviços e kits

4. **Geração de PDF Melhorada**:
   - Layout no formato original
   - Inclusão de anexos de todas as 4 abas
   - Melhor formatação e organização
   - Campos condicionais (só aparecem se preenchidos)

5. **Limpeza e Otimização**:
   - Remoção de arquivos desnecessários
   - Estrutura de banco de dados otimizada
   - Migração automática de dados antigos

## 🚀 Como Executar

### Pré-requisitos
- Python 3.7 ou superior
- pip (gerenciador de pacotes Python)

### Instalação

1. Clone o repositório:
```bash
git clone <url-do-repositorio>
cd crm-compressores
```

2. Instale as dependências:

**Opção 1 - Script automático (recomendado):**
```bash
python instalar_dependencias.py
```

**Opção 2 - Manual:**
```bash
pip install -r requirements.txt
```

3. Execute o sistema:
```bash
python main.py
```

### ⚠️ Solução de Problemas

Se encontrar erro de "ReportLab não disponível":
```bash
pip install reportlab Pillow
```

Se encontrar erro de indentação ou importação, o sistema foi corrigido automaticamente.

### Login Padrão
- **Usuário**: admin
- **Senha**: admin123

## 🗂️ Estrutura do Projeto

```
crm-compressores/
├── main.py                 # Arquivo principal
├── database.py             # Configuração do banco de dados
├── requirements.txt        # Dependências Python
├── logo.jpg               # Logo da empresa
├── interface/             # Módulos da interface
│   ├── __init__.py
│   ├── login.py           # Tela de login
│   ├── main_window.py     # Janela principal
│   └── modules/           # Módulos específicos
│       ├── base_module.py
│       ├── clientes.py    # Gestão de clientes
│       ├── produtos.py    # Gestão de produtos/kits
│       ├── cotacoes.py    # Sistema de cotações
│       ├── relatorios.py  # Relatórios técnicos
│       ├── tecnicos.py    # Gestão de técnicos
│       ├── usuarios.py    # Gestão de usuários
│       └── dashboard.py   # Dashboard principal
├── pdf_generators/        # Geradores de PDF
│   ├── __init__.py
│   ├── cotacao.py
│   └── relatorio_tecnico.py
└── utils/                 # Utilitários
    ├── __init__.py
    ├── formatters.py      # Formatadores de dados
    └── correios.py        # Busca de CEP
```

## 🛠️ Tecnologias Utilizadas

- **Python 3.7+**: Linguagem principal
- **Tkinter**: Interface gráfica
- **SQLite**: Banco de dados
- **FPDF2**: Geração de PDFs
- **Requests**: Consulta de APIs (CEP)

## 📊 Banco de Dados

O sistema utiliza SQLite com as seguintes tabelas principais:
- `usuarios`: Usuários do sistema
- `clientes`: Dados dos clientes
- `contatos`: Contatos dos clientes
- `produtos`: Produtos, serviços e kits
- `kit_items`: Composição dos kits
- `tecnicos`: Técnicos de campo
- `cotacoes`: Propostas comerciais
- `itens_cotacao`: Itens das cotações
- `relatorios_tecnicos`: Relatórios de campo
- `eventos_campo`: Eventos registrados pelos técnicos

## 🔧 Funcionalidades Avançadas

### Busca de CEP
O sistema integra com a API ViaCEP para busca automática de endereços.

### Validações
- CNPJ com dígitos verificadores
- E-mail com formato válido
- Telefones formatados automaticamente

### Formatação Automática
- CNPJ: XX.XXX.XXX/XXXX-XX
- Telefone: (XX) XXXXX-XXXX
- CEP: XXXXX-XXX
- Valores monetários: R$ X.XXX,XX

## 📝 Changelog

### Versão Atual
- ✅ Login aprimorado com nova interface
- ✅ Cadastro de clientes com múltiplos contatos
- ✅ Sistema de kits funcional
- ✅ Geração de PDF com anexos
- ✅ Busca automática de CEP
- ✅ Limpeza de arquivos desnecessários
- ✅ Migração automática de banco de dados

## 🤝 Contribuição

Para contribuir com o projeto:

1. Faça um fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto é desenvolvido para uso interno da empresa de manutenção de compressores.

## 📞 Contato

Para dúvidas ou suporte, entre em contato com a equipe de desenvolvimento. 
