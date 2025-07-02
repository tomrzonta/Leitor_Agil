import time
from docx import Document # Importa a classe Document da biblioteca python-docx

def ler_texto_de_docx(caminho_do_arquivo):
    """Lê o texto de um arquivo .docx."""
    try:
        # Usa o caminho completo recebido como parâmetro
        doc = Document(caminho_do_arquivo)
        full_text = []
        for paragraph in doc.paragraphs:
            full_text.append(paragraph.text)
        return '\n'.join(full_text)
    except Exception as e:
        print(f"Erro ao ler DOCX: {e}")
        return None

def ler_texto_de_txt(caminho_do_arquivo):
    """Lê o texto de um arquivo .txt."""
    try:
        # Usa o caminho completo recebido como parâmetro
        with open(caminho_do_arquivo, 'r', encoding='utf-8') as arquivo:
            return arquivo.read()
    except Exception as e:
        print(f"Erro ao ler TXT: {e}")
        return None

def ler_e_exibir_palavras(caminho_do_arquivo, tempo_por_palavra_segundos=0.2):
    """
    Lê um arquivo (TXT ou DOCX) e exibe cada palavra individualmente.

    Args:
        caminho_do_arquivo (str): O caminho COMPLETO para o arquivo de texto ou DOCX.
        tempo_por_palavra_segundos (float): O tempo (em segundos) que cada palavra será exibida.
    """
    conteudo = None
    # Verifica a extensão do arquivo para chamar a função de leitura correta
    if caminho_do_arquivo.endswith('.docx'):
        conteudo = ler_texto_de_docx(caminho_do_arquivo)
    elif caminho_do_arquivo.endswith('.txt'):
        conteudo = ler_texto_de_txt(caminho_do_arquivo)
    else:
        print("Erro: Formato de arquivo não suportado. Use .txt ou .docx.")
        return

    # Se houve algum erro na leitura do arquivo, a função retorna e não continua
    if conteudo is None:
        return

    # Limpeza e divisão do texto
    # Esta parte remove quebras de linha, pontos e vírgulas e divide por espaços
    palavras = conteudo.replace('\n', ' ').replace('.', '').replace(',', '').split(' ')

    for palavra in palavras:
        palavra_limpa = palavra.strip() # Remove espaços extras no início/fim da palavra
        if palavra_limpa: # Verifica se a palavra não está vazia após a limpeza
            print(palavra_limpa)
            time.sleep(tempo_por_palavra_segundos) # Pausa para controlar a velocidade

# --- Como usar a função ---
if __name__ == "__main__":
    print("Iniciando leitura a 300 PPM:")

    # CAMINHO DO SEU ARQUIVO INCLUÍDO AQUI.
    # CERTIFIQUE-SE DE QUE ESTE CAMINHO ESTÁ CORRETO NO SEU COMPUTADOR.
    # Use barras duplas (\\) ou barras normais (/) para separar as pastas.
    caminho_do_arquivo_completo = 'C:\\Users\\Pichau\\Desktop\\Projeto_Python_Leitor_de_Texto\\Projeto_Leitor_Texto\\O_Senhor_dos_Aneis_Completo.docx'

    ler_e_exibir_palavras(caminho_do_arquivo_completo, tempo_por_palavra_segundos=0.2)