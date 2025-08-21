from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.colors import black, grey, whitesmoke, beige


def gerar_pdf_locacao(output_path: str = "exemplo_locacao.pdf") -> None:
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT))
    styles.add(ParagraphStyle(name='Justify', alignment=TA_LEFT))

    story = []

    # Página 1
    story.append(Paragraph("UbibComp", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("COMPRESSORES", styles["Title"]))
    story.append(Spacer(1, 24))
    story.append(Paragraph("PROPOSTA", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("COMERCIAL", styles["Title"]))
    story.append(PageBreak())

    # Página 2
    story.append(Paragraph("WORLD COMP DO BRASIL COMPRESSORES EIRELI", styles["Heading2"]))
    story.append(Paragraph("Rua Fernando Pessoa, 11 Bairro: Batistini,", styles["Normal"]))
    story.append(Paragraph("São Bernardo do Campo – SP Cep: 09844-390", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("PROPOSTA COMERCIAL", styles["Heading2"]))
    story.append(Paragraph("REF: CONTRATO DE LOCAÇÃO", styles["Normal"]))
    story.append(Paragraph("NÚMERO:", styles["Normal"]))
    story.append(Paragraph("DADOS:", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("A/C:", styles["Heading3"]))
    story.append(Paragraph("GRUPO DELGA", styles["Normal"]))
    story.append(Paragraph("Srta", styles["Normal"]))
    story.append(Paragraph("Compras", styles["Normal"]))
    story.append(Paragraph("11 97283-8255", styles["Normal"]))
    story.append(Paragraph("Aline.gomes@delga.com.br", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("De:", styles["Heading3"]))
    story.append(Paragraph("WORLD COMP DO BRASIL", styles["Normal"]))
    story.append(Paragraph("Rogério Cerqueira | Valdir Bernardes", styles["Normal"]))
    story.append(Paragraph("rogerio@worldcompressores.com.br", styles["Normal"]))
    story.append(Paragraph("valdir@worldcompressores.com.br", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Prezados Senhores:", styles["Normal"]))
    story.append(Spacer(1, 12))
    texto_apresentacao = (
        "Agradecemos por nos a oportunidade de apresentarmos nossa proposta para especificação de LOCAÇÃO DE COMPRESSOR DE AR. "
        "A World Comp Compressores é especializada em manutenção de compressores de parafuso das principais marcas do mercado, como Atlas Copco, Ingersoll Rand, Chicago. "
        "Atuamos também com revisão de equipamentos e unidades compressoras, venda de peças, bem como venda e locação de compressores de parafuso isentos de óleo e lubrificados. "
        "Com profissionais altamente especializados e atendimento especializado, colocando-nos à disposição para analisar, concordar e prestar os devidos esclarecimentos, sempre buscando atender às especificações e necessidades de nossos clientes."
    )
    story.append(Paragraph(texto_apresentacao, styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Atenciosamente,", styles["Normal"]))
    story.append(Spacer(1, 24))
    story.append(Paragraph("WORLD COMP DO BRASIL COMPRESSORES EIRELI", styles["Heading3"]))
    story.append(PageBreak())

    # Página 3
    story.append(Paragraph("WORLD COMP DO BRASIL COMPRESSORES EIRELI", styles["Heading2"]))
    story.append(Paragraph("Rua Fernando Pessoa, 11 Bairro: Batistini,", styles["Normal"]))
    story.append(Paragraph("São Bernardo do Campo – SP Cep: 09844-390", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("SOBRE A WORLD COMP", styles["Heading2"]))
    sobre_text = (
        "A World Comp Compressores é uma empresa com mais de uma década de atuação no mercado nacional, especializada na manutenção de compressores de ar do tipo parafuso."
    )
    story.append(Paragraph(sobre_text, styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("NOSSOS SERVIÇOS", styles["Heading2"]))
    servicos_text = (
        "A empresa oferece um portfólio completo de serviços,que contempla a manutenção preventiva e corretiva de compressores e unidades compressoras, a venda de peças de reposição para diversas marcas, a compra de compressores de parafuso — incluindo modelos lubrificados e isentos de óleo —, além da recuperação de unidades compressoras e trocadores de calor. "
        "A World Comp também disponibiliza contratos de manutenção personalizados, adaptados às necessidades operacionais específicas de cada cliente. Dentre os principais fabricantes atendidos, destacam-se marcas reconhecidas como Atlas Copco, Ingersoll Rand e Chicago Pneumatic."
    )
    story.append(Paragraph(servicos_text, styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("QUALIDADE DOS SERVIÇOS & MELHORIA CONTÍNUA", styles["Heading2"]))
    qualidade_text = (
        "A empresa investe continuamente na capacitação de sua equipe, na modernização de processos e no aprimoramento da estrutura de atendimento, garantindo alto padrão de atendimento qualidade, agilidade e eficácia nos serviços. "
        "Mantém ainda uma política ativa de melhoria contínua, com avaliações periódicas que visam atualizar tecnologias, aperfeiçoar métodos e garantir excelência técnica."
    )
    story.append(Paragraph(qualidade_text, styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("CONTE CONOSCO PARA UMA PARCERIA!", styles["Heading2"]))
    parceria_text = "Nossa missão é ser sua melhor parceria com sinônimos de qualidade, garantia e o melhor custo benefício."
    story.append(Paragraph(parceria_text, styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("CNPJ:22 790 603/0001 77 Contato: (11) 4543 6896/ 4543 6857 / 4357 8062", styles["Normal"]))
    story.append(PageBreak())

    # Página 4
    story.append(Paragraph("WORLD COMP DO BRASIL COMPRESSORES EIRELI", styles["Heading2"]))
    story.append(Paragraph("Rua Fernando Pessoa, 11 Bairro: Batistini,", styles["Normal"]))
    story.append(Paragraph("São Bernardo do Campo – SP Cep: 09844-390", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("COBERTURA TOTAL", styles["Heading2"]))
    cobertura_text = (
        "O Contrato de Locação cobre os serviços e manutenções, isso significa que não existem custos inesperados com o seu sistema de ar comprimido. "
        "O cronograma de manutenções preventivas é seguido à risca e gerenciado por um time de projetos para garantir o mais alto nível de eficiência. "
        "Além de você contar com a cobertura completa para reparos, intervenções emergenciais e atendimento proativo."
    )
    story.append(Paragraph(cobertura_text, styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("EQUIPAMENTO A SER OFERECIDO:", styles["Heading2"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph("COMPRESSOR DE PARAFUSO LUBRIFICADO REFRIGERADO A AR", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("CNPJ:22.790.603/0001-77 Contato: (11) 4543-6896/ 4543-6857 / 4357-8062", styles["Normal"]))
    story.append(PageBreak())

    # Página 5 - Comerciais e Tabelas
    story.append(Paragraph("WORLD COMP DO BRASIL COMPRESSORES EIRELI", styles["Heading2"]))
    story.append(Paragraph("Rua Fernando Pessoa, 11 Bairro: Batistini,", styles["Normal"]))
    story.append(Paragraph("São Bernardo do Campo – SP Cep: 09844-390", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("COMERCIAIS:", styles["Heading2"]))
    story.append(Spacer(1, 12))

    # Unidade Diadema
    story.append(Paragraph("Unidade Diadema", styles["Heading3"]))
    data_diadema = [
        ['Item', 'Qtd.', 'Descrição', 'Valor unitário', 'Período'],
        ['01', '03', 'Compressor de Ar Atlas Copco novo Modelo G160 , 440V/60Hz', '', '5 anos']
    ]
    table_diadema = Table(data_diadema, colWidths=[0.8*inch, 0.8*inch, 3*inch, 1.2*inch, 0.8*inch])
    table_diadema.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), beige),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, black)
    ]))
    story.append(table_diadema)
    story.append(Spacer(1, 6))
    story.append(Paragraph("VALOR MENSAL R$ 39.000,00", styles["Normal"]))
    story.append(Spacer(1, 12))

    # Unidade Anchieta
    story.append(Paragraph("Unidade Anchieta", styles["Heading3"]))
    data_anchieta = [
        ['Item', 'Qtd.', 'Descrição', 'Valor unitário', 'Período'],
        ['01', '01', 'Compressor de Ar Atlas Copco novo Modelo GA110 380cv', '', '5 anos']
    ]
    table_anchieta = Table(data_anchieta, colWidths=[0.8*inch, 0.8*inch, 3*inch, 1.2*inch, 0.8*inch])
    table_anchieta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), beige),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, black)
    ]))
    story.append(table_anchieta)
    story.append(Spacer(1, 6))
    story.append(Paragraph("VALOR MENSAL R$ 9.000,00", styles["Normal"]))
    story.append(Spacer(1, 12))

    # Unidade Ferraz
    story.append(Paragraph("Unidade Ferraz", styles["Heading3"]))
    data_ferraz = [
        ['Item', 'Qtd.', 'Descrição', 'Valor unitário', 'Período'],
        ['01', '04', 'Compressor de Ar Atlas Copco novo Modelo G160 440V/60Hz', '', '5 anos']
    ]
    table_ferraz = Table(data_ferraz, colWidths=[0.8*inch, 0.8*inch, 3*inch, 1.2*inch, 0.8*inch])
    table_ferraz.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), beige),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, black)
    ]))
    story.append(table_ferraz)
    story.append(Spacer(1, 6))
    story.append(Paragraph("VALOR MENSAL R$ 52.000,00", styles["Normal"]))
    story.append(Spacer(1, 12))

    # Unidade Jarinu
    story.append(Paragraph("Unidade Jarinu", styles["Heading3"]))
    data_jarinu = [
        ['Item', 'Qtd.', 'Descrição', 'Valor unitário', 'Período'],
        ['01', '02', 'Compressor de Ar Atlas Copco novo Modelo G160 , 440V/60Hz R', '', '5 anos'],
        ['02', '01', 'Compressor de Ar Atlas Copco novo Modelo GA55 380V R', '', '5 anos']
    ]
    table_jarinu = Table(data_jarinu, colWidths=[0.8*inch, 0.8*inch, 3*inch, 1.2*inch, 0.8*inch])
    table_jarinu.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), beige),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, black)
    ]))
    story.append(table_jarinu)
    story.append(Spacer(1, 6))
    story.append(Paragraph("VALOR MENSAL R$ 33.000,00", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("CNPJ:22.790.603/0001-77 Contato: (11) 4543-6896/ 4543-6857 / 4357-8062", styles["Normal"]))
    story.append(PageBreak())

    # Página 6 - Condições de Pagamento e Comerciais
    story.append(Paragraph("WORLD COMP DO BRASIL COMPRESSORES EIRELI", styles["Heading2"]))
    story.append(Paragraph("Rua Fernando Pessoa, 11 Bairro: Batistini,", styles["Normal"]))
    story.append(Paragraph("São Bernardo do Campo – SP Cep: 09844-390", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("CONDIÇÕES DE PAGAMENTO:", styles["Heading2"]))
    pagamento_text = (
        "O preço inclui: Uso do equipamento listado no Resumo da Proposta Preço, partida técnicos, serviços preventivos e corretivos, peças, deslocamento e acomodação dos técnicos, quando necessário. "
        "Pelos serviços objeto desta proposta, após a entrega do(s) equipamento(s) previsto(s) neste contrato, o CONTRATANTE deverá iniciar os respectivos pagamentos monetários referentes à contratação no valor de R$ _____ (_____ reais) taxa fixa mensal, com vencimento a 30 DDL, Dados estes que contará a partir da entrega do equipamento nas dependências do contratante, (COM FATURAMENTO ATRAVÉS DE RECIBO DE LOCAÇÃO)."
    )
    story.append(Paragraph(pagamento_text, styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("CONDIÇÕES COMERCIAIS", styles["Heading2"]))
    condicoes_text = [
        "• Os equipamentos desta proposta serão fornecidos em caráter de Locação, cujas regras dessa modalidade estão descritas nos Termos e Condições Gerais de Locação de Equipamento, parte integrante deste documento.",
        "• Assim que V. Sa. recebendo os equipamentos e materiais, entre em contato conosco para agendar o serviço de partida(s) técnica(s).",
        "• Validade do Contrato 5 anos",
        "• Informar sobre a necessidade de envio de documentos necessários para integração de técnicos.",
        "• Antes da compra do serviço, o cliente deve informar a World Comp, ou seu representante, se existem quaisquer riscos ou implicações em sua operação que possam provocar acidentes envolvendo as pessoas que realizarão o serviço, assim como as medidas de proteção ou outras ações necessárias que a World Comp deva tomar a fim de reduzir tais riscos.",
        "• É de responsabilidade do cliente fornecer todas as condições necessárias para a execução das manutenções, tais como equipamentos para elevação/transporte interno, iluminação, água e local adequados para limpeza de refrigeradores e demais componentes, mão de obra para eventuais necessidades, etc.",
        "• Os resíduos gerados pelas atividades da World Comp são de responsabilidade do cliente.",
        "• Todos os preços são para horário de trabalho definido como horário comercial, de segunda a sexta-feira, das 8h às 17h.",
        "• A World Comp não responsabiliza se perante o cliente, seus funcionários ou terceiros por perdas ou danos pessoais, diretos e indiretos, de imagem, lucros cessantes e perda econômica decorrentes dos serviços ora contratados ou de tipos de acidentes de quaisquer danos pelos equipamentos que sofrerão manutenção.",
    ]
    for item in condicoes_text:
        story.append(Paragraph(item, styles["Normal"]))
        story.append(Spacer(1, 3))
    story.append(PageBreak())

    # Página 7 - Termos (início)
    story.append(Paragraph("WORLD COMP DO BRASIL COMPRESSORES EIRELI", styles["Heading2"]))
    story.append(Paragraph("Rua Fernando Pessoa, 11 Bairro: Batistini,", styles["Normal"]))
    story.append(Paragraph("São Bernardo do Campo – SP Cep: 09844-390", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("TERMOS E CONDIÇÕES GERAIS DE LOCAÇÃO DE EQUIPAMENTO", styles["Heading2"]))
    story.append(Spacer(1, 12))
    termos_text = (
        "Pelo presente instrumento particular, <b>LOCADORA: WORLD COMP DP BRASIL COMPRESSORES EIRELI</b>, sociedade limitada com sede na Rua Fernando Pessoa, 17 Bairro Batistini – São Bernardo do Campo – São Paulo, CEP: 09844- 390, inscrita no CNPJ/MF sob nº. 22.790.603/0001-77, designado simplesmente como <b>WORLD COMP.</b> "
        "<b>LOCATÁRIA: _____</b> <b>WORLD COMP</b> e <b>CONTRATANTE</b> serão referidos individualmente como <b>Parte</b> e, em conjunto, <b>Partes.</b> As partes originais, por seus representantes legais ao finais, têm entre si apenas e acertado os presentes Termos e Condições Gerais de Localização de Equipamento, denominados simplesmente <b>Contrato</b>, que se regerá pelas cláusulas e condições seguintes, com efeitos a partir dos dados _____ da Proposta Comercial nº_____. "
        "<b>1 - CLÁUSULA PRIMEIRA – DO OBJETO</b> O presente Contrato consiste na contratação do(s) <b>Equipamento(s)</b> referência(s) NA Proposta Comercial Preço anexo, denominados simplesmente <b>Equipamento(s)</b>, de propriedade da <b>World Comp</b>, como parte da Locação de Compressores oferecidos ao <b>CONTRATANTE</b>, para uso em suas atividades industriais, sendo proibido o uso para outros fins. Caberá ao CONTRATANTE a obrigação de manter o(s) equipamento(s) em suas dependências, em endereço descrito como sua sede no preâmbulo do presente instrumento, obrigando-se a solicitar previamente e por escrito à World Comp eventual alteração de sua localização, sob pena de expressa e inequívoca violação do presente instrumento, o que autorizará a incidência de multa de 10% (dez por cento), em caráter não compensatório, sobre o valor do Contrato, bem como facultará à <b>World Comp</b> a rescisão do presente instrumento, com a retomada imediata liminar do(s) Equipamento(s). A Referida Proposta Comercial dispõe sobre as normas e especificações técnicas do(s) equipamento(s) localizado(s), bem como as condições comerciais para a presente locação. Caso ocorra qualquer alteração relevante nas condições de operação do(s) Equipamento(s) (tais como condições de operação, escopo do trabalho, ou ainda nas condições ambientais, qualidade do ar, ventilação, temperatura, fornecimento de água e energia elétrica) ou do local ou regime de trabalho do equipamento, a World Comp deverá ser notificada previamente, por escrito. Nessa hipótese, o presente Contrato deverá ser revisto pelas Partes, a fim de adaptá-lo à nova realidade, assumindo o <b>CONTRATANTE</b> responsabilidade integral antes da avaliação pela <b>Companhia Mundial</b> das novas condições e/ou da celebração de termo aditivo que reflita as novas condições."
    )
    story.append(Paragraph(termos_text, styles["Normal"]))
    story.append(PageBreak())

    # Página 8
    story.append(Paragraph("WORLD COMP DO BRASIL COMPRESSORES EIRELI", styles["Heading2"]))
    story.append(Paragraph("Rua Fernando Pessoa, 11 Bairro: Batistini,", styles["Normal"]))
    story.append(Paragraph("São Bernardo do Campo – SP Cep: 09844-390", styles["Normal"]))
    story.append(Spacer(1, 12))
    termos_text2 = (
        "Trabalho do equipamento, a A World Comp deverá ser notificada previamente, por escrito. Nessa hipótese, o presente Contrato deverá ser revisto pelas Partes, a fim de adaptá-lo à nova realidade, assumindo o <b>CONTRATANTE</b> responsabilidade integral antes da avaliação pela <b>Companhia Mundial</b> das novas condições e/ou da celebração de termo aditivo que reflita as novas condições. "
        "Estão incluídos no objeto deste instrumento: <b>Equipamento(s):</b> Equipamentos listados de acordo com relação descrita na Proposta Comercial Preço. Partida técnica do(s) Equipamento(s), sendo obrigatória sua realização somente, e exclusivamente, por funcionários especializados da World Comp, em local comercial, sendo de responsabilidade do CONTRATANTE a instalação do(s) equipamento(s) contratado(s) de acordo com o manual de instalação. "
        "Peças, componentes e insumos específicos para cada visita de manutenção preventiva ou corretiva. A World Comp, reserva o direito realizar as intervenções técnicas que entendem o bom funcionamento e manutenção do(s) equipamento(s), incluindo peças e produtos usados nas manutenções preventivas e/ou corretivas, em especial alterando o transporte utilizado conforme recomendação para melhor desempenho, consumo energético e extensão da vida útil do(s) <b>Equipamento(s)</b> e seus componentes. "
        "Estão excluídos do objeto deste instrumento: Atendimento para manutenções preventivas e/ou corretivas fora do horário comercial entendido como das 8:00h às 17:00h, de segunda a sexta-feira, salvo disposição em contrário na Proposta. "
        "Custos de componentes ou peças que tenham sido danificadas por negligência, mau uso, falha operacional ou elétrica do contratante. O presente Contrato abrange não apenas o(s) <b>Equipamento(s)</b> já relacionado na Proposta Comercial, mas também todos os demais que poderão vir a ser enviados..."
    )
    story.append(Paragraph(termos_text2, styles["Normal"]))
    story.append(PageBreak())

    # Página 9
    story.append(Paragraph("WORLD COMP DO BRASIL COMPRESSORES EIRELI", styles["Heading2"]))
    story.append(Paragraph("Rua Fernando Pessoa, 11 Bairro: Batistini,", styles["Normal"]))
    story.append(Paragraph("São Bernardo do Campo – SP Cep: 09844-390", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>3- CLÁUSULA TERCEIRA – DAS CONDIÇÕES DE PAGAMENTO</b>", styles["Normal"]))
    story.append(Spacer(1, 6))
    clausula3_text = (
        "3.1 O CONTRATANTE pagará à Comp World o valor descrito e em conformidade com as condições constantes da Proposta Comercial. "
        "3.1.2 O CONTRATANTE efetuará os pagamentos por meio de boleto bancário ou depósito em conta... "
        "5 - CLÁUSULA QUINTA - DAS RESPONSABILIDADES DO CONTRATANTE ..."
    )
    story.append(Paragraph(clausula3_text, styles["Normal"]))
    story.append(PageBreak())

    # Página 10
    story.append(Paragraph("WORLD COMP DO BRASIL COMPRESSORES EIRELI", styles["Heading2"]))
    story.append(Paragraph("Rua Fernando Pessoa, 11 Bairro: Batistini,", styles["Normal"]))
    story.append(Paragraph("São Bernardo do Campo – SP Cep: 09844-390", styles["Normal"]))
    story.append(Spacer(1, 12))
    clausula5_text = (
        "Código Civil. 5.1.4 Manter, na qualidade de único responsável pelo(s) Equipamento(s), a World Comp isenta de todas e quaisquer reclamações... "
        "5.1.21 Em caso de acidente de qualquer natureza envolvendo o(s) <b>Equipamento(s)</b>, o <b>CONTRATANTE</b> é responsável por fornecer notificação imediata e escrita à World Comp..."
    )
    story.append(Paragraph(clausula5_text, styles["Normal"]))
    story.append(PageBreak())

    # Página 11
    story.append(Paragraph("WORLD COMP DO BRASIL COMPRESSORES EIRELI", styles["Heading2"]))
    story.append(Paragraph("Rua Fernando Pessoa, 11 Bairro: Batistini,", styles["Normal"]))
    story.append(Paragraph("São Bernardo do Campo – SP Cep: 09844-390", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>6 - CLÁUSULA SEXTA – SEGURO</b>", styles["Normal"]))
    story.append(Spacer(1, 6))
    clausula6_text = (
        "6.1 O CONTRATANTE deverá providenciar o seguro do(s) Equipamento(s)... "
        "7 – CLÁUSULA SÉTIMA – RESCISÃO ..."
    )
    story.append(Paragraph(clausula6_text, styles["Normal"]))
    story.append(PageBreak())

    # Página 12
    story.append(Paragraph("WORLD COMP DO BRASIL COMPRESSORES EIRELI", styles["Heading2"]))
    story.append(Paragraph("Rua Fernando Pessoa, 11 Bairro: Batistini,", styles["Normal"]))
    story.append(Paragraph("São Bernardo do Campo – SP Cep: 09844-390", styles["Normal"]))
    story.append(Spacer(1, 12))
    clausula8_text = (
        "<b>8- CLÁUSULA OITAVA – CASO FORTUITO OU FORÇA MAIOR</b> ... "
        "<b>10- CLÁUSULA DÉCIMA – DAS DISPOSIÇÕES GERAIS</b> ... "
        "11.9 O presente Contrato e suas obrigações vinculam as Partes, seus herdeiros e sucessores a qualquer título."
    )
    story.append(Paragraph(clausula8_text, styles["Normal"]))
    story.append(PageBreak())

    # Página 13
    story.append(Paragraph("WORLD COMP DO BRASIL COMPRESSORES EIRELI", styles["Heading2"]))
    story.append(Paragraph("Rua Fernando Pessoa, 11 Bairro: Batistini,", styles["Normal"]))
    story.append(Paragraph("São Bernardo do Campo – SP Cep: 09844-390", styles["Normal"]))
    story.append(Spacer(1, 12))
    clausula11_text = (
        "11.10 O presente Contrato e os direitos e obrigações dele decorrentes não poderão ser cedidos... "
        "<b>11– CLÁUSULA DÉCIMA PRIMEIRA – FORO</b> ... "
        "São Bernardo do Campo, 25 de julho de 2025. _____ Contratante: CNPJ: _____ Contratada: WORLD COMP DO BRASIL COMPRESSORES EIRELI CNPJ: 22.790.603/0001-77 Testemunhas: _____ Nome: Nome: CPF: CPF:"
    )
    story.append(Paragraph(clausula11_text, styles["Normal"]))

    doc.build(story)


if __name__ == "__main__":
    gerar_pdf_locacao("exemplolocacao.pdf")

