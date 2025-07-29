from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
import json
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class ScrapingCentrosLGBTI:
    def __init__(self):
        self.url = "https://capital.sp.gov.br/web/lgbti/w/rede_de_atendimento/271098"
        self.driver = self.iniciar_navegador()

    def iniciar_navegador(self):
        """Inicializa o navegador"""
        servico = Service(GeckoDriverManager().install())
        opcoes = webdriver.FirefoxOptions()
        return webdriver.Firefox(service=servico, options=opcoes)

    def extrair_dados(self):
        """Extrai títulos, textos e links da seção específica da página."""
        self.driver.get(self.url)

        try:
            # Espera até que o primeiro elemento da página seja carregado
            secao_1 = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]/div[1]/div[2]'))
            )

            # Rolagem até o elemento final
            self.driver.execute_script("arguments[0].scrollIntoView();", secao_1)

            # Extração dos dados
            dados = {"titulos": [], "textos": []}

            # Captura os títulos dentro de h2
            titulos = secao_1.find_elements(By.TAG_NAME, "h2")
            dados["titulos"] = [titulo.text.strip() for titulo in titulos if titulo.text.strip()]

            # Captura os parágrafos e textos dentro de divs
            paragrafos = secao_1.find_elements(By.TAG_NAME, "p")
            dados["textos"] = [p.text.strip() for p in paragrafos if p.text.strip()]

            return dados

        except Exception as e:
            print(f"Erro ao localizar a seção: {e}")
            return None

    def salvar_como_txt(self, dados, caminho="rede_atendimento.txt"):
        """Salva os dados extraídos em um arquivo TXT."""
        with open(caminho, "w", encoding="utf-8") as arquivo:
            arquivo.write("\n".join(dados["titulos"]) + "\n\n")
            arquivo.write("\n".join(dados["textos"]) + "\n\n")

    def salvar_como_json(self, dados, caminho="rede_atendimento.txt"):
        """Salva os dados extraídos em um arquivo JSON."""
        with open(caminho, "w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=4)

    def executar(self):
        """Executa todo o processo de raspagem e salvamento."""
        try:
            dados = self.extrair_dados()
            if dados:
                self.salvar_como_txt(dados)
                print("Arquivos salvos com sucesso!")
            else:
                print("Falha ao extrair os dados.")
        finally:
            self.driver.quit()

if __name__ == "__main__":
    raspador = ScrapingCentrosLGBTI()
    raspador.executar()