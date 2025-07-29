import hashlib
import json
import os
import re
import time
from difflib import SequenceMatcher

import faiss
import redis
import torch

from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoProcessor, AutoModelForImageTextToText

import opik
from opik.evaluation.metrics import Equals, Contains, RegexMatch, LevenshteinRatio

opik.configure(workspace="chatbot_vivi", use_local=True, automatic_approvals=True)

metrica_e_igual_a = Equals()
metrica_contem = Contains(case_sensitive=False)
metrica_regex = RegexMatch(regex=r"Centro\s+de\s+Refer[eê]ncia\s+LGBTI\+?\s+Laura\s+Vermont")
metrica_levenshtein = LevenshteinRatio()

class RAGPipeline:
    
    def __init__(self, nome_modelo: str, nome_modelo_ollama_avaliador: str, caminho_faiss: str, caminho_id_texto: str, modelo_embedding: str = "sentence-transformers/all-MiniLM-L6-v2", redis_host='localhost', redis_port=6379, redis_db=0, arquivo_log="log.json"):
        print("\nEtapa 1: Carregando tokenizer...\n")
        self.nome_modelo = nome_modelo


        print("\nEtapa 2: Detectando dispositivo...\n")
        self.nome_modelo_ollama_avaliador = nome_modelo_ollama_avaliador
        

        self.tokenizer = AutoTokenizer.from_pretrained(nome_modelo)


        print("\nEtapa 3: Carregando modelo principal...\n")
        self.dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
        
        
        self.modelo = AutoModelForCausalLM.from_pretrained(
            nome_modelo,
            device_map="auto" if self.dispositivo == "cuda" else None,
            torch_dtype=torch.float16 if self.dispositivo == "cuda" else torch.float32
        )
        
        
        self.modelo.to(self.dispositivo)

        
        print("\nEtapa 4: Carregando modelo de embedding...\n")
        self.embedding_model = SentenceTransformer(modelo_embedding)

        
        print("\nEtapa 5: Carregando índice FAISS...\n")
        self.indice = faiss.read_index(caminho_faiss)

        
        print("\nEtapa 6: Lendo id_para_texto...\n")
        with open(caminho_id_texto, "r", encoding="utf-8") as f:
            self.id_para_texto = json.load(f)


        print("\nEtapa 7: Conectando ao Redis...\n")
        self.redis = redis.Redis(host=redis_host, port=redis_port, db=redis_db)


        print("\nEtapa 8: Verificando arquivo de log...\n")
        self.arquivo_log = arquivo_log

        try:
            with open(self.arquivo_log, "r", encoding="utf-8") as f:
                pass
        except FileNotFoundError:
            with open(self.arquivo_log, "w", encoding="utf-8") as f:
                json.dump([], f)

        print("*" * 150)
        print("\n\nRAGPipeline inicializado com sucesso.\n\n")
        print("*" * 150)


    def registrar_log(self, evento: dict):
        try:
            with open(self.arquivo_log, "r+", encoding="utf-8") as f:
                dados = json.load(f)
                dados.append(evento)
                f.seek(0)
                json.dump(dados, f, ensure_ascii=False, indent=2)
                f.truncate()
        except Exception as e:
            pass


    def cache_obter(self, pergunta: str):
        chave = f"resposta:{hashlib.md5(pergunta.encode()).hexdigest()}"
        resposta = self.redis.get(chave)
        return resposta.decode("utf-8") if resposta else None


    def cache_salvar(self, pergunta: str, resposta: str, tempo_expiracao: int = 3600):
        chave = f"resposta:{hashlib.md5(pergunta.encode()).hexdigest()}"
        self.redis.setex(chave, tempo_expiracao, resposta)


    def recuperar_documentos(self, pergunta: str, top_k: int = 3):
        embedding = self.embedding_model.encode([pergunta])
        _, indices = self.indice.search(embedding, top_k)
        trechos_recuperados = []
        for i in indices[0]:
            texto = self.id_para_texto.get(str(i), "")
            if texto:
                trechos_recuperados.append(texto)
        return trechos_recuperados


    def deve_preservar(self, trecho):
        padroes_preservar = [
                            r"Centro de Referência LGBTI\+.*",
                            r"Zona (Oeste|Leste|Sul|Norte|Centro)",
                            r"(Rua|Avenida|Av\.|Travessa|Alameda|Praça|Estrada)\s+.*[0-9]+.*",
                            r"Segunda a sexta-feira.*",
                            r"\(?\d{2}\)?\s?\d{4,5}-?\d{4}",
                            r"E-?mail:?\s?[^\s]+@[^\s]+",
                            ]
        
        for padrao in padroes_preservar:
            if re.search(padrao, trecho, re.IGNORECASE):
                return True
        return False


    def extrair_dado_documento(self, pergunta, documentos):
        pergunta_lower = pergunta.lower()
        nome_centro_alvo = None

        # Busca por nome do centro
        for doc in documentos:
            if "laura vermont" in pergunta_lower and "laura vermont" in doc.lower():
                nome_centro_alvo = doc
                break
            elif "claudia wonder" in pergunta_lower and "claudia wonder" in doc.lower():
                nome_centro_alvo = doc
                break
            elif "luana barbosa" in pergunta_lower and "luana barbosa" in doc.lower():
                nome_centro_alvo = doc
                break
            elif "edson neris" in pergunta_lower and "edson neris" in doc.lower():
                nome_centro_alvo = doc
                break
            elif "brunna valin" in pergunta_lower and "brunna valin" in doc.lower():
                nome_centro_alvo = doc
                break

        if not nome_centro_alvo:
            return "Desculpe, não encontrei esse centro."

        # Extrair campos com base na intenção da pergunta
        if "telefone" in pergunta_lower:
            telefones = re.findall(r"\(?\d{2}\)? ?\d{4,5}-\d{4}", nome_centro_alvo)
            return f"Telefone: {', '.join(telefones)}" if telefones else "Telefone não encontrado."

        elif "e-mail" in pergunta_lower or "email" in pergunta_lower:
            email = re.search(r"[\w\.-]+@[\w\.-]+", nome_centro_alvo)
            return f"E-mail: {email.group()}" if email else "E-mail não encontrado."

        elif "endereço" in pergunta_lower or "endereco" in pergunta_lower:
            endereco_match = re.search(r"\n([^\n]*\d+[^\n]*)\n", nome_centro_alvo)
            return f"Endereço: {endereco_match.group(1)}" if endereco_match else "Endereço não encontrado."

        elif "horário" in pergunta_lower or "funcionamento" in pergunta_lower:
            horario_match = re.search(r"segunda.*\d+h.*\d+h", nome_centro_alvo.lower())
            return f"Horário: {horario_match.group().capitalize()}" if horario_match else "Horário não encontrado."

        else:
            return "Que informação você gostaria de saber: telefone, e-mail, endereço ou horário?"


    def salvar_avaliacao_em_json(self, pergunta: str, resposta: str, contexto: str, avaliacao: dict, caminho_json: str = "log_avaliacoes.json"):

        nova_avaliacao = {
            "pergunta": pergunta,
            "resposta": resposta,
            "contexto": contexto,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        try:
            with open(caminho_json, "r", encoding="utf-8") as f:
                avaliacoes_existentes = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            avaliacoes_existentes = []

        avaliacoes_existentes.append(nova_avaliacao)

        with open(caminho_json, "w", encoding="utf-8") as f:
            json.dump(avaliacoes_existentes, f, indent=2, ensure_ascii=False)


    @opik.track
    def gerar_resposta(self, pergunta: str, top_k: int = 3, max_tokens: int = 500):

        inicio_tempo = time.time()

        self.registrar_log({"evento": "pergunta_recebida", "pergunta": pergunta, "timestamp": inicio_tempo})

        pergunta_lower = pergunta.lower().strip()
        
        if any(p in pergunta_lower for p in ["o que você é", "quem é você", "o que você faz", "quem está falando", "qual é a sua função",  "qual o seu nome", "o que você faz", "qual é a sua função"]):
            resposta_identidade = (
                "Eu sou a Vivi, sua assistente virtual!\n"
                "Fui criada para oferecer apoio, acolhimento e informações úteis, especialmente para quem passou por situações difíceis. "
                "Estou aqui para ouvir, orientar com empatia e te ajudar a encontrar o que precisa. Você não está só. 🌟"
            )
            self.cache_salvar(pergunta, resposta_identidade)
            self.registrar_log({"evento": "resposta_identidade", "pergunta": pergunta, "resposta": resposta_identidade, "timestamp": time.time()})
            return resposta_identidade


        if any(p in pergunta_lower for p in ["qual a origem do seu nome", "qual o significado do seu nome", "qual é o significado do seu nome", "qual o motivo do seu nome", "seu nome é uma homenagem a alguém"]):
            resposta_identidade_significado_nome = (
               "Meu nome tem origem no Latim e significa 'cheio de vida', 'vivo' e 'vida'. Além de ser um nome brasileiro, ele é uma homenagem às pessoas que sobreviveram a situações de violência — um lembrete de que ainda há força, esperança e luz dentro de cada uma delas."
            )
            self.cache_salvar(pergunta, resposta_identidade_significado_nome)
            self.registrar_log({"evento": "resposta_significado_nome", "pergunta": pergunta, "resposta": resposta_identidade_significado_nome, "timestamp": time.time()})
            return resposta_identidade_significado_nome
        

        if any(p in pergunta_lower for p in ["qual é a fonte", "quais são as fontes", "de onde vem", "onde encontrou", "de onde tirou isso", "você pode citar as fontes", "origem da informação", "qual a origem da informação"]):
            resposta_fontes =(
            "As informações aqui apresentadas têm como base conteúdos produzidos por centros de referência LGBTI+ e pela ANTRA (Associação Nacional de Travestis e Transexuais), especialmente as cartilhas elaboradas por Bruna G. Benevides (@brunabenevidex), 2ª Sargenta da Marinha do Brasil, com foco em orientações à população LGBTI no combate à LGBTIfobia e sobre violência doméstica. "
            "O material contou com revisão técnica de Paulo Iotti (@pauloiotti), advogado, e Anderson Cavichioli (@renosplgbti), presidente da RENOSP-LGBTI e delegado de Polícia Civil; "
            "revisão ortográfica de Isaac Porto (@iporto), consultor LGBTI para o Instituto sobre Raça, Igualdade e Direitos Humanos; "
            "e projeto gráfico e diagramação de Raykka Rica (@distritodrag), integrante do coletivo Distrito Drag.")

            self.cache_salvar(pergunta, resposta_fontes)
            self.registrar_log({"evento": "qual_e_a_fonte", "pergunta": pergunta, "resposta": resposta_fontes, "timestamp": time.time()})
            
            return resposta_fontes

        resposta_cache = self.cache_obter(pergunta)

        if resposta_cache:
            self.registrar_log({"evento": "resposta_cache_encontrada", "pergunta": pergunta, "resposta_cache": resposta_cache, "timestamp": time.time()})
            return f"{resposta_cache}"
        
        documentos = self.recuperar_documentos(pergunta, top_k)

        if any(p in pergunta_lower for p in ["contato", "email", "e-mail", "telefone", "horário de funcionamento"]):
            resposta_centro_contato = self.extrair_dado_documento(pergunta, documentos)

            self.cache_salvar(pergunta, resposta_centro_contato)

            self.registrar_log({"evento": "resposta_significado_nome", "pergunta": pergunta, "resposta": resposta_centro_contato, "timestamp": time.time()})

            return resposta_centro_contato

        self.registrar_log({"evento": "documentos_recuperados", "pergunta": pergunta, "documentos": documentos, "timestamp": time.time()})

        documentos_filtrados = [doc for doc in documentos if len(doc.split()) > 10]

        if not documentos_filtrados:
            resposta = "Desculpe, não encontrei informações suficientes para responder sua pergunta. 😔"
            self.registrar_log({"evento": "documentos_insuficientes", "pergunta": pergunta, "resposta": resposta, "timestamp": time.time()})
            return resposta
        
        contexto = "\n".join(documentos_filtrados)

        tokens_contexto = self.tokenizer(contexto, return_tensors="pt", truncation=True, max_length=1024)["input_ids"][0]
        contexto_limitado = self.tokenizer.decode(tokens_contexto, skip_special_tokens=True)

        prompt = (
            "A seguir está uma pergunta respondida por Vivi, uma assistente virtual brasileira, empática, amigável e respeitosa.\n"
            "Ela responde com base no contexto fornecido, sem inventar informações e sem repetir trechos do contexto.\n"
            "Caso a informação não esteja presente, ela explica educadamente que não foi possível encontrar a resposta.\n\n"
            "A resposta deve ter no máximo 500 caracteres. Se for necessário ultrapassar esse limite, Vivi deve perguntar ao usuário se deseja mais detalhes antes de continuar.\n"
            f"Contexto:\n{contexto_limitado}\n\n"
            f"Pergunta:\n{pergunta}\n\n"
            "Resposta:"
        )

        entradas = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048).to(self.dispositivo)

        saida_ids = self.modelo.generate(
            **entradas,
            max_new_tokens=max_tokens,
            pad_token_id=self.tokenizer.eos_token_id,
            num_beams=3,
            early_stopping=True,
            do_sample=True,
            top_p=0.9,
            temperature=0.7,
            repetition_penalty=2.0
        )

        resposta_completa = self.tokenizer.decode(saida_ids[0], skip_special_tokens=True)

        resposta = resposta_completa.split("Resposta:")[-1].strip()

        for trecho in contexto_limitado.split("\n"):
            trecho_limpo = trecho.strip()
            if trecho_limpo and not self.deve_preservar(trecho_limpo):
                if trecho_limpo in resposta:
                    resposta = resposta.replace(trecho_limpo, "")

        resposta_final = resposta.split("Contexto:")[0].strip()

        self.cache_salvar(pergunta, resposta_final)

        referencia_de_resposta = "Centro de Referência LGBTI+ Laura Vermont"
        referencia_de_resposta_02 = "O Centro de Referência LGBTI+ Laura Vermont está localizado na Avenida Nordestina, 496 – São Miguel Paulista."
        
        metrica_e_igual_a.score(output=resposta_final, reference=referencia_de_resposta_02)
        metrica_contem.score(output=resposta_final, reference= referencia_de_resposta)
        metrica_regex.score(output=resposta_final)
        metrica_levenshtein.score(output=resposta_final, reference=referencia_de_resposta)

        self.registrar_log({"evento": "resposta_gerada", "pergunta": pergunta, "resposta": resposta_final, "tempo_execucao_segundos": time.time() - inicio_tempo, "timestamp": time.time()})

        caminho_json = "avaliacoes_ollama.json"

        self.salvar_avaliacao_em_json(pergunta, resposta_final, contexto_limitado, self.nome_modelo_ollama_avaliador, caminho_json)

        return resposta_final
