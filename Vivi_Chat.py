import time

import streamlit as st

from modelo_com_rag import RAGPipeline 

AZUL_TRANSPARENTE = '#5BCEFA'
ROSA_TRANSPARENTE = '#F5A9B8'
BRANCO = '#FFFFFF'
ROSA_ESCURO = "#D18F9C"
AZUL_ESCURO = "#00A8EA"

st.set_page_config(
page_title="Chatbot Vivi",
page_icon="https://upload.wikimedia.org/wikipedia/commons/b/b0/Transgender_Pride_flag.svg",
layout="wide"
)

def estilizacao_com_css():
    st.markdown(f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@300;700&display=swap');
            @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css');
                
            html, body {{
                padding: 0 !important;
                margin: 0 !important;
                overflow-x: hidden;
                overflow-y: hidden;
            }}
            .stApp header {{
                display: none;
            }}
            .stApp {{
                margin: 0;
                padding: 0;
            }}
            .main .block-container {{
                padding: 0 !important;
                margin: 0 !important;
                overflow: hidden;
            }}
            .stButton>button {{
                background: linear-gradient(180deg, {AZUL_TRANSPARENTE}, {ROSA_TRANSPARENTE}, {BRANCO}, {ROSA_TRANSPARENTE}, {AZUL_TRANSPARENTE});
                border: none;
                color: {AZUL_ESCURO};
                font-size: 16px;
                padding: 10px 24px;
                border-radius: 12px;
                cursor: pointer;
                transition: transform 0.2s, color 0.2s;
                font-weight: bold;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            .stButton>button:hover {{
                transform: scale(1.05);
                color: {ROSA_ESCURO};
            }}
        </style>
    """, unsafe_allow_html=True)


def tela_1():
    st.markdown(f"""
        <div style="background: {BRANCO}; padding: 60px 20px; display: flex; flex-direction: column;
            justify-content: center; align-items: center; text-align: center;
            font-family: 'Nunito', sans-serif; color: {ROSA_TRANSPARENTE};">
            <div style="max-width: 800px;">
                <h1 style="color: {AZUL_TRANSPARENTE}; font-size: 48px; margin-bottom: 20px;">Quem é a Vivi?</h1>
                <p style="font-size: 22px; line-height: 1.6;">
                    A Vivi é uma assistente virtual que apoia pessoas trans vítimas de violência,
                    oferecendo informações sobre LGBTfobia, transfobia e locais de acolhimento e ajuda.
                </p>
            </div>
        </div>
    """, unsafe_allow_html=True)


def tela_2():
    st.markdown(f"""
        <div style="background: {BRANCO}; padding: 60px 20px; display: flex; flex-direction: column;
            justify-content: center; align-items: center; text-align: center;
            font-family: 'Nunito', sans-serif; color: {ROSA_TRANSPARENTE};">
            <div style="max-width: 800px;">
                <h1 style="color: {AZUL_TRANSPARENTE}; font-size: 48px; margin-bottom: 20px;">Sobre o Projeto</h1>
                <p style="font-size: 22px; line-height: 1.6;">
                    A Vivi foi criada como parte de um projeto de Iniciação Científica com o objetivo de desenvolver 
                    um chatbot inclusivo, utilizando tecnologias de Recuperação de Informação e Aprendizado de Máquina.
                </p>
            </div>
        </div>
    """, unsafe_allow_html=True)


def tela_3():
    st.markdown(f"""
        <div style="background: {BRANCO}; padding: 60px 20px; display: flex; flex-direction: column;
            justify-content: center; align-items: center; text-align: center;
            font-family: 'Nunito', sans-serif; color: {ROSA_TRANSPARENTE};">
            <div style="max-width: 800px;">
                <h1 style="color: {AZUL_TRANSPARENTE}; font-size: 48px; margin-bottom: 20px;">Autoria</h1>
                <p style="font-size: 22px; line-height: 1.6;">
                    Este projeto foi desenvolvido por Alanis Urquisa Dias Moreira, estudante de Ciência de Dados, sob orientação do Prof. Dr. Ivan Carlos Alcântara de Oliveira. 
                    É uma iniciativa vinculada ao Laboratório de Ciberdemocracia da Universidade Presbiteriana Mackenzie.
                </p>
            </div>
        </div>
    """, unsafe_allow_html=True)


class InterfaceVivi:
    def __init__(self):
        if "rag" not in st.session_state:
            st.session_state.rag = RAGPipeline(
                nome_modelo="CEIA-UFG/Gemma-3-Gaia-PT-BR-4b-it",
                nome_modelo_ollama_avaliador = "llama2",
                caminho_faiss="faiss.index",
                caminho_id_texto="id_para_texto.json"
            )
        self.rag = st.session_state.rag
        self._configurar_pagina()
        self._inicializar_historico()


    def _configurar_pagina(self):
        st.title("Olá, eu sou a Vivi! 🏳️‍⚧️")


    def _inicializar_historico(self):
        if "messages" not in st.session_state:
            st.session_state.messages = []


    def mensagem_usuario(self, texto):
        st.markdown(
            f"""
            <div style='
                background-color: #F8E0F7;
                padding: 10px;
                border-radius: 15px;
                margin: 5px 0 5px auto;
                max-width: 75%;
                text-align: left;
                color: black;
                font-family: sans-serif;
                font-size: 16px;
                float: right;
                clear: both;
            '>
                {texto}
            </div>
            """,
            unsafe_allow_html=True,
        )

    def mensagem_bot(self, texto):
        st.markdown(
            f"""
            <div style='
                background-color: #A9E2F3;
                padding: 10px;
                border-radius: 15px;
                margin: 5px auto 5px 0;
                max-width: 75%;
                text-align: left;
                color: black;
                font-family: sans-serif;
                font-size: 16px;
                float: left;
                clear: both;
            '>
                {texto}
            </div>
            """,
            unsafe_allow_html=True,
        )

    def executar(self):
        for message in st.session_state.messages:
            if message["role"] == "user":
                self.mensagem_usuario(message["content"])
            else:
                self.mensagem_bot(message["content"])

        user_input = st.chat_input("Digite sua mensagem...")

        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            self.mensagem_usuario(user_input)

            with st.spinner("Pensando..."):
                time.sleep(0.5) # Pequeno atraso para simular processamento
                try:
                    resposta = self.rag.gerar_resposta(user_input)
                except Exception as e:
                    resposta = f"Desculpe, ocorreu um erro ao gerar a resposta: {e}"
                    st.error(resposta)

            st.session_state.messages.append({"role": "bot", "content": resposta})
            self.mensagem_bot(resposta)


def main():
    if "tela" not in st.session_state:
        st.session_state.tela = 1

    estilizacao_com_css()

    if st.session_state.tela == 1:
        tela_1()
        col1, col2, col3 = st.columns([1, 1, 1])
        with col3:
            if st.button("Próximo", key="btn1"):
                st.session_state.tela = 2
                st.rerun()

    elif st.session_state.tela == 2:
        tela_2()
        col1, col2, col3 = st.columns([1, 1, 1])
        with col3:
            if st.button("Próximo", key="btn2"):
                st.session_state.tela = 3
                st.rerun()

    elif st.session_state.tela == 3:
        tela_3()
        col1, col2, col3 = st.columns([1, 1, 1])
        with col3:
            if st.button("Ir para o Chatbot", key="btn3"):
                st.session_state.tela = 4
                st.rerun()

    elif st.session_state.tela == 4:
        interface = InterfaceVivi()
        interface.executar()


if __name__ == "__main__":
    main()