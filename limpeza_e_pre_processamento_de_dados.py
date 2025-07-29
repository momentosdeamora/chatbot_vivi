import json
import os
import re

class PreProcessamentoCentrosLGBTI:
    def __init__(self, caminho_arquivo):
        self.caminho_arquivo = caminho_arquivo
        self.paragrafos = {}
        self.centros = []


    def ler_arquivo(self):
        with open(self.caminho_arquivo, 'r', encoding='utf-8') as f:
            return f.read()


    def limpar_texto(self, texto):
        return re.sub(r'[\r]', '', texto).strip()


    def extrair_paragrafos(self, texto):
        paragrafos_regex = [
            r"Centros de Cidadania LGBTI\+",
            r"Os Centros de Cidadania LGBTI\+.*?respeito à diversidade sexual\.",
            r"Os equipamentos atuam a partir de dois eixos:.*?todo o público LGBTI\.",
            r"Acesse aqui o Manual dos Centros de Cidadania LGBTI\."
        ]
        
        for i, regex in enumerate(paragrafos_regex, start=1):
            matches = re.findall(regex, texto, re.IGNORECASE | re.DOTALL)
            if matches:
                self.paragrafos[f"paragrafo_{i}"] = matches[0].strip()

        return self.paragrafos
    

    def extrair_centros(self, texto):
        texto_apos_enderecos = re.split(r'Endereços', texto, flags=re.IGNORECASE)[-1]

        padrao_centro = re.compile(r'(Centro.*?)\n(.*?)\n(.*?)\nTelefone: (.*?)\n(.*?@.*?)(?=\n|$)', re.IGNORECASE | re.DOTALL)
        
        for match in padrao_centro.finditer(texto_apos_enderecos):
            nome_zona = match.group(1)
            endereco = match.group(2).strip()
            horario = match.group(3).strip()
            telefones = [tel.strip() for tel in match.group(4).split('/') if tel.strip()]
            email = match.group(5).strip()

            zona = re.search(r'\((.*?)\)', nome_zona)
            zona = zona.group(1) if zona else "Desconhecida"

            self.centros.append({
                "nome": nome_zona,
                "zona": zona,
                "endereco": endereco,
                "horario": horario,
                "telefone": telefones,
                "email": email
            })


    def salvar_json(self, caminho_saida):
        dados = {
            "paragrafos": self.paragrafos,
            "centros": self.centros
        }
        with open(caminho_saida, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)


    def executar(self, caminho_saida):
        texto = self.ler_arquivo()
        texto_limpo = self.limpar_texto(texto)
        self.extrair_paragrafos(texto_limpo)
        self.extrair_centros(texto_limpo)
        self.salvar_json(caminho_saida)


class PreProcessamentoEtapa1Limpeza:
    def __init__(self, caminho_arquivo):
        self.caminho_arquivo = caminho_arquivo
        self.nome_arquivo = os.path.basename(caminho_arquivo)
        self.nome_limpo = self.nome_arquivo.replace(".txt", "_etapa_1_limpo.txt")
        self.pasta_saida = "dados_limpos_e_pre_processados"
        os.makedirs(self.pasta_saida, exist_ok=True)


    def ler_arquivo(self):
        with open(self.caminho_arquivo, "r", encoding="utf-8") as f:
            return f.readlines()


    def limpar_linhas(self, linhas):
        texto_limpo = []
        paragrafo = ""

        for linha in linhas:
            linha = linha.strip()
            if linha == "":
                if paragrafo:
                    texto_limpo.append(paragrafo.strip())
                    paragrafo = ""
            else:
                paragrafo += " " + linha

        if paragrafo:
            texto_limpo.append(paragrafo.strip())

        return "\n\n".join(texto_limpo)


    def ajustes_finais(self, texto):
        texto = re.sub(r"\s+", " ", texto)
        texto = re.sub(r"\s*\n\s*", "\n\n", texto)
        return texto.strip()


    def salvar_texto_limpo(self, texto):
        caminho_saida = os.path.join(self.pasta_saida, self.nome_limpo)
        with open(caminho_saida, "w", encoding="utf-8") as f:
            f.write(texto)
        print(f"Texto limpo salvo em: {caminho_saida}")


    def processar(self):
        linhas = self.ler_arquivo()
        texto_bruto = self.limpar_linhas(linhas)
        texto_final = self.ajustes_finais(texto_bruto)
        self.salvar_texto_limpo(texto_final)


class PreProcessadorEtapa2ComoAgirEmCasosDeViolenciaDomestica:
    def __init__(self, caminho_arquivo):
        self.caminho_arquivo = caminho_arquivo
        self.nome_arquivo = os.path.basename(caminho_arquivo)
        self.nome_json = "como_agir_em_casos_de_violencia_domestica_durante_o_isolamento_social_etapa_2_limpo_e_pre_processado"
        self.pasta_saida = "dados_limpos_e_pre_processados"
        os.makedirs(self.pasta_saida, exist_ok=True)


    def ler_texto_unico(self):
        with open(self.caminho_arquivo, "r", encoding="utf-8") as f:
            return f.read()


    def extrair_titulo_e_fonte(self, texto):
        padrao = re.compile(
            r'(COMO AGIR EM CASOS DE VIOLÊNCIA DOMÉSTICA DURANTE O ISOLAMENTO SOCIAL)(.*?)\b([A-Z0-9.-]+\.ORG)\b',
            flags=re.IGNORECASE | re.DOTALL
        )
        resultado = padrao.search(texto)
        if resultado:
            titulo = resultado.group(1).strip()
            fonte_primaria = resultado.group(3).strip()
            texto_restante = texto[:resultado.start()] + texto[resultado.end():]
            texto_restante = texto_restante.strip()
            return titulo, fonte_primaria, texto_restante
        else:
            return "", "", texto.strip()


    def separar_por_categorias(self, frases):
        categorias = {
            "contexto_social": [],
            "apoio_emocional_e_familiar": [],
            "violencia_psicologica": [],
            "medidas_emergenciais": [],
            "como_denunciar": [],
            "direitos_de_pessoas_lgbti+": [],
            "violencia_sexual_e_protocolo_saude": [],
            "telefones_importantes": [],
            "mensagem_final": [],
            "creditos": [],
            "procurar_delegacia": []
        }

        frase_destaque = "A melhor ferramenta contra a violência é a denúncia!"

        for frase in frases:
            frase = frase.strip()
            if not frase:
                continue

            frase_lower = frase.lower()
            print(f"\n\nAnalisando frase: {frase}\n\n")

            if re.search(r"\bcvv\b|\b180\b|\b190\b|\b188\b|disque 100", frase_lower):
                categorias["telefones_importantes"].append(frase)
                continue

            if frase_destaque.lower() in frase_lower:
                if frase_lower == frase_destaque.lower():
                    categorias["mensagem_final"].append(frase)
                else:
                    partes = re.split(re.escape(frase_destaque), frase, flags=re.IGNORECASE)
                    categorias["mensagem_final"].append(frase_destaque)
                    resto = "".join(partes).strip()
                    if resto:
                        categorias["creditos"].append(resto)
                continue

            if "copyright" in frase_lower or "criado por" in frase_lower or "benevides" in frase_lower:
                categorias["creditos"].append(frase)
                continue

            if frase == "Se possível vá para outro cômodo e tente manter a calma":
                categorias["violencia_psicologica"].append(frase)
                continue

            if any(p in frase_lower for p in [
                "violência física ou sexual",
                "violência contra a criança ou adolescente"
            ]) or "delegacia de polícia" in frase_lower:
                frase_base = "Procure imediatamente uma Delegacia de Polícia nos seguintes casos: violência contra a mulher, violência física ou sexual, ou violência contra a criança ou adolescente."
                if frase_base not in categorias["procurar_delegacia"]:
                    categorias["procurar_delegacia"].append(frase_base)
                continue

            if any(p in frase_lower for p in [
                "converse", "familia", "saúde mental", "mantenha-se estável",
                "lgbti+", "conviver em ambientes tóxicos"
            ]):
                categorias["apoio_emocional_e_familiar"].append(frase)
                continue

            if any(p in frase_lower for p in [
                "violência psicológica", "respire", "xingamento",
                "afaste-se", "mantenha distância"
            ]):
                categorias["violencia_psicologica"].append(frase)
                continue

            if any(p in frase_lower for p in [
                "controle", "vizinho", "grave", "áudio", "vídeo", "ajuda"
            ]):
                categorias["medidas_emergenciais"].append(frase)
                continue

            if any(p in frase_lower for p in [
                "registro", "denúncia", "flagrante", "urgência"
            ]) and "delegacia" not in frase_lower:
                categorias["como_denunciar"].append(frase)
                continue

            if any(p in frase_lower for p in [
                "travestis", "transexuais", "lésbica", "lei maria da penha"
            ]):
                categorias["direitos_de_pessoas_lgbti+"].append(frase)
                continue

            if any(p in frase_lower for p in [
                "violência sexual", "pep", "pílula do dia seguinte", "unidade de saúde"
            ]):
                categorias["violencia_sexual_e_protocolo_saude"].append(frase)
                continue

            if "cuide da sua vida" in frase_lower or "temos muitos dias pela frente" in frase_lower:
                categorias["mensagem_final"].append(frase)
                continue

            if any(p in frase_lower for p in [
                "isolamento social", "quarentena", "álcool", "uso abusivo",
                "risco de violência", "org há pesquisas", "períodos de isolamento",
                "homens têm maior dificuldade"
            ]):
                categorias["contexto_social"].append(frase)
                continue

            categorias["contexto_social"].append(frase)

        if categorias["creditos"]:
            categorias["creditos"] = [" ".join(categorias["creditos"]).strip()]

        return categorias


    def salvar_json(self, dados_classificados):
        caminho_json = os.path.join(self.pasta_saida, self.nome_json)
        with open(caminho_json, "w", encoding="utf-8") as f:
            json.dump(dados_classificados, f, indent=4, ensure_ascii=False)
        print(f"JSON automatizado salvo como '{caminho_json}'.")


    def processar(self):
        texto_original = self.ler_texto_unico()

        titulo, fonte_primaria, texto_para_segmentar = self.extrair_titulo_e_fonte(texto_original)

        frases = re.split(r'\.\s+|\.$', texto_para_segmentar)

        dados_organizados = self.separar_por_categorias(frases)

        dados_organizados["titulo"] = [titulo] if titulo else []
        dados_organizados["fonte_primaria"] = [fonte_primaria] if fonte_primaria else []

        self.salvar_json(dados_organizados)


class PreProcessadorEtapa2OQueFazerEmCasoDeViolenciaLgbtfobica:
    def __init__(self, caminho_arquivo):
        self.caminho_arquivo = caminho_arquivo
        self.texto_completo = self._carregar_texto_do_arquivo()
        self.titulos_secoes = [
            "1. o que é lgbtifobia?",
            "2. a importância da denúncia",
            "3. tipos de violência",
            "4. o que não fazer",
            "5. não desista!",
            "6. não recue!",
            "7. incentive mais denúncias e de como proceder",
            "8. o que fazer:",
            "8.1. registrar boletim de ocorrência policial",
            "8.2. identificar possíveis testemunhas",
            "8.3 levar as provas que conseguir para instruir a notícia-crime",
            "8.4. buscar orientação jurídica",
            "i. acompanhar o oferecimento da denúncia ou da queixa-crime",
            "ii. existe o risco de o crime de injúria racial prescrever?",
            "iii. atentar para todas as fases do processo",
            "9. como ajudar uma vítima a efetivar a denúncia?",
            "9.1. escute e acredite em sua história",
            "9.2. não deixe a vítima sozinha",
            "9.3. sugira buscar ajuda em outros lugares além da delegacia",
            "10. exemplos clássicos de lgbtifobia que podem ser denunciados",
            "11. violência lgbtifóbica no ambiente virtual",
            "11.1 lgbtifobia e cyberbullying",
            "11.2 espaço virtual, consequências reais",
            "11.3 acesso à justiça e apoio nos casos de violência na internet",
            "11.4 como denunciar",
            "11.5 fazendo o boletim de ocorrência online"
        ]


    def _carregar_texto_do_arquivo(self):
        try:
            with open(self.caminho_arquivo, 'r', encoding='utf-8') as f:
                texto = f.read()
                print(f"\n[INFO] Texto carregado com sucesso. Total de caracteres: {len(texto)}")
                print(f"[INFO] Prévia do texto:\n{texto[:500]}...\n")
                return texto
        except FileNotFoundError:
            raise IOError(f"O arquivo não foi encontrado: {self.caminho_arquivo}")
        except Exception as e:
            raise IOError(f"Erro ao ler o arquivo {self.caminho_arquivo}: {e}")


    def _pre_processar_texto(self, texto):
        texto_limpo = re.sub(r'O que fazer em caso de violência LGBTIfóbica\?\s*\d*\s*', '', texto, flags=re.IGNORECASE).strip()
        print(f"[INFO] Texto após pré-processamento. Total de caracteres: {len(texto_limpo)}")
        return texto_limpo.lower()


    def processar_para_dicionario(self):
        if not self.texto_completo:
            print("[WARN] Nenhum texto foi carregado.")
            return {}

        dados_processados = {}
        texto_processado = self._pre_processar_texto(self.texto_completo)

        titulos_ordenados = sorted(self.titulos_secoes, key=len, reverse=True)
        posicoes_secoes = []

        print(f"[INFO] Iniciando busca pelos títulos no texto...")
        for titulo in titulos_ordenados:
            pattern = re.compile(r'(?<!\S)' + re.escape(titulo) + r'(?=\s+|$)', re.IGNORECASE)
            matches = list(pattern.finditer(texto_processado))
            if matches:
                for match in matches:
                    posicoes_secoes.append({'titulo': titulo, 'inicio': match.start()})
                print(f"[DEBUG] Encontrado: '{titulo}' - Ocorrências: {len(matches)}")
            else:
                print(f"[DEBUG] NÃO encontrado: '{titulo}'")

        posicoes_secoes.sort(key=lambda x: x['inicio'])

        outros = []
        fim_anterior = 0

        for i, secao in enumerate(posicoes_secoes):
            titulo = secao['titulo']
            inicio = secao['inicio']
            fim = posicoes_secoes[i + 1]['inicio'] if i + 1 < len(posicoes_secoes) else len(texto_processado)

            # Coleta texto entre fim anterior e início atual como "outros" (se não for vazio)
            if fim_anterior < inicio:
                trecho_outros = texto_processado[fim_anterior:inicio].strip()
                if trecho_outros:
                    outros.append(trecho_outros)

            # Captura o conteúdo da seção
            texto_secao = texto_processado[inicio:fim].strip()
            match = re.match(r'(?<!\S)' + re.escape(titulo) + r'\s*', texto_secao, re.IGNORECASE)
            conteudo = texto_secao[match.end():].strip() if match else texto_secao

            dados_processados[titulo] = conteudo
            fim_anterior = fim
            
        if outros:
            texto_outros = "\n\n".join(outros)

            dados_processados["outros_paragrafos"] = {
                "créditos": (
                    "cartilha de orientações à população lgbti no combate à lgbtifobia o que fazer em caso de violência "
                    "lgbtifóbica bruna g. benevides | @brunabenevidex 2ª sargenta da marinha do brasil paulo iotti | "
                    "@pauloiotti advogado anderson cavichioli | @renosplgbti presidente da renosp-lgbti delegado de polícia "
                    "civil isaac porto | @iporto consultor lgbti para o instituto sobre raça, igualdade e direitos humanos "
                    "raykka rica | @distritodrag membro do distrito drag texto e pesquisa revisão técnica revisão ortográfica "
                    "projeto gráfico e diagramação associação nacional de travestis e transexuais antra associação brasileira "
                    "de lésbicas, gays, bissexuais, travestis, transexuais e intersexos abglt copyright©2020 por bruna g. "
                    "benevides permitida a reprodução total ou parcial desta publicação, desde que citadas as fontes. rio de janeiro - 2020"
                ),
                "apresentação": (
                    "durante diversos períodos deste ano, o governo federal, através de sua nova cúpula nomeada, comandada e "
                    "alinhada com fundamentalistas religiosos e reacionários(as) morais, tem se colocado contra a decisão do stf, "
                    "que, embora não tenha legislado nem praticado analogia in malam partem, reconheceu a mora do estado em garantir "
                    "proteção específica na forma da lei à população lgbti+, vítima de diversos tipos de violências (psicológicas, "
                    "sexuais, físicas e simbólicas), socialmente difundidas de forma estrutural, sistemática, institucional e histórica. "
                    "da mesma forma, o governo tem cassado direitos, retrocedido em temas que havíamos avançado e tem cada vez mais se "
                    "mostrado anti-lgbti+, pautando uma agenda antigênero e especialmente contra direitos sociais e políticos das pessoas trans."
                ),
                "decisão_do_stf": (
                    "em 2019, foi julgado pelo supremo tribunal federal a ação direta de inconstitucionalidade por omissão (ado 26). "
                    "nesse julgamento, reconheceu-se a inconstitucionalidade na demora do congresso nacional em legislar sobre a proteção penal "
                    "à população lgbti+, interpretando conforme a constituição federal para enquadrar a homofobia e a transfobia, ou qualquer que "
                    "seja a forma da sua manifestação, nos diversos tipos penais definidos em legislação já existente, como a lei federal 7.716/1989 "
                    "(que define os crimes de racismo). a tese defendida no julgado entende que as práticas lgbtifóbicas constituem uma forma de "
                    "racismo social, considerando que tais condutas segregam e inferiorizam pessoas lgbti. (giowanna cambrone)"
                ),
                "dados_do_dossiê": (
                    "em recente dossiê lançado pela antra e ibte, pode-se constatar que o brasil segue como o país que mais assassina pessoas "
                    "trans do mundo. o dossiê também traz um dado alarmante sobre uma pesquisa realizada por ocasião do mês de enfrentamento da "
                    "lgbtifobia no mundo, segundo a qual que 99% das pessoas lgbti+ participantes afirmaram não se sentirem seguras no país."
                ),
                "objetivo_cartilha": (
                    "desta forma, esta cartilha tem como objetivo principal trazer informações para o enfrentamento das violências e violações "
                    "dos direitos humanos de lésbicas, gays, bissexuais, travestis, transexuais e intersexos e demais minorias sexuais e de gênero "
                    "(lgbti+), indicando caminhos a serem tomados para possibilitar o enquadramento eficaz da lgbtifobia estrutural a partir da "
                    "decisão do stf através do mi 4733, impetrado pela abglt, e da ado 26, apresentada pelo pps (hoje chamado de cidadania)."
                ),
                "link_fontes": (
                    "cf. vecchiatti, paulo roberto iotti. disponível em: https://www.conjur.com.br/2019-ago-19/paulo-iotti-stf-nao-legislou-equipararhomofobia-racismo\n"
                    "dossiê da antra: https://antrabrasil.org/assassinatos/\n"
                    "isp/rj: http://www.rio.rj.gov.br/dlstatic/10112/8528204/4225954/dossielgbt1.pdf"
                )
            }

            print(f"[INFO] Blocos organizados por tema em 'outros_paragrafos'")

        return dados_processados


    def salvar_para_json(self, dados, nome_arquivo_json, indentacao=4):
        try:
            with open(nome_arquivo_json, 'w', encoding='utf-8') as f:
                json.dump(dados, f, ensure_ascii=False, indent=indentacao)
            print(f"[SUCESSO] Dados salvos em '{nome_arquivo_json}'")
        except Exception as e:
            raise IOError(f"Erro ao salvar dados para o arquivo JSON '{nome_arquivo_json}': {e}")


if __name__ == "__main__":
    caminho_do_arquivo_txt = "dados_limpos_e_pre_processados\o_que_fazer_em_caso_de_violencia_lgbtfobica_etapa_1_limpo.txt"
    nome_do_arquivo_json_saida = "dados_limpos_e_pre_processados\o_que_fazer_em_caso_de_violencia_lgbtfobica_etapa_2_limpo_e_pre_processado.json"

    try:
        processador = PreProcessadorEtapa2OQueFazerEmCasoDeViolenciaLgbtfobica(caminho_do_arquivo_txt)
        dicionario_resultante = processador.processar_para_dicionario()
        processador.salvar_para_json(dicionario_resultante, nome_do_arquivo_json_saida)

        print("\n--- Dicionário Final ---")
        for chave, conteudo in dicionario_resultante.items():
            print(f"{chave} → {conteudo[:100]}...")

    except IOError as e:
        print(f"[ERRO DE ARQUIVO] {e}")
    except Exception as e:
        print(f"[ERRO GERAL] {e}")
