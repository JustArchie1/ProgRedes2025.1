import socket
import os
import hashlib

# CONFIGURAÇÕES

HOST = 'localhost'
PORT = 5000
PASTA_SALVAR = './downloads'

if not os.path.exists(PASTA_SALVAR):
    os.makedirs(PASTA_SALVAR)

# FUNÇÕES DE UTILIDADE

def receber_arquivo(sock, caminho, tamanho):
    """Recebe dados do socket até o tamanho indicado e salva no arquivo."""
    bytes_recebidos = 0
    with open(caminho, 'wb') as f:
        while bytes_recebidos < tamanho:
            dados = sock.recv(min(1024, tamanho - bytes_recebidos))
            if not dados:
                break  # conexão fechada inesperadamente
            f.write(dados)
            bytes_recebidos += len(dados)

def calcular_md5_local(caminho, tamanho):
    if not os.path.isfile(caminho):
        return None
    h = hashlib.md5()
    with open(caminho, 'rb') as f:
        dados = f.read(tamanho)
        h.update(dados)
    return h.hexdigest()

# CLIENTE PRINCIPA

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((HOST, PORT))
        print(f'Conectado ao servidor {HOST}:{PORT}\n')

        while True:
            print('''\nEscolha um comando:
1 - Listar arquivos (DIR)
2 - Download arquivo (DOW)
3 - Obter MD5 parcial (MD5)
4 - Retomar download (DRA)
5 - Download múltiplos por máscara (DMA)
6 - Sair
''')
            escolha = input('Digite o número da opção: ').strip()

            # COMANDO: DIR
            if escolha == '1':
                sock.sendall(b'DIR\n')
                resposta = sock.recv(4096).decode()
                print('Arquivos no servidor:\n' + resposta)

            # COMANDO: DOW
            elif escolha == '2':
                nome = input('Digite o nome do arquivo para download: ').strip()
                sock.sendall(f'DOW {nome}\n'.encode())
                resposta = sock.recv(1024).decode().strip()

                if not resposta.startswith('OK'):
                    print('Arquivo não encontrado no servidor.')
                    continue

                # Resposta do servidor: "OK <tamanho>"
                _, tamanho_str = resposta.split()
                tamanho_total = int(tamanho_str)

                caminho_local = os.path.join(PASTA_SALVAR, nome)
                print(f'Baixando {nome} ({tamanho_total} bytes)...')

                receber_arquivo(sock, caminho_local, tamanho_total)
                print('Download concluído.')

            # COMANDO: MD5
            elif escolha == '3':
                nome = input('Nome do arquivo: ').strip()
                pos = input('Posição final para cálculo MD5 (bytes): ').strip()
                if not pos.isdigit():
                    print('Posição inválida.')
                    continue
                sock.sendall(f'MD5 {nome} {pos}\n'.encode())
                resposta = sock.recv(1024).decode().strip()
                print(f'MD5 parcial: {resposta}')

            # COMANDO: DRA
            elif escolha == '4':
                nome = input('Nome do arquivo para retomar download: ').strip()
                caminho_local = os.path.join(PASTA_SALVAR, nome)
                if not os.path.isfile(caminho_local):
                    print('Arquivo local não encontrado.')
                    continue
                tamanho_local = os.path.getsize(caminho_local)

                sock.sendall(f'DRA {nome} {tamanho_local}\n'.encode())

                resposta = sock.recv(1024).decode().strip()
                if resposta.startswith('ERRO'):
                    print(resposta)
                    continue
                elif resposta == 'OK':
                    print(f'Retomando download a partir do byte {tamanho_local}...')
                    receber_arquivo(sock, caminho_local, 10**9)  # Workaround temporário
                    print('Download retomado concluído.')
                else:
                    print('Resposta inesperada:', resposta)

            # COMANDO: DMA 
            elif escolha == '5':
                mascara = input('Digite a máscara (ex: *.txt): ').strip()
                sock.sendall(f'DMA {mascara}\n'.encode())

                resposta = sock.recv(1024).decode().strip()
                if not resposta.isdigit() or int(resposta) == 0:
                    print('Nenhum arquivo encontrado com essa máscara.')
                    continue

                quantidade = int(resposta)
                print(f'{quantidade} arquivo(s) encontrado(s). Iniciando download...\n')

                for _ in range(quantidade):
                    sock.sendall(b'OK')  # Confirma que está pronto pra receber o nome
                    nome_arquivo = sock.recv(1024).decode().strip()

                    sock.sendall(b'OK')  # Confirma que está pronto pra receber o tamanho
                    tamanho_str = sock.recv(1024).decode().strip()
                    tamanho = int(tamanho_str)

                    sock.sendall(b'OK')  # Confirma que está pronto pra receber o arquivo
                    caminho_local = os.path.join(PASTA_SALVAR, nome_arquivo)

                    print(f'Baixando {nome_arquivo} ({tamanho} bytes)...')
                    receber_arquivo(sock, caminho_local, tamanho)
                    print(f'Download de {nome_arquivo} concluído.')

            # SAIR 
            elif escolha == '6':
                print('Saindo...')
                break

            else:
                print('Opção inválida.')

if __name__ == '__main__':
    main()
