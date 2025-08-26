# Proposta Comercial — Documento de Apresentação do Sistema

## 1. Visão Geral Executiva
O sistema é uma aplicação desktop (Tkinter/Python) para gestão comercial e técnica de compressores, com ênfase na criação de propostas comerciais (compras e locações) e na geração de documentos executivos padronizados em PDF. Ele centraliza o cadastro de clientes e produtos, organiza o histórico de propostas, provê funcionalidades para relatórios técnicos, e mantém consistência de identidade (filiais, CNPJ, contatos) em todos os artefatos gerados.

Benefícios para o cliente:
- Padronização e qualidade de apresentação das propostas.
- Ganho de tempo na elaboração, revisão e distribuição de documentos comerciais.
- Histórico de negociações e documentos centralizados por cliente.
- Menor risco de erro humano (numeração automática, validações e cálculos automáticos).

## 2. Público-alvo e Cenários
- Equipes comerciais que elaboram cotações de compra e contratos de locação.
- Gestores técnicos que emitem relatórios de serviços e acompanhamento.
- Diretores/gestores que necessitam de documentos formais consistentes e auditáveis.

## 3. Arquitetura em Alto Nível
- Interface: Tkinter (Python).
- Persistência: SQLite local (arquivo), com tabelas de clientes, usuários, cotações, itens, etc.
- Geração de PDF: fpdf2 (layout programático das páginas, sem dependência de Word/Adobe).
- Utilitários: formatadores (moeda, data, CNPJ, telefone) e validadores.
- Estrutura de diretórios:
  - `interface/` — módulos de UI por área funcional.
  - `pdf_generators/` — geradores de PDF (propostas, relatórios, apresentação).
  - `assets/` — logos e configuração de filiais (CNPJ, contatos, logomarca).
  - `utils/` — formatadores e validações.
  - `data/` — saída (PDFs) e documentação versionada.

## 4. Módulos e Funcionalidades (Detalhes)
### 4.1 Dashboard
- Visão inicial com status do sistema e atalhos para módulos principais.
- Sinalizações de sucesso/erro durante o carregamento (ex.: clientes, produtos, expiração de cotações). 

### 4.2 Clientes
- Cadastro completo (Razão Social, Fantasia, CNPJ, Endereço, Cidade/Estado, CEP, site, contatos).
- Contatos vinculados a um cliente (nome, email, telefone), para uso direto nas propostas.
- Busca por nome/trechos, atualização de lista em tempo real.
- Integração com cotações: seleção de cliente e contato ao criar proposta.

### 4.3 Produtos
- Cadastro de produtos/itens (nome, tipo, NCM, valor unitário, status ativo).
- Base para compor itens de proposta de compras (quando aplicável).

### 4.4 Compras (Cotações de Compra)
- Fluxo exclusivo para propostas de compra.
- Numeração automática no padrão `PROP-000001` (somente compras).
- Itens com quantidade, valor unitário, total por item e total geral.
- Campos comerciais: condição de pagamento, prazo, frete, moeda.
- Geração de PDF de compra com seções: dados do cliente, itens, condições comerciais e observações.
- Atualização de status e histórico por número de proposta.

### 4.5 Locações (Propostas de Locação)
- Fluxo exclusivo para propostas de locação, independente de compras.
- Numeração automática no padrão `LOC-000001` (somente locações).
- Itens com suporte a:
  - Quantidade, Valor Mensal/Unitário.
  - Datas de início/fim, cálculo automático de meses.
  - Cálculo automático do total (valor mensal × meses × quantidade).
  - Descrição por item e imagem opcional do equipamento.
- Edição de itens por duplo clique (nome, quantidade, valor, período, datas, descrição, imagem) com recálculo instantâneo.
- Geração de PDF de locação com layout executivo:
  - Capa e apresentação institucional.
  - Página 4: apresentação do equipamento ofertado, com imagem redimensionada (margens seguras).
  - Página 5: tabela de equipamentos (nome, qtd, valor, período, total).
  - Página 6: condições de pagamento e condições comerciais (texto padronizado).
  - Páginas 7–13: termos e condições gerais, com substituição dinâmica do nome da filial.
  - Página 14: encerramento e assinaturas (Contratante/Contratada/Testemunhas), respeitando margens.
- Evita vazamento de estado entre locações (limpeza de campos ao criar nova).

### 4.6 Relatórios Técnicos
- Emissão de relatórios com dados de serviços realizados (tipo, datas, tempos de trabalho/deslocamento, materiais/peças).
- Associação a cliente e responsável, histórico de atendimentos.
- Geração de documento técnico em PDF (quando configurado no gerador específico).

### 4.7 Usuários e Permissões
- Cadastro de usuários (nome, username, email, telefone). 
- Perfis e permissões (ex.: admin) controlam visibilidade de abas e ações.
- Possibilidade de templates de capa por usuário (quando configurado).

### 4.8 Filiais (Identidade Corporativa)
- Configuração em `assets/filiais/filiais_config.py` (nome, CNPJ, endereço, emails, telefones, logotipo).
- Substituição automática de “World Comp” pelo nome da filial selecionada em todos os textos de contrato.
- Rodapé com CNPJ/contatos da filial em todas as páginas (exceto capa quando aplicável).

## 5. Regras de Negócio e Validações
- Numeração distinta por tipo de proposta:
  - Compras: `PROP-######`.
  - Locações: `LOC-######`.
- Obrigatoriedade de cliente, filial e condição de pagamento para salvar e gerar PDFs.
- Cálculo de meses a partir de datas de início/fim (garantia de período mínimo de 1 mês quando aplicável).
- Limpeza de campos ao iniciar nova locação (evita reuso involuntário de imagens/itens).
- Geração de PDF somente quando a proposta está salva (usa o registro persistido).

## 6. Detalhes de Geração de PDF
- Biblioteca: fpdf2 (core fonts);
- Textos com acentuação preservada (Latin-1), símbolos especiais ajustados.
- Imagens redimensionadas com preservação de proporção e respeito às margens.
- Substituição dinâmica de variáveis (filial, cliente, contatos, datas, valores, CNPJ).
- Saída padrão: `data/cotacoes/arquivos/Proposta_<NUMERO>.pdf`.

## 7. Operação — Passo a Passo (Sem Imagens)
### 7.1 Criar Proposta de Locação
1) Acesse “📄 Locações”.
2) Preencha número (auto), filial, cliente e contato, condição de pagamento.
3) Adicione itens (nome, qtd, valor mensal, datas início/fim, descrição, imagem opcional).
4) Clique “Salvar Locação”.
5) Clique “Gerar PDF”.

### 7.2 Criar Proposta de Compra
1) Acesse “💰 Compras”.
2) Preencha dados (cliente, filial, condições, itens).
3) Salve e gere o PDF.

### 7.3 Emitir Relatório Técnico
1) Acesse “📋 Relatórios”.
2) Selecione cliente e responsável, informe serviço, tempos e peças.
3) Salve e gere o documento técnico.

## 8. Integrações e Dados
- Banco: SQLite local (arquivo) — simples de distribuir e fazer backup.
- Exportações: Excel via `openpyxl` (quando disponível no módulo específico).
- Identidade corporativa: centralizada em `assets/filiais/filiais_config.py`.

## 9. Segurança e Governança
- Controle de permissões por perfil (ex.: abas restritas a admin).
- Logs básicos e mensagens de erro amigáveis ao usuário.
- Estrutura versionável (Git) para auditoria de mudanças.

## 10. Requisitos e Instalação
- Python 3.10+.
- Dependências: `pip install -r requirements.txt` (fpdf2, Pillow, openpyxl).
- Execução: `python main.py`.
- Ambiente gráfico requerido para Tkinter (Windows/Mac; em Linux, X11).

## 11. Limitações e Considerações
- Armazenamento local (SQLite) — considerar centralização/servidor se houver múltiplos usuários concorrentes.
- Envio automático por e-mail não nativo (pode ser implementado no roadmap).
- Assinaturas digitais/fluxo de aprovação fora do escopo atual.

## 12. Roadmap Sugerido
- Envio de propostas por e-mail com template e anexos em um clique.
- Assinaturas eletrônicas integradas.
- API para integração com ERP/CRM externos.
- Relatórios gerenciais (pipeline de cotações por status, conversão, volume por filial).
- Gerador DOCX opcional, além do PDF, para edição rápida.

## 13. Conclusão
Este sistema organiza o ciclo comercial de forma consistente, segura e ágil, elevando a qualidade das propostas e reduzindo o tempo de resposta ao cliente. A separação clara entre compras e locações, aliada ao controle de identidade por filial e à geração de PDFs executivos, oferece uma experiência profissional do início ao fim.