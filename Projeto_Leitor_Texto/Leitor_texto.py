import time

def ler_e_exibir_palavras(nome_do_arquivo, tempo_por_palavra_segundos=0.5):
    """
    Lê um arquivo de texto e exibe cada palavra individualmente.

    Args:
        nome_do_arquivo (str): O caminho para o arquivo de texto.
        tempo_por_palavra_segundos (float): O tempo (em segundos) que cada palavra será exibida.
    """
    try:
        with open(nome_do_arquivo, 'r', encoding='utf-8') as arquivo:
            conteudo = arquivo.read(O_Senhor_dos_Aneis_Completo.docx)
            # Substitui quebras de linha e pontuações comuns por espaços
            # e divide o texto em palavras.
            # Convertemos tudo para minúsculas para simplificar, mas isso é opcional.
            palavras = conteudo.replace('\n', ' ').replace('.', '').replace(',', '').split(' ')

            for palavra in palavras:
                palavra_limpa = palavra.strip() # Remove espaços extras nas pontas
                if palavra_limpa: # Verifica se a palavra não está vazia (depois de limpar)
                    print(palavra_limpa)
                    time.sleep(tempo_por_palavra_segundos) # Pausa o programa pelo tempo definido
    except FileNotFoundError:
        print(f"Erro: O arquivo '{nome_do_arquivo}' não foi encontrado.")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")

# --- Como usar a função ---
# 1. Crie um arquivo de texto (ex: meu_texto.txt) na mesma pasta do seu código Python.
# 2. Adicione algum texto dentro dele.
# 3. Chame a função abaixo:

if __name__ == "__main__":
    # Exemplo de uso, mostrando cada palavra por 0.5 segundos
    ler_e_exibir_palavras('O_Senhor_dos_Aneis_Completo.docx', tempo_por_palavra_segundos=0.5)

    # Para 300 palavras por minuto (PPM):
    # 60 segundos / 300 palavras = 0.2 segundos por palavra
    print("\nIniciando leitura a 300 PPM:")
    ler_e_exibir_palavras('O_Senhor_dos_Aneis_Completo.docx', tempo_por_palavra_segundos=0.2)
