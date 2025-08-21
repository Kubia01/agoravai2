from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.colors import black, blue, red, HexColor


def create_proposal_pdf(output_filename="proposta_comercial_replicada.pdf"):
    doc = SimpleDocTemplate(output_filename, pagesize=A4)
    styles = getSampleStyleSheet()

    # Definir estilos personalizados
    styles.add(ParagraphStyle(name='TitleStyle',
                             fontName='Helvetica-Bold',
                             fontSize=18,
                             alignment=TA_CENTER,
                             spaceAfter=14))
    styles.add(ParagraphStyle(name='SubtitleStyle',
                             fontName='Helvetica-Bold',
                             fontSize=12,
                             alignment=TA_LEFT,
                             spaceAfter=6))
    styles.add(ParagraphStyle(name='NormalText',
                             fontName='Helvetica',
                             fontSize=10,
                             alignment=TA_LEFT,
                             spaceAfter=6))
    styles.add(ParagraphStyle(name='BoldText',
                             fontName='Helvetica-Bold',
                             fontSize=10,
                             alignment=TA_LEFT,
                             spaceAfter=6))
    styles.add(ParagraphStyle(name='TableHeading',
                             fontName='Helvetica-Bold',
                             fontSize=10,
                             alignment=TA_CENTER,
                             spaceAfter=2))
    styles.add(ParagraphStyle(name='TableContent',
                             fontName='Helvetica',
                             fontSize=9,
                             alignment=TA_LEFT,
                             spaceAfter=2))

    story = []

    # --- Página 1: Cabeçalho e Introdução ---
    story.append(Paragraph("PROPOSTA COMERCIAL", styles['TitleStyle']))
    story.append(Paragraph("REF: CONTRATO DE LOCAÇÃO", styles['SubtitleStyle']))
    story.append(Spacer(1, 0.2 * inch))

    # Informações de Contato (simplificado)
    story.append(Paragraph("<b>Cliente:</b> ________________________", styles['NormalText']))
    story.append(Paragraph("<b>Data:</b> ________________________", styles['NormalText']))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("<b>De:</b> GRUPO DELGA", styles['NormalText']))
    story.append(Paragraph("WORLD COMP DO BRASIL", styles['NormalText']))
    story.append(Spacer(1, 0.2 * inch))

    # Saudação e Introdução
    intro_text = """Prezados Senhores: Agradecemos por nos conceder a oportunidade de apresentarmos nossa proposta para fornecimento de LOCAÇÃO DE COMPRESSOR DE AR. A World Comp Compressores é especializada em manutenção de compressores de parafuso das principais marcas do mercado, como Atlas Copco, Ingersoll Rand, Chicago. Atuamos também com revisão de equipamentos e unidades compressoras, venda de peças, bem como venda e locação de compressores de parafuso isentos de óleo e lubrificados. Com profissionais altamente qualificados e atendimento especializado, colocamo-nos à disposição para analisar, corrigir e prestar os devidos esclarecimentos, sempre buscando atender às especificações e necessidades dos nossos clientes. Atenciosamente, WORLD COMP DO BRASIL COMPRESSORES EIRELI"""
    story.append(Paragraph(intro_text, styles['NormalText']))
    story.append(Spacer(1, 0.3 * inch))

    # Seção "SOBRE A WORLD COMP"
    story.append(Paragraph("<b>SOBRE A WORLD COMP</b>", styles['SubtitleStyle']))
    about_text = """A World Comp Compressores é uma empresa com mais de uma década de atuação no mercado nacional, especializada na manutenção de compressores de ar do tipo parafuso. Seu atendimento abrange todo o território brasileiro, oferecendo soluções técnicas e comerciais voltadas à maximização do desempenho e da confiabilidade dos sistemas de ar comprimido utilizados por seus clientes."""
    story.append(Paragraph(about_text, styles['NormalText']))
    story.append(Spacer(1, 0.2 * inch))

    # Seção "NOSSOS SERVIÇOS"
    story.append(Paragraph("<b>NOSSOS SERVIÇOS</b>", styles['SubtitleStyle']))
    services_text = """A empresa oferece um portfólio completo de serviços, que contempla a manutenção preventiva e corretiva de compressores e unidades compressor as, a venda de peças de reposição para diversas marcas, a locação de compressores de parafuso — incluindo modelos lubrificados e isentos de óleo —, além da recuperação de unidades compressor as e trocadores de calor. A World Comp também disponibiliza contratos de manutenção personalizados, adaptados às necessidades operacionais específicas de cada cliente. Dentre os principais fabricantes atendidos, destacam-se marcas reconhecidas como Atlas Copco, Ingersoll Rand e Chicago Pneumatic."""
    story.append(Paragraph(services_text, styles['NormalText']))
    story.append(Spacer(1, 0.2 * inch))

    # Seção "QUALIDADE DOS SERVIÇOS & MELHORIA CONTÍNUA"
    story.append(Paragraph("<b>QUALIDADE DOS SERVIÇOS & MELHORIA CONTÍNUA</b>", styles['SubtitleStyle']))
    quality_text = """A empresa investe continuamente na capacitação de sua equipe, na modernização de processos e no aprimoramento da estrutura de atendimento, assegurando alto padrão de qualidade, agilidade e eficácia nos serviços. Mantém ainda uma política ativa de melhoria contínua, com avaliações periódicas que visam atualizar tecnologias, aperfeiçoar métodos e garantir excelência técnica."""
    story.append(Paragraph(quality_text, styles['NormalText']))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("<b>CONTE CONOSCO PARA UMA PARCERIA!</b>", styles['BoldText']))
    story.append(Paragraph("Nossa missão é ser sua melhor parceria com sinônimo de qualidade, garantia e o melhor custo benefício.", styles['NormalText']))
    story.append(Spacer(1, 0.3 * inch))

    # --- Página 2: Cobertura Total e Equipamentos Ofertados ---
    story.append(PageBreak())

    story.append(Paragraph("<b>COBERTURA TOTAL</b>", styles['SubtitleStyle']))
    coverage_text = """O Contrato de Locação cobre todos os serviços e manutenções, isso significa que não existe custos inesperados com o seu sistema de ar comprimido. O cronograma de manutenções preventivas é seguido à risca e gerenciado por um time de engenheiros especializados para garantir o mais alto nível de eficiência. Além de você contar com a cobertura completa para reparos, intervenções emergenciais e atendimento proativo completa para reparos, intervenções emergenciais e atendimento proativo."""
    story.append(Paragraph(coverage_text, styles['NormalText']))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("<b>EQUIPAMENTO A SER OFERTADO:</b>", styles['SubtitleStyle']))
    story.append(Paragraph("COMPRESSOR DE PARAFUSO LUBRIFICADO REFRIGERADO À AR", styles['NormalText']))
    story.append(Spacer(1, 0.3 * inch))

    story.append(Paragraph("<b>PROPOSTAS COMERCIAIS:</b>", styles['SubtitleStyle']))

    # Unidade Diadema
    story.append(Paragraph("<b>Unidade Diadema</b>", styles['BoldText']))
    data_diadema = [
        [Paragraph("Item", styles['TableHeading']), Paragraph("Qtd.", styles['TableHeading']), Paragraph("Descrição", styles['TableHeading']), Paragraph("Valor unitário", styles['TableHeading']), Paragraph("Período", styles['TableHeading'])],
        [Paragraph("01", styles['TableContent']), Paragraph("03", styles['TableContent']), Paragraph("Compressor de Ar Atlas Copco novo Modelo G160, 440V/60Hz", styles['TableContent']), "", Paragraph("5 anos", styles['TableContent'])]
    ]
    table_diadema = Table(data_diadema, colWidths=[0.8*inch, 0.8*inch, 3*inch, 1.2*inch, 1*inch])
    table_diadema.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#CCCCCC')),
        ('TEXTCOLOR', (0, 0), (-1, 0), black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#EEEEEE')),
        ('GRID', (0, 0), (-1, -1), 1, black),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(table_diadema)
    story.append(Paragraph("<b>VALOR MENSAL R$ 39.000,00</b>", styles['BoldText']))
    story.append(Spacer(1, 0.2 * inch))

    # Unidade Anchieta
    story.append(Paragraph("<b>Unidade Anchieta</b>", styles['BoldText']))
    data_anchieta = [
        [Paragraph("Item", styles['TableHeading']), Paragraph("Qtd.", styles['TableHeading']), Paragraph("Descrição", styles['TableHeading']), Paragraph("Valor unitário", styles['TableHeading']), Paragraph("Período", styles['TableHeading'])],
        [Paragraph("01", styles['TableContent']), Paragraph("01", styles['TableContent']), Paragraph("Compressor de Ar Atlas Copco novo Modelo GA110 380cv", styles['TableContent']), "", Paragraph("5 anos", styles['TableContent'])]
    ]
    table_anchieta = Table(data_anchieta, colWidths=[0.8*inch, 0.8*inch, 3*inch, 1.2*inch, 1*inch])
    table_anchieta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#CCCCCC')),
        ('TEXTCOLOR', (0, 0), (-1, 0), black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#EEEEEE')),
        ('GRID', (0, 0), (-1, -1), 1, black),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(table_anchieta)
    story.append(Paragraph("<b>VALOR MENSAL R$ 9.000,00</b>", styles['BoldText']))
    story.append(Spacer(1, 0.2 * inch))

    # Unidade Ferraz
    story.append(Paragraph("<b>Unidade Ferraz</b>", styles['BoldText']))
    data_ferraz = [
        [Paragraph("Item", styles['TableHeading']), Paragraph("Qtd.", styles['TableHeading']), Paragraph("Descrição", styles['TableHeading']), Paragraph("Valor unitário", styles['TableHeading']), Paragraph("Período", styles['TableHeading'])],
        [Paragraph("01", styles['TableContent']), Paragraph("04", styles['TableContent']), Paragraph("Compressor de Ar Atlas Copco novo Modelo G160 440V/60Hz", styles['TableContent']), "", Paragraph("5 anos", styles['TableContent'])]
    ]
    table_ferraz = Table(data_ferraz, colWidths=[0.8*inch, 0.8*inch, 3*inch, 1.2*inch, 1*inch])
    table_ferraz.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#CCCCCC')),
        ('TEXTCOLOR', (0, 0), (-1, 0), black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#EEEEEE')),
        ('GRID', (0, 0), (-1, -1), 1, black),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(table_ferraz)
    story.append(Paragraph("<b>VALOR MENSAL R$ 52.000,00</b>", styles['BoldText']))
    story.append(Spacer(1, 0.2 * inch))

    # Unidade Jarinu
    story.append(Paragraph("<b>Unidade Jarinu</b>", styles['BoldText']))
    data_jarinu = [
        [Paragraph("Item", styles['TableHeading']), Paragraph("Qtd.", styles['TableHeading']), Paragraph("Descrição", styles['TableHeading']), Paragraph("Valor unitário", styles['TableHeading']), Paragraph("Período", styles['TableHeading'])],
        [Paragraph("01", styles['TableContent']), Paragraph("02", styles['TableContent']), Paragraph("Compressor de Ar Atlas Copco novo Modelo G160, 440V/60Hz", styles['TableContent']), "", Paragraph("5 anos", styles['TableContent'])],
        [Paragraph("02", styles['TableContent']), Paragraph("01", styles['TableContent']), Paragraph("Compressor de Ar Atlas Copco novo Modelo GA55 380V", styles['TableContent']), "", Paragraph("5 anos", styles['TableContent'])]
    ]
    table_jarinu = Table(data_jarinu, colWidths=[0.8*inch, 0.8*inch, 3*inch, 1.2*inch, 1*inch])
    table_jarinu.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#CCCCCC')),
        ('TEXTCOLOR', (0, 0), (-1, 0), black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#EEEEEE')),
        ('GRID', (0, 0), (-1, -1), 1, black),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(table_jarinu)
    story.append(Paragraph("<b>VALOR MENSAL R$ 33.000,00</b>", styles['BoldText']))
    story.append(Spacer(1, 0.3 * inch))

    # --- Página 3: Condições de Pagamento e Comerciais ---
    story.append(PageBreak())

    story.append(Paragraph("<b>CONDIÇÕES DE PAGAMENTO:</b>", styles['SubtitleStyle']))
    payment_intro = """O preço inclui: Uso do equipamento listado no Resumo da Proposta Preço, partida técnica, serviços preventivos e corretivos, peças, deslocamento e acomodação dos técnicos, quando necessário. Pelos serviços objeto desta proposta, após a entrega do(s) equipamento(s) previsto neste contrato, o CONTRATANTE deverá iniciar os respectivos pagamentos mensais referentes a locação no valor de R$ __________ (______________reais) taxa fixa mensal, com vencimento à 30 DDL, Data esta que contará a partir da entrega do equipamento nas dependencias da contratante, (COM FATURAMENTO ATRAVÉS DE RECIBO DE LOCAÇÃO)."""
    story.append(Paragraph(payment_intro, styles['NormalText']))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("<b>CONDIÇÕES COMERCIAIS</b>", styles['SubtitleStyle']))
    commercial_conditions = [
        "Os equipamentos objetos desta proposta serão fornecidos em caráter de Locação, cujas regras dessa modalidade estão descritas nos Termos e Condições Gerais de Locação de Equipamento, parte integrante deste documento.",
        "Assim que V. Sa. receber os equipamentos e materiais, entrar em contato conosco para agendar o serviço de partida(s) técnica(s).",
        "Validade do Contrato 5 anos",
        "Informar sobre a necessidade de envio de documentos necessários para integração de técnicos.",
        "Antes da compra do serviço, o cliente deve informar a World Comp, ou seu representante, se existem quaisquer riscos ou circunstâncias na sua operação que possam provocar acidentes envolvendo as pessoas que realizarão o serviço, assim como as medidas de proteção ou outras ações necessárias que a World Comp deva tomar a fim de reduzir tais riscos.",
        "É de responsabilidade do cliente fornecer todas as condições necessárias para a execução das manutenções, tais como equipamentos para elevação/transporte interno, iluminação, água e local adequados para limpeza de resfriadores e demais componentes, mão de obra para eventuais necessidades, etc.",
        "Os resíduos gerados pelas atividades da World Comp são de responsabilidade do cliente.",
        "Todos os preços são para horário de trabalho definido como horário comercial, de segunda a sexta-feira, das 8h às 17h.",
        "A World Comp não se responsabiliza perante o cliente, seus funcionários ou terceiros por perdas ou danos pessoais, diretos e indiretos, de imagem, lucros cessantes e perda econômica decorrentes dos serviços ora contratados ou de acidentes de qualquer tipo causados pelos equipamentos que sofrerão manutenção."
    ]
    for item in commercial_conditions:
        story.append(Paragraph(f"• {item}", styles['NormalText']))
    story.append(Spacer(1, 0.3 * inch))

    # --- Página 4: Termos e Condições Gerais de Locação (Início) ---
    story.append(PageBreak())

    story.append(Paragraph("<b>TERMOS E CONDIÇÕES GERAIS DE LOCAÇÃO DE EQUIPAMENTO</b>", styles['SubtitleStyle']))
    story.append(Paragraph("Pelo presente instrumento particular,", styles['NormalText']))
    story.append(Paragraph("<b>LOCADORA:</b> WORLD COMP DP BRASIL COMPRESSORES EIRELI, sociedade limitada com sede na Rua Fernando Pessoa, 17 Bairro Batistini – São Bernardo do Campo – São Paulo, CEP: 09844-390, inscrita no CNPJ/MF sob nº. 22.790.603/0001-77, denominada simplesmente como <b>WORLD COMP</b>.", styles['NormalText']))
    story.append(Paragraph("<b>LOCATÁRIA:</b> __________________________________", styles['NormalText']))
    story.append(Paragraph("WORLD COMP e CONTRATANTE serão referidas individualmente como Parte e, em conjunto, Partes.", styles['NormalText']))
    story.append(Paragraph("As partes qualificadas, por seus representantes legais ao final assinados, têm entre si justo e acertado os presentes Termos e Condições Gerais de Locação de Equipamento, denominado simplesmente Contrato, que se regerá pelas cláusulas e condições seguintes, com efeitos a partir da data _________ da Proposta Comercial nº ___________________.", styles['NormalText']))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("<b>1 - CLÁUSULA PRIMEIRA – DO OBJETO</b>", styles['BoldText']))
    clause1_text = """O presente Contrato consiste na locação do(s) Equipamento(s) mencionado(s) NA Proposta Comercial Preço anexa, denominados simplesmente Equipamento(s), de propriedade da World Comp, como parte da Locação de Compressores oferecida ao CONTRATANTE, para uso em suas atividades industriais, sendo proibido o uso para outros fins. Caberá ao CONTRATANTE a obrigação de manter o(s) Equipamento(s) em suas dependências, em endereço descrito como sua sede no preâmbulo do presente instrumento, obrigando-se a solicitar previamente e por escrito à World Comp eventual alteração de sua localização, sob pena de expressa e inequívoca violação do presente instrumento, o que autorizará a incidência de multa de 10% (dez por cento), em caráter não compensatório, sobre o valor do Contrato, bem como facultará à World Comp a rescisão do presente instrumento, com a imediata retomada liminar do(s) Equipamento(s). Referida Proposta Comercial dispõe as descrições e especificações técnicas do(s) equipamento(s) locado(s), bem como as condições comerciais para a presente locação. Caso ocorra qualquer alteração relevante nas condições de operação dos Equipamento(s) (tais como condições de operação, escopo do trabalho, ou ainda nas condições ambientais, qualidade do ar, ventilação, temperatura, fornecimento de água e energia elétrica) ou do local ou regime de trabalho do equipamento, a World Comp deverá ser notificada previamente, por escrito. Nessa hipótese, o presente Contrato deverá ser revisto pelas Partes, a fim de adaptá-lo à nova realidade, assumindo a CONTRATANTE integral responsabilidade antes da avaliação pela World Comp das novas condições e/ou da celebração de termo aditivo que reflita as novas condições."""
    story.append(Paragraph(clause1_text, styles['NormalText']))
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("Estão incluídos no objeto deste instrumento:", styles['BoldText']))
    included_items = [
        "Equipamento(s): Equipamentos listados de acordo com relação descrita na Proposta Comercial Preço.",
        "Partida técnica dos Equipamento(s), sendo obrigatório sua realização somente, e exclusivamente, por funcionários especializados da World Comp, em horário comercial, sendo de responsabilidade do CONTRATANTE a instalação do(s) equipamento(s) contratados de acordo com o manual de instalação.",
        "Peças, componentes e insumos específicos para cada visita de manutenção preventiva ou corretiva",
        "A World Comp, reserva o direito realizar as intervenções técnicas que entender necessárias para o bom funcionamento e manutenção do(s) Equipamento(s), incluindo substituição de peças e produtos utilizados nas manutenções preventivas e/ou corretivas, em especial alterando o lubrificante utilizado conforme recomendação para melhor desempenho, consumo energético e extensão da vida útil do(s) Equipamento(s) e seus componentes."
    ]
    for item in included_items:
        story.append(Paragraph(f"• {item}", styles['NormalText']))
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("Estão excluídos do objeto deste instrumento:", styles['BoldText']))
    excluded_items = [
        "Atendimento para manutenções preventivas e/ou corretivas fora do horário comercial entendido como das 8:00h às 17:00h, de segunda a sexta-feira, salvo especificação em contrário na Proposta.",
        "Custos com componentes ou peças que tenham sido danificados por negligência, mau uso, falha operacional ou elétrica da contratante."
    ]
    for item in excluded_items:
        story.append(Paragraph(f"• {item}", styles['NormalText']))
    story.append(Spacer(1, 0.1 * inch))

    clause1_end_text = """O presente Contrato, alcança não apenas o(s) Equipamento(s) já relacionados na Proposta Comercial, mas também todos os demais que poderão vir a ser enviados, através de solicitação do CONTRATANTE, conforme as respectivas propostas comerciais futuras, e por meio de Notas Fiscais de Remessa emitidas pela World Comp e termos aditivos a serem celebrados entre as Partes."""
    story.append(Paragraph(clause1_end_text, styles['NormalText']))
    story.append(Spacer(1, 0.2 * inch))

    # Fechar documento
    doc.build(story)
    print(f"PDF '{output_filename}' criado com sucesso!")


if __name__ == "__main__":
    create_proposal_pdf()

