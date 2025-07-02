import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser, simpledialog # Importe colorchooser e simpledialog
import time
import re
from docx import Document

# --- Funções de Leitura de Arquivos ---

def ler_texto_de_docx(caminho_do_arquivo):
    """Lê o texto de um arquivo .docx e retorna uma lista de parágrafos."""
    try:
        doc = Document(caminho_do_arquivo)
        full_text_paragraphs = [p.text for p in doc.paragraphs]
        return full_text_paragraphs
    except Exception as e:
        messagebox.showerror("Erro ao Ler DOCX", f"Não foi possível ler o arquivo DOCX:\n{e}")
        return None

def ler_texto_de_txt(caminho_do_arquivo):
    """Lê o texto de um arquivo .txt e retorna uma lista de parágrafos."""
    try:
        with open(caminho_do_arquivo, 'r', encoding='utf-8') as arquivo:
            full_text = arquivo.read()
            paragraphs = [p.strip() for p in re.split(r'\n\s*\n', full_text) if p.strip()]
            return paragraphs
    except FileNotFoundError:
        messagebox.showerror("Erro de Arquivo", f"O arquivo não foi encontrado:\n{caminho_do_arquivo}")
        return None
    except Exception as e:
        messagebox.showerror("Erro ao Ler TXT", f"Não foi possível ler o arquivo TXT:\n{e}")
        return None

# --- Lógica Principal da Aplicação com Tkinter ---

class LeitorRapidoApp:
    def __init__(self, master):
        self.master = master
        master.title("Leitor Rápido de Texto")
        master.geometry("1000x580") # Largura e altura ajustadas para mais espaço

        self.texto_completo_paragrafos = []
        self.palavras = []
        self.indice_palavra_atual = 0
        self.esta_lendo = False
        self.job_id = None
        self.paragraph_start_indices = []

        # Variáveis para a customização visual
        self.cor_texto_atual = "blue"
        self.cor_fundo_atual = "white"
        self.tamanho_fonte_atual = 48
        self.nome_fonte_atual = "Arial" # Adicionando a opção de nome da fonte

        # --- Componentes da Interface ---

        self.palavra_label = tk.Label(master, text="Carregue um arquivo para começar.",
                                      font=(self.nome_fonte_atual, self.tamanho_fonte_atual, "bold"),
                                      fg=self.cor_texto_atual, bg=self.cor_fundo_atual)
        self.palavra_label.pack(pady=30, fill=tk.BOTH, expand=True)

        self.main_controls_frame = tk.Frame(master)
        self.main_controls_frame.pack(pady=10)

        self.basic_buttons_frame = tk.Frame(self.main_controls_frame)
        self.basic_buttons_frame.pack(side=tk.TOP, pady=5)

        self.btn_carregar = tk.Button(self.basic_buttons_frame, text="Carregar Arquivo", command=self.carregar_arquivo)
        self.btn_carregar.pack(side=tk.LEFT, padx=5)

        self.btn_iniciar_pausar = tk.Button(self.basic_buttons_frame, text="Iniciar", command=self.iniciar_pausar_leitura, state=tk.DISABLED)
        self.btn_iniciar_pausar.pack(side=tk.LEFT, padx=5)

        self.btn_resetar = tk.Button(self.basic_buttons_frame, text="Resetar", command=self.resetar_leitura, state=tk.DISABLED)
        self.btn_resetar.pack(side=tk.LEFT, padx=5)

        self.nav_speed_frame = tk.Frame(self.main_controls_frame)
        self.nav_speed_frame.pack(side=tk.TOP, pady=5)

        self.btn_voltar_10 = tk.Button(self.nav_speed_frame, text="<- 10 Palavras", command=self.voltar_10_palavras, state=tk.DISABLED)
        self.btn_voltar_10.pack(side=tk.LEFT, padx=5)

        self.btn_voltar_paragrafo = tk.Button(self.nav_speed_frame, text="<- Parágrafo", command=self.voltar_paragrafo, state=tk.DISABLED)
        self.btn_voltar_paragrafo.pack(side=tk.LEFT, padx=5)

        self.velocidade_label = tk.Label(self.nav_speed_frame, text="Velocidade (PPM): 300")
        self.velocidade_label.pack(side=tk.LEFT, padx=10)

        self.velocidade_scale = tk.Scale(self.nav_speed_frame, from_=100, to=1000, orient=tk.HORIZONTAL,
                                        length=200, command=self.atualizar_velocidade_label, resolution=50)
        self.velocidade_scale.set(300)
        self.velocidade_scale.pack(side=tk.LEFT, padx=5)

        self.frame_progresso = tk.Frame(master)
        self.frame_progresso.pack(pady=10)

        self.progresso_label = tk.Label(self.frame_progresso, text="Progresso: 0/0 palavras")
        self.progresso_label.pack(side=tk.LEFT, padx=5)
        
        # --- NOVOS CONTROLES DE CUSTOMIZAÇÃO VISUAL ---
        self.customization_frame = tk.Frame(master)
        self.customization_frame.pack(pady=10)

        self.btn_mudar_cor_texto = tk.Button(self.customization_frame, text="Cor do Texto", command=self.mudar_cor_texto)
        self.btn_mudar_cor_texto.pack(side=tk.LEFT, padx=5)

        self.btn_mudar_cor_fundo = tk.Button(self.customization_frame, text="Cor de Fundo", command=self.mudar_cor_fundo)
        self.btn_mudar_cor_fundo.pack(side=tk.LEFT, padx=5)

        self.btn_mudar_tamanho_fonte = tk.Button(self.customization_frame, text="Tamanho da Fonte", command=self.mudar_tamanho_fonte)
        self.btn_mudar_tamanho_fonte.pack(side=tk.LEFT, padx=5)

        self.btn_mudar_nome_fonte = tk.Button(self.customization_frame, text="Nome da Fonte", command=self.mudar_nome_fonte)
        self.btn_mudar_nome_fonte.pack(side=tk.LEFT, padx=5)

    # --- Métodos da Classe ---
    def atualizar_velocidade_label(self, val):
        self.velocidade_label.config(text=f"Velocidade (PPM): {int(float(val))}")

    def carregar_arquivo(self):
        self.resetar_leitura()
        
        caminho_arquivo = filedialog.askopenfilename(
            filetypes=[
                ("Documentos Word", "*.docx"),
                ("Arquivos de Texto", "*.txt"),
                ("Todos os Arquivos", "*.*")
            ]
        )
        if caminho_arquivo:
            self.habilitar_botoes(False) 

            if caminho_arquivo.lower().endswith('.docx'):
                self.texto_completo_paragrafos = ler_texto_de_docx(caminho_arquivo)
            elif caminho_arquivo.lower().endswith('.txt'):
                self.texto_completo_paragrafos = ler_texto_de_txt(caminho_arquivo)
            else:
                messagebox.showwarning("Formato Não Suportado", "Por favor, selecione um arquivo .txt ou .docx.")
                self.palavra_label.config(text="Formato não suportado!")
                self.habilitar_botoes(False)
                return
            
            if self.texto_completo_paragrafos:
                self.palavras = []
                self.paragraph_start_indices = [0] 

                for paragraph in self.texto_completo_paragrafos:
                    texto_para_dividir = paragraph.lower()
                    
                    tokens = re.findall(r'\S+', texto_para_dividir) 
                    
                    limpo_e_filtrado = [token for token in tokens if token.strip()]
                    
                    self.palavras.extend(limpo_e_filtrado)
                    
                    if paragraph != self.texto_completo_paragrafos[-1] and limpo_e_filtrado:
                        self.paragraph_start_indices.append(len(self.palavras))
                
                self.paragraph_start_indices = sorted(list(set(self.paragraph_start_indices)))
                if self.paragraph_start_indices and self.paragraph_start_indices[-1] == len(self.palavras) and len(self.paragraph_start_indices) > 1:
                    self.paragraph_start_indices.pop()
                
                if not self.palavras:
                    messagebox.showwarning("Arquivo Vazio", "O arquivo selecionado não contém texto válido.")
                    self.palavra_label.config(text="Arquivo vazio ou sem texto válido.")
                    self.habilitar_botoes(False)
                    return

                self.indice_palavra_atual = 0
                self.atualizar_exibicao_palavra()
                self.btn_iniciar_pausar.config(text="Iniciar")
                self.esta_lendo = False
                self.habilitar_botoes(True)
                self.atualizar_progresso()
            else:
                messagebox.showwarning("Arquivo Vazio", "O arquivo selecionado não contém texto válido.")
                self.palavra_label.config(text="Erro ao carregar o arquivo ou arquivo vazio.")
                self.habilitar_botoes(False)
        else:
            self.habilitar_botoes(False)
            if self.palavras:
                self.habilitar_botoes(True)
                self.btn_iniciar_pausar.config(text="Iniciar")


    def atualizar_exibicao_palavra(self):
        if self.indice_palavra_atual < len(self.palavras):
            self.palavra_label.config(text=self.palavras[self.indice_palavra_atual])
            self.indice_palavra_atual += 1
            self.atualizar_progresso()

            ppm = self.velocidade_scale.get()
            tempo_por_palavra_ms = (60 / ppm) * 1000

            if self.esta_lendo:
                self.job_id = self.master.after(int(tempo_por_palavra_ms), self.atualizar_exibicao_palavra)
        else:
            self.palavra_label.config(text="Fim da leitura!")
            self.esta_lendo = False
            self.btn_iniciar_pausar.config(text="Reiniciar")
            if self.job_id:
                self.master.after_cancel(self.job_id)
                self.job_id = None
            self.habilitar_botoes(True)


    def iniciar_pausar_leitura(self):
        if not self.palavras:
            messagebox.showwarning("Nenhum Texto", "Por favor, carregue um arquivo antes de iniciar a leitura.")
            return

        if self.esta_lendo:
            self.esta_lendo = False
            self.btn_iniciar_pausar.config(text="Continuar")
            if self.job_id:
                self.master.after_cancel(self.job_id)
        else:
            self.esta_lendo = True
            self.btn_iniciar_pausar.config(text="Pausar")
            if self.indice_palavra_atual >= len(self.palavras):
                self.indice_palavra_atual = 0
                self.atualizar_progresso()
            self.atualizar_exibicao_palavra()

    def resetar_leitura(self):
        self.esta_lendo = False
        self.indice_palavra_atual = 0
        if self.job_id:
            self.master.after_cancel(self.job_id)
            self.job_id = None
        
        if self.palavras:
            self.palavra_label.config(text=self.palavras[0])
            self.btn_iniciar_pausar.config(text="Iniciar")
            self.btn_iniciar_pausar.config(state=tk.NORMAL)
            self.btn_resetar.config(state=tk.NORMAL)
        else:
            self.palavra_label.config(text="Carregue um arquivo para começar.")
            self.btn_iniciar_pausar.config(state=tk.DISABLED)
            self.btn_resetar.config(state=tk.DISABLED)
        
        self.atualizar_progresso()
        self.btn_carregar.config(state=tk.NORMAL)

    def atualizar_progresso(self):
        total_palavras = len(self.palavras)
        palavras_lidas = min(self.indice_palavra_atual, total_palavras)
        self.progresso_label.config(text=f"Progresso: {palavras_lidas}/{total_palavras} palavras")
    
    def habilitar_botoes(self, habilitar):
        self.btn_carregar.config(state=tk.NORMAL) 
        if habilitar:
            self.btn_iniciar_pausar.config(state=tk.NORMAL)
            self.btn_resetar.config(state=tk.NORMAL)
            self.btn_voltar_10.config(state=tk.NORMAL)
            self.btn_voltar_paragrafo.config(state=tk.NORMAL)
        else:
            self.btn_iniciar_pausar.config(state=tk.DISABLED)
            self.btn_resetar.config(state=tk.DISABLED)
            self.btn_voltar_10.config(state=tk.DISABLED)
            self.btn_voltar_paragrafo.config(state=tk.DISABLED)

    # --- Funções de Navegação ---
    def voltar_10_palavras(self):
        if not self.palavras: return
        self.esta_lendo = False
        if self.job_id:
            self.master.after_cancel(self.job_id)
            self.job_id = None
        
        self.indice_palavra_atual = max(0, self.indice_palavra_atual - 10)
        self.atualizar_exibicao_palavra_sem_avancar()
        self.btn_iniciar_pausar.config(text="Continuar")

    def voltar_paragrafo(self):
        if not self.palavras or not self.paragraph_start_indices: return
        self.esta_lendo = False
        if self.job_id:
            self.master.after_cancel(self.job_id)
            self.job_id = None

        current_paragraph_index = 0
        for i, start_index in enumerate(self.paragraph_start_indices):
            if self.indice_palavra_atual > start_index:
                current_paragraph_index = i
            else:
                break
        
        if current_paragraph_index == 0:
            self.indice_palavra_atual = 0
        else:
            if self.indice_palavra_atual == self.paragraph_start_indices[current_paragraph_index]:
                self.indice_palavra_atual = self.paragraph_start_indices[current_paragraph_index - 1]
            else:
                self.indice_palavra_atual = self.paragraph_start_indices[current_paragraph_index]

        self.atualizar_exibicao_palavra_sem_avancar()
        self.btn_iniciar_pausar.config(text="Continuar")

    def atualizar_exibicao_palavra_sem_avancar(self):
        """Atualiza o label com a palavra atual no índice atual, sem avançar o índice."""
        if self.indice_palavra_atual < len(self.palavras):
            self.palavra_label.config(text=self.palavras[self.indice_palavra_atual])
        else:
            self.palavra_label.config(text=self.palavras[-1] if self.palavras else "Fim da leitura!")
            self.indice_palavra_atual = len(self.palavras)
        self.atualizar_progresso()

    # --- NOVOS MÉTODOS DE CUSTOMIZAÇÃO VISUAL ---
    def aplicar_estilo_fonte(self):
        """Aplica a fonte, tamanho e cor ao label da palavra."""
        self.palavra_label.config(font=(self.nome_fonte_atual, self.tamanho_fonte_atual, "bold"),
                                  fg=self.cor_texto_atual,
                                  bg=self.cor_fundo_atual)
        # Se a janela principal também tiver fundo, pode atualizar aqui
        # self.master.config(bg=self.cor_fundo_atual)


    def mudar_cor_texto(self):
        """Abre o seletor de cores para mudar a cor do texto."""
        cor_selecionada = colorchooser.askcolor(title="Escolha a Cor do Texto", initialcolor=self.cor_texto_atual)
        if cor_selecionada[1]: # Se uma cor foi selecionada (o usuário não cancelou)
            self.cor_texto_atual = cor_selecionada[1]
            self.aplicar_estilo_fonte()

    def mudar_cor_fundo(self):
        """Abre o seletor de cores para mudar a cor de fundo."""
        cor_selecionada = colorchooser.askcolor(title="Escolha a Cor de Fundo", initialcolor=self.cor_fundo_atual)
        if cor_selecionada[1]: # Se uma cor foi selecionada
            self.cor_fundo_atual = cor_selecionada[1]
            self.aplicar_estilo_fonte() # Atualiza o label para refletir a nova cor de fundo

    def mudar_tamanho_fonte(self):
        """Abre uma caixa de diálogo para o usuário digitar o tamanho da fonte."""
        novo_tamanho = simpledialog.askinteger("Tamanho da Fonte", "Digite o novo tamanho da fonte:",
                                              initialvalue=self.tamanho_fonte_atual, minvalue=10, maxvalue=100)
        if novo_tamanho is not None: # Se o usuário digitou um valor (não cancelou)
            self.tamanho_fonte_atual = novo_tamanho
            self.aplicar_estilo_fonte()

    def mudar_nome_fonte(self):
        """Abre uma caixa de diálogo para o usuário digitar o nome da fonte."""
        novo_nome = simpledialog.askstring("Nome da Fonte", "Digite o novo nome da fonte (ex: Arial, Times New Roman, Courier New):",
                                           initialvalue=self.nome_fonte_atual)
        if novo_nome: # Se o usuário digitou um nome (não cancelou)
            self.nome_fonte_atual = novo_nome
            self.aplicar_estilo_fonte()

# --- Inicializa a Aplicação Tkinter ---
if __name__ == "__main__":
    root = tk.Tk()
    app = LeitorRapidoApp(root)
    root.mainloop()