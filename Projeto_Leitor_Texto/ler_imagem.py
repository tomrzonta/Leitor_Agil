import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser, simpledialog
import time
import re
from docx import Document
import json
import os
from datetime import datetime
import PyPDF2 # Importação para leitura de PDF


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

def ler_texto_de_pdf(caminho_do_arquivo):
    """Lê o texto de um arquivo .pdf e retorna uma lista de parágrafos."""
    full_text = ""
    try:
        with open(caminho_do_arquivo, 'rb') as arquivo_pdf:
            reader = PyPDF2.PdfReader(arquivo_pdf)
            for page in reader.pages:
                full_text += page.extract_text() + "\n" # Extrai texto da página
        
        # Divide o texto completo em parágrafos, similar ao TXT
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', full_text) if p.strip()]
        return paragraphs
    except FileNotFoundError:
        messagebox.showerror("Erro de Arquivo", f"O arquivo PDF não foi encontrado:\n{caminho_do_arquivo}")
        return None
    except Exception as e:
        messagebox.showerror("Erro ao Ler PDF", f"Não foi possível ler o arquivo PDF:\n{e}")
        return None

# --- Lógica Principal da Aplicação com Tkinter ---

class LeitorRapidoApp:
    def __init__(self, master):
        self.master = master
        master.title("Leitor Rápido de Texto")
        master.geometry("1000x650")

        self.texto_completo_paragrafos = []
        self.palavras = []
        self.indice_palavra_atual = 0
        self.esta_lendo = False
        self.job_id = None
        self.paragraph_start_indices = []
        self.caminho_arquivo_atual = None

        # --- Configuração da pasta de saves e config ---
        self.program_dir = os.path.dirname(os.path.abspath(__file__))
        self.saves_dir = os.path.join(self.program_dir, "progress_saves")
        self.config_dir = os.path.join(self.program_dir, "config")
        self.settings_file = os.path.join(self.config_dir, "settings.json")

        os.makedirs(self.saves_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)

        # Variáveis para a customização visual (valores padrão)
        self.cor_texto_atual = "blue"
        self.cor_fundo_atual = "white"
        self.tamanho_fonte_atual = 48
        self.nome_fonte_atual = "Arial"
        self.velocidade_leitura_atual = 300
        
        # Variáveis para aceleração gradual
        self.velocidade_inicial_aceleracao = 100
        self.passo_aceleracao = 25
        self.velocidade_leitura_atual_temp = 0


        # Carrega as configurações salvas ao iniciar
        self.carregar_configuracoes()

        # --- Componentes da Interface ---

        self.palavra_label = tk.Label(master, text="Carregue um arquivo para começar.",
                                      font=("Arial", 48, "bold"), fg="blue", bg="white")
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

        self.navigation_frame = tk.Frame(self.main_controls_frame)
        self.navigation_frame.pack(side=tk.TOP, pady=5)

        self.btn_voltar_paragrafo = tk.Button(self.navigation_frame, text="<- Parágrafo", command=self.voltar_paragrafo, state=tk.DISABLED)
        self.btn_voltar_paragrafo.pack(side=tk.LEFT, padx=5)

        self.btn_voltar_10 = tk.Button(self.navigation_frame, text="<- 10 Palavras", command=self.voltar_10_palavras, state=tk.DISABLED)
        self.btn_voltar_10.pack(side=tk.LEFT, padx=5)
        
        self.btn_avancar_10 = tk.Button(self.navigation_frame, text="10 Palavras ->", command=self.avancar_10_palavras, state=tk.DISABLED)
        self.btn_avancar_10.pack(side=tk.LEFT, padx=5)

        self.btn_avancar_paragrafo = tk.Button(self.navigation_frame, text="Parágrafo ->", command=self.avancar_paragrafo, state=tk.DISABLED)
        self.btn_avancar_paragrafo.pack(side=tk.LEFT, padx=5)


        self.speed_frame = tk.Frame(self.main_controls_frame)
        self.speed_frame.pack(side=tk.TOP, pady=5)

        self.velocidade_label = tk.Label(self.speed_frame, text=f"Velocidade (PPM): {self.velocidade_leitura_atual}")
        self.velocidade_label.pack(side=tk.LEFT, padx=10)

        self.velocidade_scale = tk.Scale(self.speed_frame, from_=100, to=1000, orient=tk.HORIZONTAL,
                                        length=200, command=self.atualizar_velocidade_label, resolution=50)
        self.velocidade_scale.set(self.velocidade_leitura_atual)
        self.velocidade_scale.pack(side=tk.LEFT, padx=5)

        self.frame_progresso = tk.Frame(master)
        self.frame_progresso.pack(pady=10)

        self.progresso_label = tk.Label(self.frame_progresso, text="Progresso: 0/0 palavras")
        self.progresso_label.pack(side=tk.LEFT, padx=5)
        
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

        self.progress_controls_frame = tk.Frame(master)
        self.progress_controls_frame.pack(pady=10)

        self.btn_salvar_progresso = tk.Button(self.progress_controls_frame, text="Salvar Progresso", command=self.salvar_progresso, state=tk.DISABLED)
        self.btn_salvar_progresso.pack(side=tk.LEFT, padx=5)

        self.btn_carregar_progresso = tk.Button(self.progress_controls_frame, text="Carregar Progresso", command=self.carregar_progresso)
        self.btn_carregar_progresso.pack(side=tk.LEFT, padx=5)

        self.aplicar_estilo_fonte()

        # Salva as configurações ao fechar a janela
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)


    # --- Métodos da Classe ---
    def atualizar_velocidade_label(self, val):
        self.velocidade_leitura_atual = int(float(val))
        self.velocidade_label.config(text=f"Velocidade (PPM): {self.velocidade_leitura_atual}")
        # Quando o usuário muda a velocidade manualmente, a aceleração é resetada
        self.velocidade_leitura_atual_temp = self.velocidade_leitura_atual


    def carregar_arquivo(self, caminho_predefinido=None, indice_predefinido=0):
        self.resetar_leitura()
        
        caminho_arquivo = caminho_predefinido
        if not caminho_arquivo:
            caminho_arquivo = filedialog.askopenfilename(
                filetypes=[
                    ("Documentos Word", "*.docx"),
                    ("Arquivos de Texto", "*.txt"),
                    ("Arquivos PDF", "*.pdf"), # Adiciona filtro para PDF
                    ("Todos os Arquivos", "*.*")
                ]
            )
        
        if caminho_arquivo:
            self.habilitar_botoes(False) 
            self.caminho_arquivo_atual = caminho_arquivo

            if caminho_arquivo.lower().endswith('.docx'):
                self.texto_completo_paragrafos = ler_texto_de_docx(caminho_arquivo)
            elif caminho_arquivo.lower().endswith('.txt'):
                self.texto_completo_paragrafos = ler_texto_de_txt(caminho_arquivo)
            elif caminho_arquivo.lower().endswith('.pdf'): # Adiciona o caso para PDF
                self.texto_completo_paragrafos = ler_texto_de_pdf(caminho_arquivo)
            else:
                messagebox.showwarning("Formato Não Suportado", "Por favor, selecione um arquivo .txt, .docx ou .pdf.")
                self.palavra_label.config(text="Formato não suportado!")
                self.habilitar_botoes(False)
                self.caminho_arquivo_atual = None
                return
            
            if self.texto_completo_paragrafos:
                self.palavras = []
                self.paragraph_start_indices = [0] 

                for paragraph in self.texto_completo_paragrafos:
                    # Garante capitalização e pontuação anexada
                    tokens = re.findall(r'\S+', paragraph) 
                    
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
                    self.caminho_arquivo_atual = None
                    return

                self.indice_palavra_atual = min(indice_predefinido, len(self.palavras) - 1)
                if self.indice_palavra_atual < 0: self.indice_palavra_atual = 0

                self.atualizar_exibicao_palavra_sem_avancar()
                self.btn_iniciar_pausar.config(text="Iniciar")
                self.esta_lendo = False
                self.habilitar_botoes(True)
                self.atualizar_progresso()
                self.btn_salvar_progresso.config(state=tk.NORMAL)
            else:
                messagebox.showwarning("Arquivo Vazio", "O arquivo selecionado não contém texto válido.")
                self.palavra_label.config(text="Erro ao carregar o arquivo ou arquivo vazio.")
                self.habilitar_botoes(False)
                self.caminho_arquivo_atual = None
        else:
            self.habilitar_botoes(False)
            self.btn_carregar.config(state=tk.NORMAL)
            self.btn_carregar_progresso.config(state=tk.NORMAL)
            if self.palavras:
                self.habilitar_botoes(True)
                self.btn_iniciar_pausar.config(text="Iniciar")
                self.btn_salvar_progresso.config(state=tk.NORMAL)

    def atualizar_exibicao_palavra(self):
        if self.indice_palavra_atual < len(self.palavras):
            self.palavra_label.config(text=self.palavras[self.indice_palavra_atual])
            self.indice_palavra_atual += 1
            self.atualizar_progresso()

            ppm_alvo = self.velocidade_scale.get()
            
            if self.velocidade_leitura_atual_temp < ppm_alvo:
                self.velocidade_leitura_atual_temp += self.passo_aceleracao
                if self.velocidade_leitura_atual_temp > ppm_alvo:
                    self.velocidade_leitura_atual_temp = ppm_alvo
            
            tempo_por_palavra_ms = (60 / self.velocidade_leitura_atual_temp) * 1000

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
            
            self.velocidade_leitura_atual_temp = self.velocidade_inicial_aceleracao
            if self.velocidade_leitura_atual_temp > self.velocidade_scale.get():
                self.velocidade_leitura_atual_temp = self.velocidade_scale.get()

            self.atualizar_exibicao_palavra()

    def resetar_leitura(self):
        self.esta_lendo = False
        self.indice_palavra_atual = 0
        if self.job_id:
            self.master.after_cancel(self.job_id)
            self.job_id = None
        
        self.velocidade_leitura_atual_temp = self.velocidade_scale.get() 

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
        self.btn_salvar_progresso.config(state=tk.DISABLED)
        self.btn_carregar_progresso.config(state=tk.NORMAL)

    def atualizar_progresso(self):
        total_palavras = len(self.palavras)
        palavras_lidas = min(self.indice_palavra_atual, total_palavras)
        self.progresso_label.config(text=f"Progresso: {palavras_lidas}/{total_palavras} palavras")
    
    def habilitar_botoes(self, habilitar):
        self.btn_carregar.config(state=tk.NORMAL) 
        self.btn_carregar_progresso.config(state=tk.NORMAL)
        if habilitar:
            self.btn_iniciar_pausar.config(state=tk.NORMAL)
            self.btn_resetar.config(state=tk.NORMAL)
            self.btn_voltar_10.config(state=tk.NORMAL)
            self.btn_voltar_paragrafo.config(state=tk.NORMAL)
            self.btn_avancar_10.config(state=tk.NORMAL)
            self.btn_avancar_paragrafo.config(state=tk.NORMAL)
            self.btn_salvar_progresso.config(state=tk.NORMAL)
        else:
            self.btn_iniciar_pausar.config(state=tk.DISABLED)
            self.btn_resetar.config(state=tk.DISABLED)
            self.btn_voltar_10.config(state=tk.DISABLED)
            self.btn_voltar_paragrafo.config(state=tk.DISABLED)
            self.btn_avancar_10.config(state=tk.DISABLED)
            self.btn_avancar_paragrafo.config(state=tk.DISABLED)
            self.btn_salvar_progresso.config(state=tk.DISABLED)

    # --- Funções de Navegação (Voltar) ---
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

    # --- Funções de Navegação (Avançar) ---
    def avancar_10_palavras(self):
        if not self.palavras: return
        self.esta_lendo = False
        if self.job_id:
            self.master.after_cancel(self.job_id)
            self.job_id = None
        
        self.indice_palavra_atual = min(len(self.palavras) - 1, self.indice_palavra_atual + 10)
        self.atualizar_exibicao_palavra_sem_avancar()
        self.btn_iniciar_pausar.config(text="Continuar")

    def avancar_paragrafo(self):
        if not self.palavras or not self.paragraph_start_indices: return
        self.esta_lendo = False
        if self.job_id:
            self.master.after_cancel(self.job_id)
            self.job_id = None

        next_paragraph_index = -1
        for i, start_index in enumerate(self.paragraph_start_indices):
            if self.indice_palavra_atual < start_index:
                next_paragraph_index = i
                break
        
        if next_paragraph_index != -1:
            self.indice_palavra_atual = self.paragraph_start_indices[next_paragraph_index]
        else:
            self.indice_palavra_atual = len(self.palavras) - 1
            if self.indice_palavra_atual < 0: self.indice_palavra_atual = 0

        self.atualizar_exibicao_palavra_sem_avancar()
        self.btn_iniciar_pausar.config(text="Continuar")

    def atualizar_exibicao_palavra_sem_avancar(self):
        """Atualiza o label com a palavra atual no índice atual, sem avançar o índice."""
        if self.indice_palavra_atual < len(self.palavras):
            self.palavra_label.config(text=self.palavras[self.indice_palavra_atual])
        else:
            self.indice_palavra_atual = len(self.palavras) - 1 
            if self.indice_palavra_atual < 0:
                self.palavra_label.config(text="Fim da leitura!")
                self.indice_palavra_atual = 0
            else:
                self.palavra_label.config(text=self.palavras[self.indice_palavra_atual])

        self.atualizar_progresso()

    # --- MÉTODOS DE CUSTOMIZAÇÃO VISUAL ---
    def aplicar_estilo_fonte(self):
        """Aplica a fonte, tamanho e cor ao label da palavra."""
        # A verificação 'hasattr' garante que o widget já existe antes de tentar configurá-lo
        if hasattr(self, 'palavra_label'): 
            self.palavra_label.config(font=(self.nome_fonte_atual, self.tamanho_fonte_atual, "bold"),
                                      fg=self.cor_texto_atual,
                                      bg=self.cor_fundo_atual)

    def mudar_cor_texto(self):
        cor_selecionada = colorchooser.askcolor(title="Escolha a Cor do Texto", initialcolor=self.cor_texto_atual)
        if cor_selecionada[1]:
            self.cor_texto_atual = cor_selecionada[1]
            self.aplicar_estilo_fonte()

    def mudar_cor_fundo(self):
        cor_selecionada = colorchooser.askcolor(title="Escolha a Cor de Fundo", initialcolor=self.cor_fundo_atual)
        if cor_selecionada[1]:
            self.cor_fundo_atual = cor_selecionada[1]
            self.aplicar_estilo_fonte()

    def mudar_tamanho_fonte(self):
        novo_tamanho = simpledialog.askinteger("Tamanho da Fonte", "Digite o novo tamanho da fonte:",
                                              initialvalue=self.tamanho_fonte_atual, minvalue=10, maxvalue=100)
        if novo_tamanho is not None:
            self.tamanho_fonte_atual = novo_tamanho
            self.aplicar_estilo_fonte()

    def mudar_nome_fonte(self):
        novo_nome = simpledialog.askstring("Nome da Fonte", "Digite o novo nome da fonte (ex: Arial, Times New Roman, Courier New):",
                                           initialvalue=self.nome_fonte_atual)
        if novo_nome:
            self.nome_fonte_atual = novo_nome
            self.aplicar_estilo_fonte()

    # --- MÉTODOS DE SALVAR/CARREGAR PROGRESSO ---
    def salvar_progresso(self):
        if not self.caminho_arquivo_atual:
            messagebox.showwarning("Sem Arquivo", "Nenhum arquivo está carregado para salvar o progresso.")
            return

        nome_do_livro = os.path.splitext(os.path.basename(self.caminho_arquivo_atual))[0]
        data_atual = datetime.now().strftime("%Y-%m-%d")
        
        nome_arquivo_progresso = f"{nome_do_livro}_{data_atual}.json"
        caminho_completo_salvar = os.path.join(self.saves_dir, nome_arquivo_progresso)

        dados_progresso = {
            "caminho_arquivo": self.caminho_arquivo_atual,
            "indice_palavra": self.indice_palavra_atual
        }
        try:
            with open(caminho_completo_salvar, 'w', encoding='utf-8') as f:
                json.dump(dados_progresso, f, indent=4)
            messagebox.showinfo("Progresso Salvo", f"Progresso salvo com sucesso em:\n{caminho_completo_salvar}")
        except Exception as e:
            messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar o progresso:\n{e}")

    def carregar_progresso(self):
        caminho_carregar = filedialog.askopenfilename(
            initialdir=self.saves_dir,
            filetypes=[("Arquivos de Progresso JSON", "*.json")],
            title="Carregar Progresso da Leitura"
        )
        if caminho_carregar:
            try:
                with open(caminho_carregar, 'r', encoding='utf-8') as f:
                    dados_progresso = json.load(f)
                
                caminho_arquivo_salvo = dados_progresso.get("caminho_arquivo")
                indice_palavra_salvo = dados_progresso.get("indice_palavra", 0)

                if not caminho_arquivo_salvo:
                    messagebox.showwarning("Erro de Progresso", "O arquivo de progresso não contém o caminho do arquivo original.")
                    return
                
                if not os.path.exists(caminho_arquivo_salvo):
                    messagebox.showwarning("Arquivo Original Não Encontrado", 
                                          f"O arquivo original '{os.path.basename(caminho_arquivo_salvo)}' não foi encontrado no caminho salvo.\n"
                                          "Por favor, certifique-se de que o arquivo não foi movido ou renomeado.")
                    resposta = messagebox.askyesno("Localizar Arquivo?", "Deseja tentar localizar o arquivo original agora?")
                    if resposta:
                        novo_caminho_original = filedialog.askopenfilename(
                            title=f"Localizar '{os.path.basename(caminho_arquivo_salvo)}'",
                            filetypes=[("Documentos Word", "*.docx"), ("Arquivos de Texto", "*.txt"), ("Arquivos PDF", "*.pdf")]
                        )
                        if novo_caminho_original:
                            caminho_arquivo_salvo = novo_caminho_original
                        else:
                            messagebox.showinfo("Cancelado", "Operação de carregamento de progresso cancelada.")
                            return
                    else:
                        messagebox.showinfo("Cancelado", "Operação de carregamento de progresso cancelada.")
                        return

                self.carregar_arquivo(caminho_predefinido=caminho_arquivo_salvo, indice_predefinido=indice_palavra_salvo)
                messagebox.showinfo("Progresso Carregado", "Progresso carregado com sucesso!")

            except FileNotFoundError:
                messagebox.showerror("Erro ao Carregar", "Arquivo de progresso não encontrado.")
            except json.JSONDecodeError:
                messagebox.showerror("Erro ao Carregar", "Arquivo de progresso inválido (não é um JSON válido).")
            except Exception as e:
                messagebox.showerror("Erro ao Carregar", f"Não foi possível carregar o progresso:\n{e}")

    # --- MÉTODOS DE CONFIGURAÇÕES PERSISTENTES ---
    def salvar_configuracoes(self):
        """Salva as configurações atuais (velocidade, cores, fonte) em um arquivo JSON."""
        config_data = {
            "velocidade_leitura": self.velocidade_leitura_atual,
            "cor_texto": self.cor_texto_atual,
            "cor_fundo": self.cor_fundo_atual,
            "tamanho_fonte": self.tamanho_fonte_atual,
            "nome_fonte": self.nome_fonte_atual
        }
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4)
        except Exception as e:
            print(f"Erro ao salvar configurações: {e}")

    def carregar_configuracoes(self):
        """Carrega as configurações de um arquivo JSON, se existir."""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                self.velocidade_leitura_atual = config_data.get("velocidade_leitura", 300)
                self.cor_texto_atual = config_data.get("cor_texto", "blue")
                self.cor_fundo_atual = config_data.get("cor_fundo", "white")
                self.tamanho_fonte_atual = config_data.get("tamanho_fonte", 48)
                self.nome_fonte_atual = config_data.get("nome_fonte", "Arial")

                if hasattr(self, 'velocidade_scale'):
                    self.velocidade_scale.set(self.velocidade_leitura_atual)
                if hasattr(self, 'velocidade_label'):
                    self.velocidade_label.config(text=f"Velocidade (PPM): {self.velocidade_leitura_atual}")

            except Exception as e:
                print(f"Erro ao carregar configurações: {e}")
        
    def on_closing(self):
        """Método chamado ao fechar a janela para salvar as configurações."""
        self.salvar_configuracoes()
        self.master.destroy()


# --- Inicializa a Aplicação Tkinter ---
if __name__ == "__main__":
    root = tk.Tk()
    app = LeitorRapidoApp(root)
    root.mainloop()