import fitz  # pymupdf
import os

def converter_pdfs_para_txt(pasta):
    for arquivo in os.listdir(pasta):
        if arquivo.endswith(".pdf"):
            caminho_pdf = os.path.join(pasta, arquivo)
            nome_base = os.path.splitext(arquivo)[0]
            caminho_txt = os.path.join(pasta, nome_base + ".txt")

            with fitz.open(caminho_pdf) as doc:
                texto_total = ""
                for pagina in doc:
                    texto_total += pagina.get_text()

            with open(caminho_txt, "w", encoding="utf-8") as f:
                f.write(texto_total)

            print(f"Salvo: {caminho_txt}")


if __name__ == "__main__":
    pasta = "fonte_de_dados"
    converter_pdfs_para_txt(pasta)
