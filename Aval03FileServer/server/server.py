import socket
import threading
import os
import hashlib
import fnmatch

# Pasta onde os arquivos disponíveis para download estão
PASTA_ARQUIVOS = 'arquivos'

# Função que lida com cada cliente
def handle_client(conn, addr):
    try:
        print(f"[+] Conectado com {addr}")
        while True:
            try:
                dados = conn.recv(1024).decode().strip()
                if not dados:
                    break  # Cliente desconectou normalmente

                print(f"[Comando recebido de {addr}]: {dados}")
                partes = dados.split()
                if not partes:
                    continue

                comando = partes[0].upper()

                if comando == 'DIR':
                    arquivos = os.listdir(PASTA_ARQUIVOS)
                    resposta = '\n'.join(f"{arq} - {os.path.getsize(os.path.join(PASTA_ARQUIVOS, arq))} bytes" for arq in arquivos)
                    conn.send(resposta.encode())

                elif comando == 'DOW' and len(partes) > 1:
                    nome_arquivo = ' '.join(partes[1:])
                    caminho_arquivo = os.path.join(PASTA_ARQUIVOS, nome_arquivo)
                    if os.path.exists(caminho_arquivo):
                        tamanho = os.path.getsize(caminho_arquivo)
                        conn.send(f'OK {tamanho}'.encode())  # Envia OK + tamanho do arquivo
                        with open(caminho_arquivo, 'rb') as f:
                            while True:
                                dados = f.read(1024)
                                if not dados:
                                    break
                                conn.sendall(dados)
                    else:
                        conn.send(b'ERRO: Arquivo nao encontrado.')

                elif comando == 'MD5' and len(partes) > 2:
                    nome_arquivo = ' '.join(partes[1:-1])
                    tamanho = int(partes[-1])
                    caminho_arquivo = os.path.join(PASTA_ARQUIVOS, nome_arquivo)
                    if os.path.exists(caminho_arquivo):
                        with open(caminho_arquivo, 'rb') as f:
                            f.seek(0)
                            dados = f.read(tamanho)
                            hash_md5 = hashlib.md5(dados).hexdigest()
                        conn.send(hash_md5.encode())
                    else:
                        conn.send(b'ERRO: Arquivo nao encontrado.')

                elif comando == 'DRA' and len(partes) > 2:
                    nome_arquivo = ' '.join(partes[1:-1])
                    tamanho_existente = int(partes[-1])
                    caminho_arquivo = os.path.join(PASTA_ARQUIVOS, nome_arquivo)
                    if os.path.exists(caminho_arquivo):
                        with open(caminho_arquivo, 'rb') as f:
                            f.seek(tamanho_existente)
                            conn.send(b'OK')
                            while True:
                                dados = f.read(1024)
                                if not dados:
                                    break
                                conn.sendall(dados)
                    else:
                        conn.send(b'ERRO: Arquivo nao encontrado.')

                elif comando == 'DMA' and len(partes) > 1:
                    mascara = ' '.join(partes[1:])
                    arquivos = fnmatch.filter(os.listdir(PASTA_ARQUIVOS), mascara)
                    if arquivos:
                        conn.send(f"{len(arquivos)}".encode())
                        for nome_arquivo in arquivos:
                            conn.recv(2)  # Espera 'OK' do cliente para enviar nome
                            conn.send(nome_arquivo.encode())

                            ack = conn.recv(2)  # Espera 'OK' do cliente para enviar tamanho
                            if ack != b'OK':
                                break

                            caminho_arquivo = os.path.join(PASTA_ARQUIVOS, nome_arquivo)
                            tamanho = os.path.getsize(caminho_arquivo)
                            conn.send(str(tamanho).encode())

                            ack = conn.recv(2)  # Espera 'OK' do cliente para enviar dados
                            if ack != b'OK':
                                break

                            with open(caminho_arquivo, 'rb') as f:
                                while True:
                                    dados = f.read(1024)
                                    if not dados:
                                        break
                                    conn.sendall(dados)
                    else:
                        conn.send(b'0')

                else:
                    conn.send(b'ERRO: Comando desconhecido.')

            except ConnectionResetError:
                print(f"[!] Cliente {addr} desconectou abruptamente.")
                break
            except Exception as e:
                print(f"[!] Erro no comando de {addr}: {e}")
                conn.send(b'ERRO: Problema ao processar comando.')

    finally:
        conn.close()
        print(f"[-] Conexao encerrada com {addr}")

# Função principal do servidor
def iniciar_servidor(host='0.0.0.0', porta=5000):
    if not os.path.exists(PASTA_ARQUIVOS):
        os.makedirs(PASTA_ARQUIVOS)

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((host, porta))
    servidor.listen(5)
    print(f"[SERVIDOR] Servidor ouvindo em {host}:{porta}\n")

    try:
        while True:
            conn, addr = servidor.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
    except KeyboardInterrupt:
        print("\n[!] Encerrando servidor...")
    finally:
        servidor.close()

if __name__ == '__main__':
    iniciar_servidor()
