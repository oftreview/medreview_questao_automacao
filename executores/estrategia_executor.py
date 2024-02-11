from .base import NotebookExecutor
import fitz
import re
import json
from datetime import datetime
import os


class EstrategiaExecutor(NotebookExecutor):
    
    def __init__(self, file_path=None, on_complete=None):
        self.file_path = file_path
        self.on_complete = on_complete

    def execute(self):
        print("Executando notebook Usp")
        content_pdf = self.extrair_texto_pdf(caminho_pdf=self.file_path, begin=0)

        # Usar expressão regular para encontrar "Questão 1" e tudo o que segue
        regex_pattern = r'Questão 1[\s\S]*'
        texto_modificado = re.search(regex_pattern, content_pdf).group()

        result = texto_modificado.split("Respostas")

        conteudo = result[0]
        respostas = result[1]
        respostas = respostas.replace(':','')

        # Expressão regular para encontrar e remover linhas que começam com "Medway" ou "Páginas"
        pattern = r"^(Essa questão possui).*\n?"

        # Substituindo as linhas encontradas por uma string vazia
        conteudo = re.sub(pattern, "", conteudo, flags=re.MULTILINE)

        # Usar expressão regular para remover o número que começa com 4000
        conteudo = re.sub(r'\b4000\d*\b', '', conteudo)

        itens = re.split(r'(?=Questão)', conteudo)
        #removendo itens vazios
        itens = list(filter(None, itens))

        # Imprimir cada correspondência encontrada
        questoes_finais = []
        for item in itens:
            questoes_finais.append(self.formata_questao(item))
        
        # Dividir o conteúdo por linhas e filtrar linhas vazias
        respostas = [linha for linha in respostas.split('\n') if linha]

        # Processar as linhas para criar a estrutura desejada
        gabarito = []
        for i in range(0, len(respostas), 2):
            gabarito.append({
                "questao": int(respostas[i]),
                "resposta": respostas[i+1]
            })

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
        nome_arquivo = f'questoes_estrategia_{data_hora_atual}.json'

        # Define o caminho completo onde o arquivo será salvo
        caminho_completo = os.path.join('.', 'medreview', 'estrategia', nome_arquivo)

        # Garanta que a pasta existe
        os.makedirs(os.path.dirname(caminho_completo), exist_ok=True)

        # Faz o dump do conteúdo no arquivo com o caminho e nome formatados
        with open(caminho_completo, 'w', encoding='utf-8') as f:
            json.dump(questoes_finais, f, ensure_ascii=False, indent=4)

        self.on_complete(f"Arquivo disponível em {caminho_completo}")

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
    
    def formata_questao(self, conteudo_questao):
        # Extrair o ID da questão
        id_questao = int(re.search(r'Questão (\d+)', conteudo_questao).group(1))

        # Extrair a descrição e as alternativas
        partes = re.split(r'\n([ABCD])\n', conteudo_questao.strip())
        descricao = partes[0].split('\n', 1)[1]  # Remove a linha "Questão 6"

        # Organizar as alternativas em um dicionário
        alternativas = {partes[i]: partes[i + 1].strip().replace('\n',' ') for i in range(1, len(partes), 2)}

        # Montar o dicionário da questão
        questao_dict = {
            "id": id_questao,
            "desc": descricao.replace('\n',' '),
            "alternativas": alternativas,
            "resposta_correta": ""  # Sem informação sobre a resposta correta
        }

        return questao_dict