from .base import NotebookExecutor
import fitz
import re
import json
from datetime import datetime
import os

class MedwayExecutor(NotebookExecutor):
    
    def __init__(self, file_path=None, on_complete=None):
        self.file_path = file_path
        self.on_complete = on_complete

    def execute(self):
        print("Executando notebook Medway")
        pagina_gabarito = self.encontrar_pagina_gabarito(caminho_pdf=self.file_path, palavra_buscada="GABARITO")
        content_pdf = self.extrair_texto_pdf(caminho_pdf=self.file_path, end=pagina_gabarito)

        # Expressão regular para encontrar e remover linhas que começam com "Medway" ou "Páginas"
        pattern = r"^(Medway|Páginas).*\n?"

        # Substituindo as linhas encontradas por uma string vazia
        content_pdf = re.sub(pattern, "", content_pdf, flags=re.MULTILINE)
        content_pdf = re.sub(r"^USP.*\n?", "", content_pdf, flags=re.MULTILINE)
        content_pdf = re.sub(r'\n\s*\n', '\n', content_pdf)

        itens = re.split(r'(?=QUESTÃO \d+\.)', content_pdf)
        itens = [item for item in itens if item]

        # Imprimir cada correspondência encontrada
        questoes_finais = []
        for item in itens:
            questoes_finais.append(self.processar_questao(item))

        parte_final = self.extrair_texto_pdf(self.file_path, begin=pagina_gabarito + 1)

        # Expressão regular para encontrar e remover linhas que começam com "Medway" ou "Páginas"
        pattern = r"^(Medway|Páginas|RESPOSTAS|ANULADA).*\n?"

        # Substituindo as linhas encontradas por uma string vazia
        parte_final = re.sub(pattern, "", parte_final, flags=re.MULTILINE)
        parte_final = re.sub(r'(120\.\n[A-D]).*', r'\1', parte_final, flags=re.DOTALL)

        # Dividir o texto em linhas
        linhas = parte_final.strip().split('\n')

        # Lista para armazenar os dicionários de questão e resposta
        gabarito = []

        # Variável temporária para armazenar o número da questão atual
        questao_atual = None

        for linha in linhas:
            # Verifica se a linha representa uma questão (número seguido de ponto)
            if linha.endswith('.'):
                # Se sim, extrai o número da questão
                questao_atual = int(linha[:-1])
                # Adiciona um dicionário para esta questão com uma resposta padrão 'A'
                gabarito.append({"questao": questao_atual, "resposta": "X"})
            else:
                # Se não, a linha deve representar uma resposta, então atualiza a última questão adicionada
                gabarito[-1]["resposta"] = linha
        
        # Atualizar a resposta correta nas questões com base no gabarito
        for questao in questoes_finais:
            for gab in gabarito:
                # Converte a resposta_correta para inteiro para comparação, assumindo que todos os IDs possam ser convertidos corretamente
                if int(questao['id']) == gab['questao']:
                    # Atualiza a resposta correta com o valor do gabarito
                    questao['resposta_correta'] = gab['resposta']
                    if(gab['resposta'] == 'X'):
                        questao['desc'] = "(ANULADA) - " + questao['desc']
                        questao['resposta_correta'] = 'A'
        

        # Gera a string de data e hora no formato desejado
        data_hora_atual = datetime.now().strftime('%Y%m%d-%H%M%S')
        nome_arquivo = f'questoes_medway_{data_hora_atual}.json'

        # Define o caminho completo onde o arquivo será salvo
        caminho_completo = os.path.join('.', 'medreview', 'medway', nome_arquivo)

        # Garanta que a pasta existe
        os.makedirs(os.path.dirname(caminho_completo), exist_ok=True)

        # Faz o dump do conteúdo no arquivo com o caminho e nome formatados
        with open(caminho_completo, 'w', encoding='utf-8') as f:
            json.dump(questoes_finais, f, ensure_ascii=False, indent=4)

        self.on_complete(f"Arquivo disponível em {caminho_completo}")

    def encontrar_pagina_gabarito(self, caminho_pdf, palavra_buscada):
        # Abrir o documento PDF
        doc = fitz.open(caminho_pdf)

        # Iterar por todas as páginas do documento
        for num_pagina in range(2,len(doc)):
            # Obter o texto da página atual
            texto_pagina = doc.load_page(num_pagina).get_text()

            # Verificar se a palavra buscada está presente no texto da página
            if palavra_buscada in texto_pagina:
                # Se encontrada, retornar o número da página (indexação começa em 0, então adiciona 1 para número real da página)
                return num_pagina + 1

        # Fechar o documento
        doc.close()

        # Retornar None se a palavra não foi encontrada em nenhuma página
        return None

    def extrair_texto_pdf(self, caminho_pdf, begin = 2, end = None):
        # Abrir o documento PDF
        doc = fitz.open(caminho_pdf)
        final = end - 1 if end is not None else len(doc)
        texto_completo = ""
        # Iterar por cada página do documento, começando da página 3 (índice 2)
        for num_pagina in range(begin, final):
            pagina = doc.load_page(num_pagina)  # Carregar a página pelo número do índice
            # Extrair o texto da página atual
            texto_pagina = pagina.get_text()
            texto_completo += texto_pagina + "\n"  # Adiciona o texto da página ao texto completo

        # Fechar o documento
        doc.close()

        return texto_completo
    
    def processar_questao(self, texto_questao):
        # Encontrar o número da questão
        numero_questao_match = re.search(r"QUESTÃO (\d+)", texto_questao)
        numero_questao = numero_questao_match.group(1) if numero_questao_match else "Desconhecido"

        # Dividir o texto pelas alternativas
        partes = re.split(r"\n(A\.|B\.|C\.|D\.)", texto_questao)

        # A primeira parte é a descrição
        descricao = partes[0].strip().replace("\n","")

        # Removendo o padrão usando regex
        descricao = re.sub(r"QUESTÃO \d+\.", "", descricao).strip()

        # Estrutura para armazenar os dados processados
        dados_questao = {
            "id" : numero_questao,
            "desc": descricao,
            "alternativas": {},
            "resposta_correta": ''
        }

        # Processar as alternativas
        for i in range(1, len(partes), 2):
            letra = partes[i].strip()
            conteudo = partes[i + 1].strip() if i + 1 < len(partes) else ""
            dados_questao["alternativas"][letra.replace(".", "")] = conteudo

        return dados_questao