import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from executores import EstrategiaExecutor, AnestExecutor, MedwayExecutor

# Funções dos executores são definidas acima

# Função chamada quando o botão de processamento é clicado
def processar():
    opcao_selecionada = combobox_value.get()
    file_path = file_path_label.cget("text")  # Caminho do arquivo selecionado

    # Dicionário para mapear opções para suas respectivas classes executoras
    executors_map = {
        'Estratégia': EstrategiaExecutor,
        'Anest - ME3': AnestExecutor,
        'Medway': MedwayExecutor,
    }

    # Seleciona o executor com base na opção e instancia com o caminho do arquivo
    executor_class = executors_map.get(opcao_selecionada)
    if executor_class:
        executor = executor_class(file_path, processamento_concluido)
        executor.execute()
    else:
        print("Opção de executor não reconhecida.")

# Função para abrir o seletor de arquivos e atualizar o label com o caminho do arquivo selecionado
def selecionar_arquivo():
    filename = filedialog.askopenfilename()
    file_path_label.config(text=filename)
    return filename

def processamento_concluido(mensagem):
    messagebox.showinfo("Processamento Concluído", mensagem)


# Cria a janela principal
root = tk.Tk()
root.title("Seletor de Arquivos e Processamento")

# Configura a janela
root.geometry('400x150')
root.resizable(False, False)

# Cria um botão para selecionar o arquivo
select_file_button = tk.Button(root, text="Selecionar Prova", command=selecionar_arquivo)
select_file_button.pack(pady=10)

# Label para mostrar o caminho do arquivo selecionado
file_path_label = tk.Label(root, text="Nenhum arquivo selecionado")
file_path_label.pack()

# Criação do combobox com as opções
combobox_value = tk.StringVar()
combobox = ttk.Combobox(root, textvariable=combobox_value, state="readonly")
combobox['values'] = ('Estratégia', 'Anest - ME3', 'Medway')
combobox.pack(pady=5)
combobox.set('Estratégia')  # Define o valor padrão

# Cria um botão para iniciar o processamento
process_button = tk.Button(root, text="Processar", command=processar)
process_button.pack(pady=10)

# Executa a janela principal
root.mainloop()