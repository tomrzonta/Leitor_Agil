import tkinter as tk
from tkinter import filedialog # Para abrir a caixa de diálogo de seleção de arquivo
import time
from docx import Document # Importa a classe Document da biblioteca python-docx

# --- Funções de Leitura de Arquivos (já existentes, mas chamadas de dentro da interface) ---
def ler_texto_de_docx(caminho_do_arquivo):
    """Lê o texto de um arquivo .docx."""
    try:
        doc = Document(caminho_do_arquivo)
        full_text = []
        for paragraph in doc.paragraphs:
            full_text.append(paragraph.text)
        return '\n'.join(full_text)
    except Exception as e:
        # Mostra o erro na interface ou em um messagebox, em vez de apenas printar
        print(f"Erro ao ler DOCX: {e}")
        return None

def ler_texto_de_txt(caminho_do_arquivo):
    """Lê o texto de um arquivo .txt."""
    try:
        with open(caminho_do_arquivo, 'r', encoding='utf-8') as arquivo:
            return arquivo.read()
    except Exception as e:
        print(f"Erro ao ler TXT: {e}")
        return None

# --- Lógica do Programa de Leitura Rápida ---
class LeitorRapidoApp:
    def __init__(self, master):
        self.master = master
        master.title("Leitor Rápido de Texto") # Título da janela
        master.geometry("800x400") # Tamanho inicial da janela

        self.texto_completo = ""
        self.palavras = []
        self.indice_palavra_atual = 0
        self.esta_lendo = False
        self.job_id = None # Para controlar o loop de atualização do Tkinter

        # --- Componentes da Interface ---

        # Label para exibir a palavra atual
        self.palavra_label = tk.Label(master, text="Clique em 'Carregar Arquivo' para começar", font=("Arial", 36))
        self.palavra_label.pack(pady=50) # Espaçamento vertical

        # Frame para os botões (para organizá-los horizontalmente)
        self.frame_botoes = tk.Frame(master)
        self.frame_botoes.pack(pady=20)

        self.btn_carregar = tk.Button(self.frame_botoes, text="Carregar Arquivo", command=self.carregar_arquivo)
        self.btn_carregar.pack(side=tk.LEFT, padx=10)

        self.btn_iniciar_pausar = tk.Button(self.frame_botoes, text="Iniciar", command=self.iniciar_pausar_leitura)
        self.btn_iniciar_pausar.pack(side=tk.LEFT, padx=10)

        self.btn_resetar = tk.Button(self.frame_botoes, text="Resetar", command=self.resetar_leitura)
        self.btn_resetar.pack(side=tk.LEFT, padx=10)

        # Controle de Velocidade (PPM)
        self.velocidade_label = tk.Label(master, text="Velocidade (PPM): 300")
        self.velocidade_label.pack()

        self.velocidade_scale = tk.Scale(master, from_=100, to=1000, orient=tk.HORIZONTAL,
                                        length=300, command=self.atualizar_velocidade_label)
        self.velocidade_scale.set(300) # Valor inicial
        self.velocidade_scale.pack()

    def atualizar_velocidade_label(self, val):
        self.velocidade_label.config(text=f"Velocidade (PPM): {int(float(val))}")

    def carregar_arquivo(self):
        # Abre uma caixa de diálogo para o usuário escolher o arquivo
        caminho_arquivo = filedialog.askopenfilename(
            filetypes=[("Arquivos de Texto", "*.txt"), ("Documentos Word", "*.docx"), ("Todos os Arquivos", "*.*")]
        )
        if caminho_arquivo: # Se o usuário selecionou um arquivo
            if caminho_arquivo.endswith('.docx'):
                self.texto_completo = ler_texto_de_docx(caminho_arquivo)
            elif caminho_arquivo.endswith('.txt'):
                self.texto_completo = ler_texto_de_txt(caminho_arquivo)
            else:
                self.palavra_label.config(text="Formato não suportado!")
                return

            if self.texto_completo:
                # Limpeza e divisão do texto (pode ser melhorada para pontuação)
                self.palavras = self.texto_completo.replace('\n', ' ').replace('.', '').replace(',', '').split(' ')
                self.palavras = [p.strip() for p in self.palavras if p.strip()] # Remove palavras vazias

                self.indice_palavra_atual = 0
                self.atualizar_exibicao_palavra()
                self.btn_iniciar_pausar.config(text="Iniciar")
                self.esta_lendo = False
            else:
                self.palavra_label.config(text="Erro ao carregar o arquivo ou arquivo vazio.")

    def atualizar_exibicao_palavra(self):
        if self.indice_palavra_atual < len(self.palavras):
            self.palavra_label.config(text=self.palavras[self.indice_palavra_atual])
            self.indice_palavra_atual += 1
            # Calcula o tempo baseado na velocidade (PPM) do controle deslizante
            ppm = self.velocidade_scale.get()
            tempo_por_palavra_ms = (60 / ppm) * 1000 # Converte segundos para milissegundos
            # Chama esta função novamente após o tempo calculado
            if self.esta_lendo:
                self.job_id = self.master.after(int(tempo_por_palavra_ms), self.atualizar_exibicao_palavra)
        else:
            self.palavra_label.config(text="Fim da leitura!")
            self.esta_lendo = False
            self.btn_iniciar_pausar.config(text="Reiniciar")


    def iniciar_pausar_leitura(self):
        if self.esta_lendo:
            self.esta_lendo = False
            self.btn_iniciar_pausar.config(text="Continuar")
            if self.job_id:
                self.master.after_cancel(self.job_id) # Cancela o próximo 'after'
        else:
            self.esta_lendo = True
            self.btn_iniciar_pausar.config(text="Pausar")
            if self.indice_palavra_atual >= len(self.palavras): # Se chegou ao fim, reinicia
                self.indice_palavra_atual = 0
            self.atualizar_exibicao_palavra()

    def resetar_leitura(self):
        self.esta_lendo = False
        self.indice_palavra_atual = 0
        if self.job_id:
            self.master.after_cancel(self.job_id)
            self.job_id = None
        self.atualizar_exibicao_palavra() # Mostra a primeira palavra ou o texto inicial
        self.btn_iniciar_pausar.config(text="Iniciar")


# --- Inicializa a Aplicação Tkinter ---
if __name__ == "__main__":
    root = tk.Tk() # Cria a janela principal
    app = LeitorRapidoApp(root) # Cria uma instância da sua aplicação
    root.mainloop() # Inicia o loop principal do Tkinter (a janela fica aberta)