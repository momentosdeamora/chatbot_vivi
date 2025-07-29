import json
import os

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

class ArmazenadorVetorialFaiss:
    def __init__(self, nome_modelo_embedding='all-MiniLM-L6-v2', caminho_indice='faiss.index', caminho_dados='id_para_texto.json', caminho_id_para_assunto='id_para_assunto.json'):
        self.modelo = SentenceTransformer(nome_modelo_embedding)
        self.textos = []
        self.embeddings = None
        self.indice = None
        self.id_para_texto = {}
        self.id_para_assunto = {}
        self.caminho_indice = caminho_indice
        self.caminho_dados = caminho_dados
        self.caminho_id_para_assunto = caminho_id_para_assunto

        self.arquivos_json = [
            r'dados_limpos_e_pre_processados\centros_LGBTI_limpo_e_pre_processado.json',
            r'dados_limpos_e_pre_processados\como_agir_em_casos_de_violencia_domestica_durante_o_isolamento_social_etapa_2_limpo_e_pre_processado.json',
            r'dados_limpos_e_pre_processados\o_que_fazer_em_caso_de_violencia_lgbtfobica_etapa_2_limpo_e_pre_processado.json'
        ]


    @staticmethod
    def extrair_todos_textos(obj):
        textos = []
        if isinstance(obj, dict):
            for chave, valor in obj.items():
                textos.extend(ArmazenadorVetorialFaiss.extrair_todos_textos(valor))
        elif isinstance(obj, list):
            for item in obj:
                textos.extend(ArmazenadorVetorialFaiss.extrair_todos_textos(item))
        elif isinstance(obj, str):
            textos.append(obj.strip())
        return textos


    def carregar_textos_de_todas_chaves(self):
        textos_para_indice = []
        id_para_texto_temp = {}
        id_para_assunto_temp = {}

        contador = 0
        for arquivo in self.arquivos_json:
            try:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    dados = json.load(f)

                    # Itera sobre as chaves de nível superior no JSON
                    for chave_primaria, valor_primario in dados.items():
                        # Se o valor for um dicionário (como "paragrafos")
                        if isinstance(valor_primario, dict):
                            for sub_chave, sub_valor in valor_primario.items():
                                # Extrai todos os textos de forma recursiva
                                textos_extraidos = self.extrair_todos_textos(sub_valor)
                                if textos_extraidos:
                                    texto_unico = '\n'.join(t for t in textos_extraidos if t)
                                    if texto_unico:
                                        id_str = str(contador)
                                        textos_para_indice.append(texto_unico)
                                        id_para_texto_temp[id_str] = texto_unico
                                        # Armazena a chave primária e a sub-chave para contexto
                                        id_para_assunto_temp[id_str] = {f"{chave_primaria}.{sub_chave}": textos_extraidos}
                                        contador += 1
                        # Se o valor for uma lista (como "centros")
                        elif isinstance(valor_primario, list):
                            for item in valor_primario:
                                # Extrai todos os textos de forma recursiva de cada item da lista (que pode ser um dicionário)
                                textos_extraidos = self.extrair_todos_textos(item)
                                if textos_extraidos:
                                    texto_unico = '\n'.join(t for t in textos_extraidos if t)
                                    if texto_unico:
                                        id_str = str(contador)
                                        textos_para_indice.append(texto_unico)
                                        id_para_texto_temp[id_str] = texto_unico
                                        # Armazena a chave primária e os textos extraídos
                                        id_para_assunto_temp[id_str] = {chave_primaria: textos_extraidos}
                                        contador += 1
                        # Se o valor for uma string ou outro tipo simples (caso não seja um dicionário aninhado ou lista)
                        elif isinstance(valor_primario, str):
                            if valor_primario.strip():
                                id_str = str(contador)
                                textos_para_indice.append(valor_primario.strip())
                                id_para_texto_temp[id_str] = valor_primario.strip()
                                id_para_assunto_temp[id_str] = {chave_primaria: [valor_primario.strip()]}
                                contador += 1

            except Exception as e:
                print(f"Erro ao abrir o arquivo {arquivo}: {e}")

        self.textos = textos_para_indice
        self.id_para_texto = id_para_texto_temp
        self.id_para_assunto = id_para_assunto_temp
        print(f"Total de segmentos carregados: {len(self.textos)}")
        return self.textos, self.id_para_texto, self.id_para_assunto


    def criar_indice(self):
        if not self.textos:
            raise ValueError("Nenhum texto carregado para indexar.")

        print("Criando embeddings...")
        embeddings = self.modelo.encode(self.textos, show_progress_bar=True)
        embeddings = np.array(embeddings).astype('float32')

        dim = embeddings.shape[1]
        self.indice = faiss.IndexFlatL2(dim)
        self.indice.add(embeddings)

        self.embeddings = embeddings


    def salvar_indice(self):
        if self.indice is None:
            raise ValueError("Índice não criado, nada para salvar.")
        faiss.write_index(self.indice, self.caminho_indice)
        with open(self.caminho_dados, 'w', encoding='utf-8') as f:
            json.dump(self.id_para_texto, f, ensure_ascii=False, indent=2)
        with open(self.caminho_id_para_assunto, 'w', encoding='utf-8') as f:
            json.dump(self.id_para_assunto, f, ensure_ascii=False, indent=2)
        print(f"Índice salvo em '{self.caminho_indice}', dados em '{self.caminho_dados}' e mapeamento de assunto em '{self.caminho_id_para_assunto}'.")


    def carregar_indice(self):
        if not os.path.exists(self.caminho_indice) or not os.path.exists(self.caminho_dados) or not os.path.exists(self.caminho_id_para_assunto):
            raise FileNotFoundError("Arquivos de índice, dados ou mapeamento de assunto não encontrados.")
        self.indice = faiss.read_index(self.caminho_indice)
        with open(self.caminho_dados, 'r', encoding='utf-8') as f:
            self.id_para_texto = json.load(f)
        with open(self.caminho_id_para_assunto, 'r', encoding='utf-8') as f:
            self.id_para_assunto = json.load(f)
        print(f"Índice, dados e mapeamento de assunto carregados. Total de textos: {len(self.id_para_texto)}")


    def atualizar_indice(self, novos_textos_com_meta):
        if self.indice is None:
            raise ValueError("Índice não carregado. Crie ou carregue um índice antes de atualizar.")

        textos_para_embedding = []
        meta_data_novos = []

        for item_data in novos_textos_com_meta:
            for chave, lista_textos in item_data.items():
                texto_concatenado = '\n'.join(t.strip() for t in lista_textos if isinstance(t, str) and t.strip())
                if texto_concatenado:
                    textos_para_embedding.append(texto_concatenado)
                    meta_data_novos.append(item_data)

        if not textos_para_embedding:
            print("Nenhum texto válido para atualização encontrado.")
            return

        novos_embeddings = self.modelo.encode(textos_para_embedding, show_progress_bar=True)
        novos_embeddings = np.array(novos_embeddings).astype('float32')

        self.indice.add(novos_embeddings)

        max_id = max(map(int, self.id_para_texto.keys())) if self.id_para_texto else -1
        for i, texto_concatenado in enumerate(textos_para_embedding, start=max_id + 1):
            id_str = str(i)
            self.id_para_texto[id_str] = texto_concatenado
            self.id_para_assunto[id_str] = meta_data_novos[i - (max_id + 1)]

        print(f"Índice atualizado com {len(textos_para_embedding)} novos textos.")


    def buscar(self, consulta, top_k=5):
        if self.indice is None:
            raise ValueError("Índice FAISS não carregado/criado.")

        vetor_consulta = self.modelo.encode([consulta]).astype('float32')
        distancias, indices = self.indice.search(vetor_consulta, top_k)

        resultados = []
        for dist, idx in zip(distancias[0], indices[0]):
            id_str = str(idx)
            assunto_info = self.id_para_assunto.get(id_str, {})
            if assunto_info:
                chave_original = list(assunto_info.keys())[0]
                lista_textos_original = assunto_info[chave_original]
                resultados.append({
                    'id': id_str,
                    'chave_original': chave_original,
                    'textos_originais': lista_textos_original,
                    'distancia': float(dist)
                })
            else:
                texto_concatenado = self.id_para_texto.get(id_str, "")
                resultados.append({'id': id_str, 'texto_concatenado': texto_concatenado, 'distancia': float(dist)})

        return resultados


    def interface_consulta_iterativa(self):
        print("\nInterface de busca iterativa iniciada. Digite 'sair' para encerrar.")
        while True:
            consulta = input("\nDigite a consulta: ").strip()
            if consulta.lower() == 'sair':
                print("Encerrando interface de busca.")
                break
            try:
                resultados = self.buscar(consulta, top_k=5)
                if resultados:
                    print("\nResultados encontrados:")
                    for i, res in enumerate(resultados, start=1):
                        if 'chave_original' in res and 'textos_originais' in res:
                            # Monta o dicionário no formato { "id": { "chave": [lista de textos] } }
                            output_dict = {res['id']: {res['chave_original']: res['textos_originais']}}
                            print(f"{i}. Distância: {res['distancia']:.4f}")
                            print(json.dumps(output_dict, ensure_ascii=False, indent=2))
                        else:
                            print(f"{i}. Distância: {res['distancia']:.4f} - Texto concatenado: {res['texto_concatenado'][:300].replace('\n', ' ')}{'...' if len(res['texto_concatenado']) > 300 else ''}")
                else:
                    print("Nenhum resultado encontrado.")
            except Exception as e:
                print(f"Erro na busca: {e}")


if __name__ == '__main__':
    armazenador = ArmazenadorVetorialFaiss(caminho_id_para_assunto='id_para_assunto.json')

    try:
        armazenador.carregar_indice()
    except Exception as e:
        print(f"Não foi possível carregar índice salvo: {e}")
        print("Carregando textos dos arquivos JSON e criando índice...")
        armazenador.carregar_textos_de_todas_chaves()
        armazenador.criar_indice()
        armazenador.salvar_indice()

    armazenador.interface_consulta_iterativa()
