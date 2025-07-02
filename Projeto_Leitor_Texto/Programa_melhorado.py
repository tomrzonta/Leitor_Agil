import tkinter as tk
from tkinter import filedialog, messagebox
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
            # Divide o texto em parágrafos usando quebras de linha duplas ou mais
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
        master.geometry("950x500") # Largura ajustada para acomodar os botões

        self.texto_completo_paragrafos = [] # Armazena parágrafos originais
        self.palavras = [] # Lista de palavras a serem exibidas
        self.indice_palavra_atual = 0
        self.esta_lendo = False
        self.job_id = None # ID para o agendador de eventos do Tkinter (after)
        self.paragraph_start_indices = [] # Armazena os índices de início de cada parágrafo na lista de palavras

        # --- Componentes da Interface ---

        # Label para exibir a palavra atual
        self.palavra_label = tk.Label(master, text="Carregue um arquivo para começar.", font=("Arial", 48, "bold"), fg="blue")
        self.palavra_label.pack(pady=30, fill=tk.BOTH, expand=True)

        # Frame principal para os controles, para organização
        self.main_controls_frame = tk.Frame(master)
        self.main_controls_frame.pack(pady=10)

        # Frame para os botões principais (Carregar, Iniciar, Resetar)
        self.basic_buttons_frame = tk.Frame(self.main_controls_frame)
        self.basic_buttons_frame.pack(side=tk.TOP, pady=5) # Empacota no topo do main_controls_frame

        self.btn_carregar = tk.Button(self.basic_buttons_frame, text="Carregar Arquivo", command=self.carregar_arquivo)
        self.btn_carregar.pack(side=tk.LEFT, padx=5)

        self.btn_iniciar_pausar = tk.Button(self.basic_buttons_frame, text="Iniciar", command=self.iniciar_pausar_leitura, state=tk.DISABLED) # Começa desabilitado
        self.btn_iniciar_pausar.pack(side=tk.LEFT, padx=5)

        self.btn_resetar = tk.Button(self.basic_buttons_frame, text="Resetar", command=self.resetar_leitura, state=tk.DISABLED) # Começa desabilitado
        self.btn_resetar.pack(side=tk.LEFT, padx=5)

        # Frame para os botões de navegação e velocidade
        self.nav_speed_frame = tk.Frame(self.main_controls_frame)
        self.nav_speed_frame.pack(side=tk.TOP, pady=5) # Empacota no topo do main_controls_frame, abaixo do basic_buttons_frame

        # Novos botões de navegação
        self.btn_voltar_10 = tk.Button(self.nav_speed_frame, text="<- 10 Palavras", command=self.voltar_10_palavras, state=tk.DISABLED)
        self.btn_voltar_10.pack(side=tk.LEFT, padx=5)

        self.btn_voltar_paragrafo = tk.Button(self.nav_speed_frame, text="<- Parágrafo", command=self.voltar_paragrafo, state=tk.DISABLED)
        self.btn_voltar_paragrafo.pack(side=tk.LEFT, padx=5)

        # Controle de Velocidade (PPM)
        self.velocidade_label = tk.Label(self.nav_speed_frame, text="Velocidade (PPM): 300")
        self.velocidade_label.pack(side=tk.LEFT, padx=10)

        self.velocidade_scale = tk.Scale(self.nav_speed_frame, from_=100, to=1000, orient=tk.HORIZONTAL,
                                        length=200, command=self.atualizar_velocidade_label, resolution=50) # Resolução de 50 PPM
        self.velocidade_scale.set(300)
        self.velocidade_scale.pack(side=tk.LEFT, padx=5)

        # Barra de Progresso e Contador de Palavras
        self.frame_progresso = tk.Frame(master)
        self.frame_progresso.pack(pady=10)

        self.progresso_label = tk.Label(self.frame_progresso, text="Progresso: 0/0 palavras")
        self.progresso_label.pack(side=tk.LEFT, padx=5)

    def atualizar_velocidade_label(self, val):
        self.velocidade_label.config(text=f"Velocidade (PPM): {int(float(val))}")

    def carregar_arquivo(self):
        # Reinicia o estado da leitura e da interface
        self.resetar_leitura()
        
        # Abre a caixa de diálogo para seleção de arquivo
        caminho_arquivo = filedialog.askopenfilename(
            filetypes=[
                ("Documentos Word", "*.docx"),
                ("Arquivos de Texto", "*.txt"),
                ("Todos os Arquivos", "*.*")
            ]
        )
        if caminho_arquivo:
            # Desabilita botões enquanto carrega o arquivo
            self.habilitar_botoes(False) 

            # Determina o tipo de arquivo e chama a função de leitura apropriada
            if caminho_arquivo.lower().endswith('.docx'):
                self.texto_completo_paragrafos = ler_texto_de_docx(caminho_arquivo)
            elif caminho_arquivo.lower().endswith('.txt'):
                self.texto_completo_paragrafos = ler_texto_de_txt(caminho_arquivo)
            else:
                messagebox.showwarning("Formato Não Suportado", "Por favor, selecione um arquivo .txt ou .docx.")
                self.palavra_label.config(text="Formato não suportado!")
                self.habilitar_botoes(False) # Apenas carregar fica ativo
                return
            
            # Processa os parágrafos se o texto foi carregado com sucesso
            if self.texto_completo_paragrafos:
                self.palavras = []
                self.paragraph_start_indices = [0] # O primeiro parágrafo começa no índice 0 da lista de palavras

                for paragraph in self.texto_completo_paragrafos:
                    texto_para_dividir = paragraph.lower()
                    
                    # --- Lógica para PONTUAÇÃO ANEXADA ---
                    # Essa regex pega qualquer sequência de caracteres que NÃO seja um espaço.
                    # Isso fará com que "palavra." ou "mundo!" sejam tratados como uma única "palavra".
                    tokens = re.findall(r'\S+', texto_para_dividir) 
                    
                    # Filtra tokens que são apenas espaços ou vazios
                    limpo_e_filtrado = [token for token in tokens if token.strip()]
                    
                    self.palavras.extend(limpo_e_filtrado)
                    
                    # Adiciona o índice de início do próximo parágrafo
                    # Verifica se não é o último parágrafo e se o parágrafo atual não estava vazio
                    if paragraph != self.texto_completo_paragrafos[-1] and limpo_e_filtrado:
                        self.paragraph_start_indices.append(len(self.palavras))
                
                # Garante que os índices de parágrafo sejam únicos e em ordem,
                # e remove o último se for redundante (aponta para o fim da lista total)
                self.paragraph_start_indices = sorted(list(set(self.paragraph_start_indices)))
                if self.paragraph_start_indices and self.paragraph_start_indices[-1] == len(self.palavras) and len(self.paragraph_start_indices) > 1:
                    self.paragraph_start_indices.pop()
                
                # Se o arquivo estiver vazio após o processamento
                if not self.palavras:
                    messagebox.showwarning("Arquivo Vazio", "O arquivo selecionado não contém texto válido.")
                    self.palavra_label.config(text="Arquivo vazio ou sem texto válido.")
                    self.habilitar_botoes(False)
                    return

                # Inicializa a exibição após carregar e processar o texto
                self.indice_palavra_atual = 0
                self.atualizar_exibicao_palavra()
                self.btn_iniciar_pausar.config(text="Iniciar")
                self.esta_lendo = False # Garante que a leitura esteja parada no início
                self.habilitar_botoes(True) # Habilita todos os botões após carregar
                self.atualizar_progresso()
            else:
                # Se o texto_completo_paragrafos veio vazio (mesmo que o arquivo existisse)
                messagebox.showwarning("Arquivo Vazio", "O arquivo selecionado não contém texto válido ou houve um erro na leitura.")
                self.palavra_label.config(text="Erro ao carregar o arquivo ou arquivo vazio.")
                self.habilitar_botoes(False) # Apenas carregar fica ativo
        else: # Se o usuário cancelou a seleção do arquivo
            self.habilitar_botoes(False) # Apenas carregar fica ativo se nenhum arquivo foi selecionado
            if self.palavras: # Se já havia um texto carregado antes de cancelar, mantém os botões ativos
                self.habilitar_botoes(True)
                self.btn_iniciar_pausar.config(text="Iniciar")


    def atualizar_exibicao_palavra(self):
        """Atualiza o label com a palavra atual e avança o índice."""
        if self.indice_palavra_atual < len(self.palavras):
            self.palavra_label.config(text=self.palavras[self.indice_palavra_atual])
            self.indice_palavra_atual += 1
            self.atualizar_progresso()

            # Calcula o tempo de exibição da palavra baseado nas PPM
            ppm = self.velocidade_scale.get()
            tempo_por_palavra_ms = (60 / ppm) * 1000 # Converte segundos para milissegundos

            # Agenda a próxima atualização se a leitura estiver ativa
            if self.esta_lendo:
                self.job_id = self.master.after(int(tempo_por_palavra_ms), self.atualizar_exibicao_palavra)
        else:
            # Fim da leitura
            self.palavra_label.config(text="Fim da leitura!")
            self.esta_lendo = False
            self.btn_iniciar_pausar.config(text="Reiniciar")
            if self.job_id: # Cancela qualquer agendamento pendente
                self.master.after_cancel(self.job_id)
                self.job_id = None
            self.habilitar_botoes(True) # Habilita botões no fim da leitura


    def iniciar_pausar_leitura(self):
        """Inicia, pausa ou continua a leitura do texto."""
        if not self.palavras:
            messagebox.showwarning("Nenhum Texto", "Por favor, carregue um arquivo antes de iniciar a leitura.")
            return

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
                self.atualizar_progresso() # Reseta o progresso visualmente
            self.atualizar_exibicao_palavra() # Inicia/continua a exibição

    def resetar_leitura(self):
        """Reseta a leitura para o início do texto."""
        self.esta_lendo = False
        self.indice_palavra_atual = 0
        if self.job_id:
            self.master.after_cancel(self.job_id)
            self.job_id = None
        
        # Exibe a primeira palavra se houver texto, senão a mensagem inicial
        if self.palavras:
            self.palavra_label.config(text=self.palavras[0])
            self.btn_iniciar_pausar.config(text="Iniciar")
            self.btn_iniciar_pausar.config(state=tk.NORMAL) # Habilita iniciar
            self.btn_resetar.config(state=tk.NORMAL) # Habilita resetar
        else:
            self.palavra_label.config(text="Carregue um arquivo para começar.")
            self.btn_iniciar_pausar.config(state=tk.DISABLED) # Desabilita iniciar
            self.btn_resetar.config(state=tk.DISABLED) # Desabilita resetar
        
        self.atualizar_progresso() # Reseta o progresso visualmente
        self.btn_carregar.config(state=tk.NORMAL) # Sempre habilita o carregar

    def atualizar_progresso(self):
        """Atualiza a exibição do progresso da leitura."""
        total_palavras = len(self.palavras)
        palavras_lidas = min(self.indice_palavra_atual, total_palavras) # Garante que não exceda o total
        self.progresso_label.config(text=f"Progresso: {palavras_lidas}/{total_palavras} palavras")
    
    def habilitar_botoes(self, habilitar):
        """Controla o estado (habilitado/desabilitado) dos botões."""
        # O botão de carregar arquivo sempre fica ativo
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
        """Volta o índice de leitura em 10 palavras."""
        if not self.palavras: return # Não faz nada se não houver palavras
        self.esta_lendo = False # Pausa a leitura
        if self.job_id: # Cancela qualquer agendamento pendente
            self.master.after_cancel(self.job_id)
            self.job_id = None
        
        # Garante que o índice não seja menor que 0
        self.indice_palavra_atual = max(0, self.indice_palavra_atual - 10)
        self.atualizar_exibicao_palavra_sem_avancar() # Atualiza a exibição sem avançar o índice
        self.btn_iniciar_pausar.config(text="Continuar") # Muda o texto do botão Iniciar

    def voltar_paragrafo(self):
        """Volta o índice de leitura para o início do parágrafo anterior."""
        if not self.palavras or not self.paragraph_start_indices: return # Não faz nada se não houver palavras ou parágrafos
        self.esta_lendo = False # Pausa a leitura
        if self.job_id: # Cancela qualquer agendamento pendente
            self.master.after_cancel(self.job_id)
            self.job_id = None

        # Encontra o índice do parágrafo atual (ou o parágrafo mais próximo antes do índice atual)
        current_paragraph_index = 0
        for i, start_index in enumerate(self.paragraph_start_indices):
            if self.indice_palavra_atual > start_index: # Se o índice atual está DENTRO ou APÓS este parágrafo
                current_paragraph_index = i
            else: # Se o índice atual é MENOR que o início deste parágrafo, já passamos do nosso alvo
                break
        
        # Agora, determine o novo índice: início do parágrafo anterior
        if current_paragraph_index == 0:
            # Se já estamos no primeiro parágrafo, volta para o início dele (índice 0)
            self.indice_palavra_atual = 0
        else:
            # Se a palavra atual já está no início exato de um parágrafo (que não é o primeiro),
            # o usuário provavelmente quer ir para o parágrafo ANTERIOR a este.
            # Por exemplo, se estou na primeira palavra do parágrafo 2 e clico, quero ir para o parágrafo 1.
            if self.indice_palavra_atual == self.paragraph_start_indices[current_paragraph_index]:
                self.indice_palavra_atual = self.paragraph_start_indices[current_paragraph_index - 1]
            else:
                # Se estou no meio de um parágrafo, volto para o início do parágrafo atual.
                self.indice_palavra_atual = self.paragraph_start_indices[current_paragraph_index]

        self.atualizar_exibicao_palavra_sem_avancar()
        self.btn_iniciar_pausar.config(text="Continuar")

    def atualizar_exibicao_palavra_sem_avancar(self):
        """Atualiza o label com a palavra atual no índice atual, sem avançar o índice."""
        if self.indice_palavra_atual < len(self.palavras):
            self.palavra_label.config(text=self.palavras[self.indice_palavra_atual])
        else:
            # Se o índice for para o final ou além, mostra a última palavra ou mensagem de fim
            self.palavra_label.config(text=self.palavras[-1] if self.palavras else "Fim da leitura!")
            self.indice_palavra_atual = len(self.palavras) # Garante que o índice esteja no fim para consistência
        self.atualizar_progresso()


# --- Inicializa a Aplicação Tkinter ---
if __name__ == "__main__":
    root = tk.Tk() # Cria a janela principal
    app = LeitorRapidoApp(root) # Cria uma instância da sua aplicação
    root.mainloop() # Inicia o loop principal do Tkinter (a janela fica aberta)