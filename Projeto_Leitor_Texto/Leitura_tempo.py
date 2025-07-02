import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser, simpledialog
import time
import re
from docx import Document
import json
import os
from datetime import datetime
import PyPDF2 

# --- Novas importações para OCR ---
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import sys # Importar sys para verificar se está rodando como executável

# --- CONFIGURAÇÃO DO TESSERACT OCR ---
# ATENÇÃO: Ajuste este caminho se o Tesseract OCR estiver instalado em outro local no seu computador.
TESSERACT_CMD_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe' 
if os.path.exists(TESSERACT_CMD_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD_PATH
else:
    print(f"AVISO: Tesseract OCR não encontrado no caminho configurado: {TESSERACT_CMD_PATH}")
    print("O OCR para PDFs com imagens pode não funcionar. Instale o Tesseract e ajuste o caminho se necessário.")


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
    """Lê o texto de um arquivo .pdf, usando OCR para imagens se necessário, e retorna o texto completo como UMA ÚNICA STRING."""
    full_text_extracted = ""
    
    try:
        with open(caminho_do_arquivo, 'rb') as arquivo_pdf:
            reader = PyPDF2.PdfReader(arquivo_pdf)
            num_pages = len(reader.pages)
            
            for i in range(num_pages):
                page = reader.pages[i]
                page_text = page.extract_text()
                
                # Se o texto extraído for muito curto, tenta OCR
                if not page_text or len(page_text.strip()) < 50: 
                    try:
                        if not os.path.exists(TESSERACT_CMD_PATH):
                            messagebox.showwarning("Tesseract Não Configurado", 
                                                   "Caminho do Tesseract OCR não configurado ou inválido. O OCR pode falhar. \n"
                                                   "Verifique 'TESSERACT_CMD_PATH' no código.")
                            full_text_extracted += page_text + "\n\n" # Adiciona o que conseguiu e continua
                            continue 
                            
                        # Converte a página para imagem e aplica OCR
                        images = convert_from_path(caminho_do_arquivo, first_page=i+1, last_page=i+1, dpi=300) 
                        
                        if images:
                            ocr_text = pytesseract.image_to_string(images[0], lang='por+eng') # Tenta português e inglês
                            full_text_extracted += ocr_text + "\n\n"
                        else:
                            # Se não conseguiu imagem, adiciona o que tinha de texto (mesmo que pouco)
                            full_text_extracted += page_text + "\n\n"
                    except pytesseract.TesseractNotFoundError:
                           messagebox.showerror("Erro Tesseract OCR", 
                                 f"Tesseract OCR não encontrado.\n"
                                 f"Por favor, instale o Tesseract OCR e/ou configure o caminho em 'TESSERACT_CMD_PATH' no código:\n'{TESSERACT_CMD_PATH}'")
                           return None # Aborta se Tesseract não for encontrado para OCR
                    except Exception as ocr_e:
                        print(f"Aviso: Erro ao tentar OCR na página {i+1}: {ocr_e}")
                        full_text_extracted += page_text + "\n\n" # Em caso de outro erro OCR, usa o texto extraído
                else:
                    full_text_extracted += page_text + "\n\n" # Usa o texto extraído se for suficiente
        
        return full_text_extracted

    except FileNotFoundError:
        messagebox.showerror("Erro de Arquivo", f"O arquivo PDF não foi encontrado:\n{caminho_do_arquivo}")
        return None
    except Exception as e:
        messagebox.showerror("Erro ao Ler PDF", f"Não foi possível ler o arquivo PDF ou processar OCR:\n{e}")
        return None

# --- Lógica Principal da Aplicação com Tkinter ---

class LeitorRapidoApp:
    def __init__(self, master):
        self.master = master
        master.title("Leitor Rápido de Texto")
        master.geometry("1000x650") # Ajustado para acomodar mais botões

        self.texto_completo_paragrafos = [] # Não mais usado diretamente, mas mantido para contexto
        self.palavras = []
        self.indice_palavra_atual = 0
        self.esta_lendo = False
        self.job_id = None
        self.paragraph_start_indices = [] # Índices onde parágrafos "recomeçam"
        self.caminho_arquivo_atual = None # Armazena o caminho do arquivo carregado

        # --- AJUSTE AQUI: DEFINIÇÃO DOS DIRETÓRIOS DE SALVAMENTO ---
        # Determina o diretório base para salvar arquivos de forma persistente
        if getattr(sys, 'frozen', False):
            # Se o programa está rodando como um executável empacotado (PyInstaller)
            # Usa o diretório de dados do aplicativo do usuário para garantir persistência e permissões
            # Ex: C:\Users\SeuUsuario\AppData\Local\LeitorRapidoDeTexto
            app_data_path = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'LeitorRapidoDeTexto')
            self.base_data_dir = app_data_path
        else:
            # Se está rodando como script Python normal
            # Usa o diretório do script para facilidade de desenvolvimento
            self.base_data_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.saves_dir = os.path.join(self.base_data_dir, "progress_saves")
        self.config_dir = os.path.join(self.base_data_dir, "config")
        self.settings_file = os.path.join(self.config_dir, "settings.json")

        # Garante que os diretórios existam
        os.makedirs(self.saves_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)

        # Configurações padrão (serão sobrescritas se houver um arquivo de configurações salvo)
        self.cor_texto_atual = "blue"
        self.cor_fundo_atual = "white"
        self.tamanho_fonte_atual = 48
        self.nome_fonte_atual = "Arial"
        self.velocidade_leitura_atual = 300
        
        # Variáveis para a aceleração gradual
        self.velocidade_inicial_aceleracao = 100
        self.passo_aceleracao = 25
        self.velocidade_leitura_atual_temp = 0 # Velocidade temporária para aceleração

        # Carrega as configurações salvas no início do programa
        self.carregar_configuracoes()

        # --- Componentes da Interface ---
        self.palavra_label = tk.Label(master, text="Carregue um arquivo para começar.",
                                       font=(self.nome_fonte_atual, self.tamanho_fonte_atual, "bold"),
                                       fg=self.cor_texto_atual, bg=self.cor_fundo_atual)
        self.palavra_label.pack(pady=30, fill=tk.BOTH, expand=True)

        # Frame principal para organizar os controles
        self.main_controls_frame = tk.Frame(master)
        self.main_controls_frame.pack(pady=10)

        # Frame para botões básicos de controle
        self.basic_buttons_frame = tk.Frame(self.main_controls_frame)
        self.basic_buttons_frame.pack(side=tk.TOP, pady=5)

        self.btn_carregar = tk.Button(self.basic_buttons_frame, text="Carregar Arquivo", command=self.carregar_arquivo)
        self.btn_carregar.pack(side=tk.LEFT, padx=5)

        self.btn_iniciar_pausar = tk.Button(self.basic_buttons_frame, text="Iniciar", command=self.iniciar_pausar_leitura, state=tk.DISABLED)
        self.btn_iniciar_pausar.pack(side=tk.LEFT, padx=5)

        self.btn_resetar = tk.Button(self.basic_buttons_frame, text="Resetar", command=self.resetar_leitura, state=tk.DISABLED)
        self.btn_resetar.pack(side=tk.LEFT, padx=5)

        # Frame para botões de navegação
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

        # Frame para o controle de velocidade
        self.speed_frame = tk.Frame(self.main_controls_frame)
        self.speed_frame.pack(side=tk.TOP, pady=5)

        self.velocidade_label = tk.Label(self.speed_frame, text=f"Velocidade (PPM): {self.velocidade_leitura_atual}")
        self.velocidade_label.pack(side=tk.LEFT, padx=10)

        self.velocidade_scale = tk.Scale(self.speed_frame, from_=100, to=1000, orient=tk.HORIZONTAL,
                                         length=200, command=self.atualizar_velocidade_label, resolution=50)
        self.velocidade_scale.set(self.velocidade_leitura_atual) # Define a velocidade inicial carregada
        self.velocidade_scale.pack(side=tk.LEFT, padx=5)

        # Frame para o progresso da leitura
        self.frame_progresso = tk.Frame(master)
        self.frame_progresso.pack(pady=10)

        self.progresso_label = tk.Label(self.frame_progresso, text="Progresso: 0/0 palavras")
        self.progresso_label.pack(side=tk.LEFT, padx=5)
        
        # NOVO: Label para o tempo estimado de leitura
        self.tempo_estimado_label = tk.Label(self.frame_progresso, text="Tempo Restante: 00:00:00") # Formato inicial HH:MM:SS
        self.tempo_estimado_label.pack(side=tk.LEFT, padx=15)

        # Frame para botões de customização visual
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

        # Frame para botões de salvar/carregar progresso
        self.progress_controls_frame = tk.Frame(master)
        self.progress_controls_frame.pack(pady=10)

        self.btn_salvar_progresso = tk.Button(self.progress_controls_frame, text="Salvar Progresso", command=self.salvar_progresso, state=tk.DISABLED)
        self.btn_salvar_progresso.pack(side=tk.LEFT, padx=5)

        self.btn_carregar_progresso = tk.Button(self.progress_controls_frame, text="Carregar Progresso", command=self.carregar_progresso)
        self.btn_carregar_progresso.pack(side=tk.LEFT, padx=5)

        # Aplica o estilo de fonte carregado
        self.aplicar_estilo_fonte()

        # Garante que as configurações sejam salvas ao fechar a janela
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)


    # --- Métodos da Classe ---
    def atualizar_velocidade_label(self, val):
        # Atualiza a velocidade de leitura alvo
        self.velocidade_leitura_atual = int(float(val))
        self.velocidade_label.config(text=f"Velocidade (PPM): {self.velocidade_leitura_atual}")
        # Reinicia a velocidade temporária para a aceleração, se a leitura estiver pausada ou recém iniciada
        if not self.esta_lendo:
            self.velocidade_leitura_atual_temp = self.velocidade_inicial_aceleracao
            if self.velocidade_leitura_atual_temp > self.velocidade_leitura_atual:
                self.velocidade_leitura_atual_temp = self.velocidade_leitura_atual
        self.atualizar_tempo_estimado() # Atualiza o tempo estimado ao mudar a velocidade


    def carregar_arquivo(self, caminho_predefinido=None, indice_predefinido=0):
        # Reseta o estado atual da leitura
        self.resetar_leitura() 
        
        caminho_arquivo = caminho_predefinido
        if not caminho_arquivo: # Se não houver um caminho predefinido (ex: vindo de um salvamento)
            caminho_arquivo = filedialog.askopenfilename(
                filetypes=[
                    ("Documentos Word", "*.docx"),
                    ("Arquivos de Texto", "*.txt"),
                    ("Arquivos PDF", "*.pdf"), # Adicionado suporte a PDF
                    ("Todos os Arquivos", "*.*")
                ]
            )
        
        if caminho_arquivo:
            self.habilitar_botoes(False) # Desabilita botões temporariamente
            self.caminho_arquivo_atual = caminho_arquivo # Salva o caminho do arquivo carregado

            texto_bruto_extraido = "" 
            if caminho_arquivo.lower().endswith('.docx'):
                paragrafos_extraidos = ler_texto_de_docx(caminho_arquivo)
                if paragrafos_extraidos:
                    texto_bruto_extraido = "\n\n".join(paragrafos_extraidos)
            elif caminho_arquivo.lower().endswith('.txt'):
                paragrafos_extraidos = ler_texto_de_txt(caminho_arquivo)
                if paragrafos_extraidos:
                    texto_bruto_extraido = "\n\n".join(paragrafos_extraidos)
            elif caminho_arquivo.lower().endswith('.pdf'):
                # ler_texto_de_pdf já retorna uma única string bruta
                texto_bruto_extraido = ler_texto_de_pdf(caminho_arquivo) 
            else:
                messagebox.showwarning("Formato Não Suportado", "Por favor, selecione um arquivo .txt, .docx ou .pdf.")
                self.palavra_label.config(text="Formato não suportado!")
                self.habilitar_botoes(False)
                self.caminho_arquivo_atual = None
                return
            
            if texto_bruto_extraido:
                # --- PRÉ-PROCESSAMENTO ROBUSTO PARA CORRIGIR SEPARAÇÃO DE PALAVRAS E LIMPAR ---
                
                # 1. Trata hifens de quebra de linha: "palavra-\ncontinua" -> "palavracontinua"
                # Garante que só junte se realmente for uma palavra hifenizada.
                processed_text = re.sub(r'(\w+)-\s*?\n*\s*?(\w+)', r'\1\2', texto_bruto_extraido)
                
                # 2. Substitui TODAS as quebras de linha por um único espaço
                processed_text = processed_text.replace('\n', ' ')
                
                # 3. Normaliza múltiplos espaços, quebras de linha (já tratadas acima, mas para segurança) e espaços do início/fim
                processed_text = re.sub(r'\s+', ' ', processed_text).strip()
                
                # 4. Remove referências de rodapé como "[1]", "[2]" etc., que podem vir de OCR de PDFs
                processed_text = re.sub(r'\[\d+\]', '', processed_text)
                
                # A regex final para dividir em palavras (\S+) mantém a pontuação anexada.
                self.palavras = re.findall(r'\S+', processed_text) 
                
                # Reconstruindo paragraph_start_indices com uma heurística após a limpeza agressiva:
                self.paragraph_start_indices = [0] # O primeiro parágrafo começa no índice 0
                for i, palavra in enumerate(self.palavras):
                    # Identifica possíveis fins de frase/parágrafo
                    # Evita que "Dr." ou "U.S." sejam considerados fim de parágrafo
                    if re.search(r'[.!?]$', palavra) and \
                       not re.match(r'^[A-Z]\.$', palavra) and \
                       not re.match(r'^\d+\.$', palavra): # Evita "1." como fim de parágrafo
                        if i + 1 < len(self.palavras): # Garante que não é a última palavra
                            self.paragraph_start_indices.append(i + 1)
                
                # Garante que os índices de parágrafo sejam únicos e em ordem.
                self.paragraph_start_indices = sorted(list(set(self.paragraph_start_indices)))
                # Remove o último índice se ele for redundante (aponta para o final do documento ou após a última palavra)
                if self.paragraph_start_indices and self.paragraph_start_indices[-1] >= len(self.palavras) - 1:
                    if len(self.paragraph_start_indices) > 1: # Só remove se houver mais de um parágrafo
                        self.paragraph_start_indices.pop()
                    # Se só tem [0] e o texto é curto, mantém [0]


                if not self.palavras:
                    messagebox.showwarning("Arquivo Vazio", "O arquivo selecionado não contém texto válido.")
                    self.palavra_label.config(text="Arquivo vazio ou sem texto válido.")
                    self.habilitar_botoes(False)
                    self.caminho_arquivo_atual = None
                    return

                # Define o índice de palavra atual (pode ser carregado de um salvamento)
                self.indice_palavra_atual = min(indice_predefinido, len(self.palavras) - 1)
                if self.indice_palavra_atual < 0: self.indice_palavra_atual = 0 # Garante que não seja negativo

                self.atualizar_exibicao_palavra_sem_avancar() # Exibe a palavra sem iniciar a leitura
                self.btn_iniciar_pausar.config(text="Iniciar")
                self.esta_lendo = False
                self.habilitar_botoes(True) # Habilita todos os botões após carregar
                self.atualizar_progresso()
                self.atualizar_tempo_estimado() # NOVO: Atualiza o tempo estimado ao carregar um arquivo
                self.btn_salvar_progresso.config(state=tk.NORMAL) # Habilita salvar progresso
            else:
                messagebox.showwarning("Arquivo Vazio", "O arquivo selecionado não contém texto válido.")
                self.palavra_label.config(text="Erro ao carregar o arquivo ou arquivo vazio.")
                self.habilitar_botoes(False)
                self.caminho_arquivo_atual = None
        else: # Se o usuário cancelou a seleção do arquivo
            self.habilitar_botoes(False) # Apenas carregar e carregar progresso ficam ativos
            self.btn_carregar.config(state=tk.NORMAL)
            self.btn_carregar_progresso.config(state=tk.NORMAL)
            if self.palavras: # Se já havia um texto carregado antes de cancelar, mantém os botões ativos para ele
                self.habilitar_botoes(True)
                self.btn_iniciar_pausar.config(text="Iniciar")
                self.btn_salvar_progresso.config(state=tk.NORMAL)


    def atualizar_exibicao_palavra(self):
        """Atualiza a palavra exibida e avança o índice, com aceleração gradual."""
        if self.indice_palavra_atual < len(self.palavras):
            self.palavra_label.config(text=self.palavras[self.indice_palavra_atual])
            self.indice_palavra_atual += 1
            self.atualizar_progresso()
            self.atualizar_tempo_estimado() # NOVO: Atualiza o tempo estimado a cada palavra

            ppm_alvo = self.velocidade_scale.get() # Velocidade alvo definida pelo usuário
            
            # Lógica de aceleração gradual
            if self.velocidade_leitura_atual_temp < ppm_alvo:
                self.velocidade_leitura_atual_temp += self.passo_aceleracao
                if self.velocidade_leitura_atual_temp > ppm_alvo: # Não ultrapassa a velocidade alvo
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
            self.atualizar_tempo_estimado() # NOVO: Atualiza para '--:--' ou 0:00 ao finalizar


    def iniciar_pausar_leitura(self):
        if not self.palavras:
            messagebox.showwarning("Nenhum Texto", "Por favor, carregue um arquivo antes de iniciar a leitura.")
            return

        if self.esta_lendo:
            self.esta_lendo = False
            self.btn_iniciar_pausar.config(text="Continuar")
            if self.job_id:
                self.master.after_cancel(self.job_id)
            self.atualizar_tempo_estimado() # NOVO: Atualiza o tempo estimado ao pausar
        else:
            self.esta_lendo = True
            self.btn_iniciar_pausar.config(text="Pausar")
            if self.indice_palavra_atual >= len(self.palavras): # Se chegou ao fim, reinicia do começo
                self.indice_palavra_atual = 0
                self.atualizar_progresso()
            
            # Reinicia a velocidade temporária para o início da aceleração
            self.velocidade_leitura_atual_temp = self.velocidade_inicial_aceleracao
            if self.velocidade_leitura_atual_temp > self.velocidade_scale.get(): # Garante que não comece acima do alvo
                self.velocidade_leitura_atual_temp = self.velocidade_scale.get()

            self.atualizar_exibicao_palavra()
            self.atualizar_tempo_estimado() # NOVO: Atualiza o tempo estimado ao iniciar

    def resetar_leitura(self):
        self.esta_lendo = False
        self.indice_palavra_atual = 0
        if self.job_id:
            self.master.after_cancel(self.job_id)
            self.job_id = None
        
        self.velocidade_leitura_atual_temp = self.velocidade_scale.get() # Reseta a velocidade temp para a velocidade alvo

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
        self.atualizar_tempo_estimado() # NOVO: Atualiza o tempo estimado ao resetar
        self.btn_carregar.config(state=tk.NORMAL)
        self.btn_salvar_progresso.config(state=tk.DISABLED) # Desabilita salvar se não tem texto
        self.btn_carregar_progresso.config(state=tk.NORMAL) # Sempre habilitado para carregar outro

    def atualizar_progresso(self):
        total_palavras = len(self.palavras)
        palavras_lidas = min(self.indice_palavra_atual, total_palavras)
        self.progresso_label.config(text=f"Progresso: {palavras_lidas}/{total_palavras} palavras")
    
    def habilitar_botoes(self, habilitar):
        # Botões que sempre ficam ativos
        self.btn_carregar.config(state=tk.NORMAL) 
        self.btn_carregar_progresso.config(state=tk.NORMAL)

        # Botões que dependem de um arquivo carregado
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
        self.esta_lendo = False # Pausa a leitura automática
        if self.job_id:
            self.master.after_cancel(self.job_id)
            self.job_id = None
        
        self.indice_palavra_atual = max(0, self.indice_palavra_atual - 10) # Volta 10 palavras, mínimo 0
        self.atualizar_exibicao_palavra_sem_avancar() # Atualiza a exibição na nova posição
        self.btn_iniciar_pausar.config(text="Continuar") # Muda o texto do botão
        self.atualizar_tempo_estimado() # NOVO: Atualiza o tempo estimado ao navegar

    def voltar_paragrafo(self):
        if not self.palavras or not self.paragraph_start_indices: return
        self.esta_lendo = False # Pausa a leitura automática
        if self.job_id:
            self.master.after_cancel(self.job_id)
            self.job_id = None

        current_paragraph_index = 0
        # Encontra o índice do parágrafo atual na lista de inícios de parágrafo
        for i, start_index in enumerate(self.paragraph_start_indices):
            if self.indice_palavra_atual > start_index: # Se a palavra atual está além do início deste parágrafo
                current_paragraph_index = i
            else: # Se a palavra atual é anterior ou igual ao início deste parágrafo
                break
        
        # Decide para onde voltar
        if self.indice_palavra_atual == self.paragraph_start_indices[current_paragraph_index]:
            # Se já estamos no início de um parágrafo (ou na primeira palavra de fato), vai para o início do parágrafo anterior
            if current_paragraph_index > 0:
                self.indice_palavra_atual = self.paragraph_start_indices[current_paragraph_index - 1]
            else: # Já está no primeiro parágrafo, vai para o início absoluto
                self.indice_palavra_atual = 0
        else:
            # Se estamos no meio de um parágrafo, volta para o início desse mesmo parágrafo
            self.indice_palavra_atual = self.paragraph_start_indices[current_paragraph_index]


        self.atualizar_exibicao_palavra_sem_avancar()
        self.btn_iniciar_pausar.config(text="Continuar")
        self.atualizar_tempo_estimado() # NOVO: Atualiza o tempo estimado ao navegar

    # --- Funções de Navegação (Avançar) ---
    def avancar_10_palavras(self):
        if not self.palavras: return
        self.esta_lendo = False
        if self.job_id:
            self.master.after_cancel(self.job_id)
            self.job_id = None
        
        # Avança 10 palavras, máximo o fim do texto
        self.indice_palavra_atual = min(len(self.palavras), self.indice_palavra_atual + 10)
        self.atualizar_exibicao_palavra_sem_avancar()
        self.btn_iniciar_pausar.config(text="Continuar")
        self.atualizar_tempo_estimado() # NOVO: Atualiza o tempo estimado ao navegar

    def avancar_paragrafo(self):
        if not self.palavras or not self.paragraph_start_indices: return
        self.esta_lendo = False
        if self.job_id:
            self.master.after_cancel(self.job_id)
            self.job_id = None

        next_paragraph_index = -1
        # Encontra o índice do próximo parágrafo
        for i, start_index in enumerate(self.paragraph_start_indices):
            if self.indice_palavra_atual < start_index: # Se a palavra atual é anterior ao início deste parágrafo
                next_paragraph_index = i
                break
        
        if next_paragraph_index != -1:
            # Vai para o início do próximo parágrafo
            self.indice_palavra_atual = self.paragraph_start_indices[next_paragraph_index]
        else:
            # Se já estamos no último parágrafo ou após ele, vai para o fim do texto
            self.indice_palavra_atual = len(self.palavras) - 1
            if self.indice_palavra_atual < 0: self.indice_palavra_atual = 0 # Garante não ser negativo

        self.atualizar_exibicao_palavra_sem_avancar()
        self.btn_iniciar_pausar.config(text="Continuar")
        self.atualizar_tempo_estimado() # NOVO: Atualiza o tempo estimado ao navegar

    def atualizar_exibicao_palavra_sem_avancar(self):
        """Atualiza o label com a palavra atual no índice atual, sem avançar o índice."""
        if self.indice_palavra_atual < len(self.palavras):
            self.palavra_label.config(text=self.palavras[self.indice_palavra_atual])
        else:
            # Se o índice for para o final ou além, mostra a última palavra ou mensagem de fim
            if self.palavras:
                self.palavra_label.config(text=self.palavras[-1])
                self.indice_palavra_atual = len(self.palavras) - 1
            else:
                self.palavra_label.config(text="Fim da leitura!")
                self.indice_palavra_atual = 0 # Garante que o índice esteja no fim ou 0 se lista vazia

        self.atualizar_progresso()
        self.atualizar_tempo_estimado() # NOVO: Atualiza o tempo estimado ao exibir palavra sem avançar

    # --- MÉTODOS DE CUSTOMIZAÇÃO VISUAL ---
    def aplicar_estilo_fonte(self):
        """Aplica a fonte, tamanho e cor ao label da palavra."""
        # 'hasattr' garante que o label já foi criado antes de tentar configurá-lo
        if hasattr(self, 'palavra_label'): 
            self.palavra_label.config(font=(self.nome_fonte_atual, self.tamanho_fonte_atual, "bold"),
                                       fg=self.cor_texto_atual,
                                       bg=self.cor_fundo_atual)

    def mudar_cor_texto(self):
        cor_selecionada = colorchooser.askcolor(title="Escolha a Cor do Texto", initialcolor=self.cor_texto_atual)
        if cor_selecionada[1]: # cor_selecionada[1] contém o código hexadecimal da cor
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
        if novo_nome: # Verifica se o usuário digitou algo
            self.nome_fonte_atual = novo_nome
            self.aplicar_estilo_fonte()

    # --- MÉTODOS DE SALVAR/CARREGAR PROGRESSO ---
    def salvar_progresso(self):
        if not self.caminho_arquivo_atual:
            messagebox.showwarning("Sem Arquivo", "Nenhum arquivo está carregado para salvar o progresso.")
            return

        # Gera um nome de arquivo para o progresso baseado no nome do arquivo original e data
        nome_do_livro = os.path.splitext(os.path.basename(self.caminho_arquivo_atual))[0]
        data_atual = datetime.now().strftime("%Y-%m-%d_%H%M%S") # Adiciona hora para unicidade
        
        nome_arquivo_progresso = f"{nome_do_livro}_{data_atual}.json"
        caminho_completo_salvar = os.path.join(self.saves_dir, nome_arquivo_progresso)

        dados_progresso = {
            "caminho_arquivo": self.caminho_arquivo_atual,
            "indice_palavra": self.indice_palavra_atual
        }
        try:
            with open(caminho_completo_salvar, 'w', encoding='utf-8') as f:
                json.dump(dados_progresso, f, indent=4) # Salva em formato JSON legível
            messagebox.showinfo("Progresso Salvo", f"Progresso salvo com sucesso em:\n{caminho_completo_salvar}")
        except Exception as e:
            messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar o progresso:\n{e}")

    def carregar_progresso(self):
        caminho_carregar = filedialog.askopenfilename(
            initialdir=self.saves_dir, # Abre a caixa de diálogo na pasta de salvamentos
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
                
                # Verifica se o arquivo original ainda existe no caminho salvo
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
                            caminho_arquivo_salvo = novo_caminho_original # Atualiza o caminho
                        else:
                            messagebox.showinfo("Cancelado", "Operação de carregamento de progresso cancelada.")
                            return
                    else:
                        messagebox.showinfo("Cancelado", "Operação de carregamento de progresso cancelada.")
                        return

                # Carrega o arquivo original e posiciona no índice salvo
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
                
                # Tenta carregar cada configuração, usando um valor padrão se não encontrar
                self.velocidade_leitura_atual = config_data.get("velocidade_leitura", 300)
                self.cor_texto_atual = config_data.get("cor_texto", "blue")
                self.cor_fundo_atual = config_data.get("cor_fundo", "white")
                self.tamanho_fonte_atual = config_data.get("tamanho_fonte", 48)
                self.nome_fonte_atual = config_data.get("nome_fonte", "Arial")

                # Se os widgets já existirem, atualiza-os. Caso contrário, serão definidos no __init__
                if hasattr(self, 'velocidade_scale'):
                    self.velocidade_scale.set(self.velocidade_leitura_atual)
                if hasattr(self, 'velocidade_label'):
                    self.velocidade_label.config(text=f"Velocidade (PPM): {self.velocidade_leitura_atual}")

            except Exception as e:
                print(f"Erro ao carregar configurações: {e}")
        
    def on_closing(self):
        """Método chamado ao fechar a janela para salvar as configurações."""
        self.salvar_configuracoes()
        self.master.destroy() # Destrói a janela e encerra o aplicativo

    # --- NOVO: Função para calcular e atualizar o tempo estimado ---
    def atualizar_tempo_estimado(self):
        if not self.palavras or self.velocidade_leitura_atual == 0:
            self.tempo_estimado_label.config(text="Tempo Restante: --:--:--") # Formato HH:MM:SS
            return

        palavras_restantes = len(self.palavras) - self.indice_palavra_atual
        
        if palavras_restantes <= 0:
            self.tempo_estimado_label.config(text="Tempo Restante: 00:00:00")
            return

        # Calcula o tempo total em segundos
        segundos_totais = (palavras_restantes / self.velocidade_leitura_atual) * 60
        
        # Converte para horas, minutos e segundos
        horas = int(segundos_totais // 3600)
        minutos = int((segundos_totais % 3600) // 60)
        segundos = int(segundos_totais % 60)
        
        # Formata a string para HH:MM:SS com dois dígitos, preenchendo com zero à esquerda
        self.tempo_estimado_label.config(text=f"Tempo Restante: {horas:02d}:{minutos:02d}:{segundos:02d}")


# --- Inicializa a Aplicação Tkinter ---
if __name__ == "__main__":
    root = tk.Tk()
    app = LeitorRapidoApp(root)
    root.mainloop()