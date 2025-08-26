# Proposta Comercial — Apresentação do Sistema

## Visão Geral
Sistema desktop para gestão comercial e técnica, focado em:
- Cotações de Compra e de Locações (fluxos distintos)
- Geração de documentos executivos em PDF
- Gestão de Clientes, Produtos, Usuários e Relatórios Técnicos
- Consultas e exportações (Excel) quando habilitadas

Benefícios principais:
- Padronização e velocidade na criação de propostas
- Histórico organizado e confiável
- Maior qualidade na apresentação ao cliente

## Módulos do Sistema
- Dashboard: visão geral e atalho às funções principais
- Clientes: cadastro, contatos associados, busca e seleção
- Produtos: cadastro e atributos (tipo, NCM, valor unitário)
- Compras (Cotações): fluxo de proposta de compra, numeração “PROP-000001”
- Locações: fluxo separado de proposta de locação, numeração “LOC-000001”
- Relatórios Técnicos: registro de serviços, tempos, peças
- Usuários e Permissões: gestão de acesso e perfis

## Funcionalidades de Cotações
- Itens com quantidade, preço, períodos/meses (para locação)
- Cálculo automático de totais e exibição amigável
- Inclusão de imagem por item (locação)
- Geração de PDF com:
  - Capa, apresentação, seções específicas
  - Página 4 (locação) com imagem redimensionada
  - Tabelas de equipamentos e condições
  - Termos/Cláusulas (páginas 7–13) com substituição dinâmica de nome da filial
  - Página 14 (assinaturas) com margens seguras

## Filiais e Identidade
- Configuração em `assets/filiais/filiais_config.py`
- Substituição dinâmica de “World Comp” pelo nome da filial selecionada
- Rodapé com CNPJ, endereço, e contatos da filial

## Fluxos Distintos
- Compra:
  - Numeração: `PROP-000001`
  - Páginas padrão (descrição, itens, condições)
- Locação:
  - Numeração: `LOC-000001`
  - Páginas específicas de locação (imagem pág. 4, tabela de equipamentos, termos 7–13, assinaturas pág. 14)

## Geração de PDF
- Módulo: `pdf_generators/cotacao_nova.py`
- Biblioteca: `fpdf2`
- Redimensionamento de imagens e controle de margens
- Arquivos prontos em `data/cotacoes/arquivos/`

## Integrações
- Banco de dados: SQLite (arquivo)
- PDF: fpdf2
- Excel: openpyxl (para consultas/exports)

## Estrutura de Pastas (essencial)
- `interface/`: UI (Tkinter); módulos por área
- `pdf_generators/`: geradores de PDF
- `assets/`: logos e configurações de filiais
- `utils/`: validadores e formatadores
- `data/`: saída (PDFs) e documentação

## Boas Práticas e Padrões
- Textos com acentuação preservada
- Imagens de locação redimensionadas
- Evitar estado residual entre locações (limpeza ao criar nova)

## Exemplos de Uso
### 1) Criar uma Cotação de Locação
1. Acesse a aba `📄 Locações`.
2. Preencha: Número (auto), Filial, Cliente e Contato, Condição de Pagamento.
3. Adicione itens: Nome do Equipamento, Qtd, Valor Mensal, Início e Fim (datas), Descrição e (opcional) Imagem.
4. Clique em “Salvar Locação”.
5. Clique em “Gerar PDF” para produzir o documento em `data/cotacoes/arquivos/`.

### 2) Editar um Item de Locação (duplo clique)
1. Na lista de itens, dê duplo clique sobre o item.
2. Ajuste Nome, Quantidade, Valor, Meses, Datas, Descrição ou Imagem.
3. Salve; os totais serão recalculados automaticamente.

### 3) Criar uma Cotação de Compra
1. Acesse `💰 Compras`.
2. Preencha os campos principais (cliente, filial, condições, itens) e salve.
3. Gere o PDF pelo botão “Gerar PDF”.

### 4) Relatórios Técnicos
1. Acesse `📋 Relatórios`.
2. Selecione cliente e preencha dados do serviço.
3. Salve e gere documentos conforme necessário.

## Capturas de Tela (placeholders)
Coloque imagens nesta pasta e ajuste os caminhos abaixo:
- Pasta sugerida: `data/docs/img/`

Exemplos de referências:
- Dashboard: `![Dashboard](img/dashboard.png)`
- Locações – formulário: `![Locações - Formulário](img/locacoes_form.png)`
- Locações – itens: `![Locações - Itens](img/locacoes_itens.png)`
- Compras: `![Compras](img/compras.png)`
- Relatórios Técnicos: `![Relatórios](img/relatorios.png)`

> Dica: crie a pasta `data/docs/img/` e adicione as imagens com esses nomes para o README de apresentação ficar completo.

## Roadmap (sugestões)
- Template de capa customizável por usuário
- Geração de Word (DOCX) opcional para propostas
- Conector para envio de propostas por e-mail direto do sistema