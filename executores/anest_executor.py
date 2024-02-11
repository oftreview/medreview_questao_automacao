from .base import NotebookExecutor
import PyPDF2
import re
import json
from datetime import datetime
import os
import fitz

class AnestExecutor(NotebookExecutor):

    def __init__(self, file_path=None, on_complete=None):
        self.file_path = file_path
        self.on_complete = on_complete

    def execute(self):
        print("Executando notebook Anest")
        content_pdf = self.ler_conteudo_pdf(self.file_path)

        content_pdf = re.sub(r'(\d+ -)', r'\n\1', content_pdf)
        # Removendo linhas que contêm "PROVA NACIONAL" e "Sociedade Brasileira de Anestesiologia"
        content_pdf = re.sub(r"(Resposta:\s+[ABCD])", r"\1\n", content_pdf)
        content_pdf = re.sub(r'.*PROVA NACIONAL.*\n?', '', content_pdf)
        content_pdf = re.sub(r'.*Sociedade Brasileira de Anestesiologia.*\n?', '', content_pdf)
        content_pdf = re.sub(r'^\s*\n', '', content_pdf, flags=re.MULTILINE)


        # Regex para capturar o conteúdo desejado
        regex = r"(\d+ - .+?Resposta:\s+[ABCD])"

        # Encontrar todas as correspondências
        resultados = re.findall(regex, content_pdf, re.DOTALL)

        # Imprimir cada correspondência encontrada
        questoes = []
        for resultado in resultados:
            questoes.append(self.formatar_questao(resultado))

        # Gera a string de data e hora no formato desejado
        data_hora_atual = datetime.now().strftime('%Y%m%d-%H%M%S')
        nome_arquivo = f'questoes_anest_{data_hora_atual}.json'

        # Define o caminho completo onde o arquivo será salvo
        caminho_completo = os.path.join('.', 'medreview', 'anest', nome_arquivo)

        # Garanta que a pasta existe
        os.makedirs(os.path.dirname(caminho_completo), exist_ok=True)

        # Faz o dump do conteúdo no arquivo com o caminho e nome formatados
        with open(caminho_completo, 'w', encoding='utf-8') as f:
            json.dump(questoes, f, ensure_ascii=False, indent=4)
        
        self.on_complete(f"Arquivo disponível em {caminho_completo}")

    def ler_conteudo_pdf(self, caminho_arquivo, ignored_initial_pages = 2):
        # Lendo o conteúdo do PDF
        texto = ""

        with open(caminho_arquivo, 'rb') as arquivo:
            leitor_pdf = PyPDF2.PdfReader(arquivo)

            # Iterando sobre cada página do PDF e extraindo o texto
            for pagina in range(ignored_initial_pages, len(leitor_pdf.pages)):
                texto += leitor_pdf.pages[pagina].extract_text()

        return texto
    
    def formatar_questao(self, texto):
        # Ajuste para capturar a questão considerando o início até a primeira alternativa
        # Encontrar a questão
        questao_match = re.search(r"(\d+ - )(.*?)(?=\sA\))", texto, re.DOTALL)
        questao = questao_match.group(2).strip() if questao_match else ""

        # Ajuste nas alternativas para evitar captura além do necessário
        alternativas_match = re.findall(r"\b([A-D])\) (.*?)(?=\n[A-D]\)|\nResposta:|$)", texto, re.DOTALL)
        alternativas = {letra: texto.strip() for letra, texto in alternativas_match}

        # Encontrar a resposta correta
        resposta_match = re.search(r"Resposta:\s+([A-D])", texto)
        resposta_correta = resposta_match.group(1).strip() if resposta_match else ""

        # Estruturando em um dicionário
        questao_formatada = {
            "desc": questao,
            "alternativas": alternativas,
            "resposta_correta": resposta_correta
        }

        return questao_formatada