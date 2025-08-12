import socket
import ssl
import json
import os
import subprocess
import platform
import time
import re
from urllib.parse import urlparse
import threading
import uuid

# CONFIGURAÇÕES DO BOT
# Token do bot fornecido pelo BotFather...
TOKEN = "COLOQUE_SEU_TOKEN_AQUI"

# Endereço e porta da API do Telegram...
HOST = "api.telegram.org"
PORT = 443

# Variável global para controlar o offset dos updates (mensagens)...
ULTIMO_UPDATE_ID = 0

# Pasta onde as imagens baixadas serão salvas...
PASTA_DOWNLOADS = "downloads"

# Criar pasta downloads caso não exista...
if not os.path.exists(PASTA_DOWNLOADS):
    os.mkdir(PASTA_DOWNLOADS)

# Dicionário para armazenar cadastro: chat_id -> nome_usuario
usuarios_cadastrados = {}

# FUNÇÕES DE COMUNICAÇÃO COM TELEGRAM
def enviar_requisicao_https(metodo, caminho, dados=None):
    """
    Envia uma requisição HTTPS para a API do Telegram usando sockets.
    """
    contexto = ssl.create_default_context()
    conexao = socket.create_connection((HOST, PORT))
    conexao_ssl = contexto.wrap_socket(conexao, server_hostname=HOST)

    if dados:
        corpo = json.dumps(dados).encode()
        cabecalho = (
            f"{metodo} {caminho} HTTP/1.1\r\n"
            f"Host: {HOST}\r\n"
            "Content-Type: application/json\r\n"
            f"Content-Length: {len(corpo)}\r\n"
            "Connection: close\r\n\r\n"
        ).encode() + corpo
    else:
        cabecalho = (
            f"{metodo} {caminho} HTTP/1.1\r\n"
            f"Host: {HOST}\r\n"
            "Connection: close\r\n\r\n"
        ).encode()

    conexao_ssl.sendall(cabecalho)

    # Recebe a resposta completa em bytes...
    resposta = b""
    while True:
        dados_recebidos = conexao_ssl.recv(4096)
        if not dados_recebidos:
            break
        resposta += dados_recebidos

    conexao_ssl.close()

    # Separa cabeçalho HTTP do corpo e decodifica JSON...
    try:
        corpo_resposta = resposta.split(b"\r\n\r\n", 1)[1]
        return json.loads(corpo_resposta.decode())
    except:
        return None

def obter_atualizacoes():
    """
    Consulta a API Telegram para receber novas mensagens (updates).
    Usa o offset para receber somente mensagens não processadas.
    Retorna uma lista de updates.
    """
    global ULTIMO_UPDATE_ID
    dados = enviar_requisicao_https(
        "GET",
        f"/bot{TOKEN}/getUpdates?offset={ULTIMO_UPDATE_ID+1}"
    )
    return dados.get("result", [])

def enviar_mensagem(chat_id, texto):
    """
    Envia uma mensagem de texto para o chat_id informado.
    """
    enviar_requisicao_https(
        "POST",
        f"/bot{TOKEN}/sendMessage",
        {"chat_id": chat_id, "text": texto}
    )

# FUNÇÕES DE UTILIDADES DE REDE E SISTEMA
def obter_ip_local():
    """
    Obtém o IP local real da máquina, tentando conectar no Google DNS.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def obter_mascara_gateway(ip_local):
    """
    Obtém a máscara de sub-rede e gateway do IP local.
    Usa comandos do sistema diferentes para Windows e Linux.
    """
    sistema = platform.system()

    if sistema == "Windows":
        try:
            saida_ipconfig = subprocess.check_output("ipconfig", encoding="utf-8")
            blocos = saida_ipconfig.split("\n\n")
            bloco_ip = None
            for b in blocos:
                if ip_local in b:
                    bloco_ip = b
                    break
            if not bloco_ip:
                return "Não encontrado", "Não encontrado"

            mascara_match = re.search(r"Máscara de sub-rede[ .]*: ([\d\.]+)", bloco_ip)
            if not mascara_match:
                mascara_match = re.search(r"Subnet Mask[ .]*: ([\d\.]+)", bloco_ip)
            mascara = mascara_match.group(1) if mascara_match else "Não encontrado"

            saida_route = subprocess.check_output("route print", encoding="utf-8")
            gateway = "Não encontrado"
            linhas = saida_route.splitlines()
            for i, linha in enumerate(linhas):
                if linha.strip().startswith("0.0.0.0"):
                    partes = linha.split()
                    if len(partes) >= 3:
                        gateway = partes[2]
                        break

            return mascara, gateway

        except Exception:
            return "Não encontrado", "Não encontrado"

    else:
        try:
            saida = subprocess.getoutput("ip -o -f inet addr show").splitlines()
            iface_correta = None
            cidr = None
            for linha in saida:
                if ip_local in linha:
                    iface_correta = linha.split()[1]
                    cidr = linha.split()[3]
                    break

            gateway = None
            saida_route = subprocess.getoutput("ip route show default").splitlines()
            for linha in saida_route:
                if iface_correta and iface_correta in linha:
                    gateway = linha.split()[2]
                    break

            return cidr.split('/')[1] if cidr else "Não encontrado", gateway if gateway else "Não encontrado"
        except:
            return "Não encontrado", "Não encontrado"

def obter_gateway():
    """
    Obtém o gateway padrão da máquina (usado no /ping).
    """
    sistema = platform.system()

    if sistema == "Windows":
        try:
            saida_route = subprocess.check_output("route print", encoding="utf-8")
            linhas = saida_route.splitlines()
            for linha in linhas:
                if linha.strip().startswith("0.0.0.0"):
                    partes = linha.split()
                    if len(partes) >= 3:
                        return partes[2]
        except:
            pass
    else:
        try:
            saida_route = subprocess.getoutput("ip route show default").splitlines()
            for linha in saida_route:
                if "default via" in linha:
                    return linha.split()[2]
        except:
            pass

    return None

# FUNÇÕES DOS COMANDOS DO BOT
def cmd_info():
    """
    Comando /info: mostra IP, máscara e gateway local.
    """
    ip_local = obter_ip_local()
    mascara, gateway = obter_mascara_gateway(ip_local)
    return f"IP Local: {ip_local}\nMáscara: {mascara}\nGateway: {gateway}"

def cmd_ping():
    """
    Comando /ping: executa ping 4x para o gateway local e retorna o resultado.
    """
    gateway = obter_gateway()
    if not gateway:
        return "Gateway não encontrado para realizar ping."

    sistema = platform.system()
    if sistema == "Windows":
        comando = ["ping", "-n", "4", gateway]
    else:
        comando = ["ping", "-c", "4", gateway]

    try:
        saida = subprocess.check_output(comando, encoding="utf-8", errors="ignore")
        return f"Ping para o gateway ({gateway}):\n{saida}"
    except Exception as e:
        return f"Erro ao realizar ping: {e}"

def cmd_active(ip):
    """
    Comando /active <ip>: ping 1 pacote para IP informado.
    """
    try:
        if platform.system() == "Windows":
            comando = ["ping", "-n", "1", ip]
        else:
            comando = ["ping", "-c", "1", ip]
        subprocess.check_output(comando)
        return f"{ip} está ativo!"
    except:
        return f"{ip} não respondeu."

def cmd_service(param):
    """
    Comando /service <ip:porta>: tenta conectar TCP na porta para verificar serviço.
    """
    try:
        ip_porta = param.split(":")
        if len(ip_porta) != 2:
            return "Formato inválido. Use /service ip:porta"

        ip = ip_porta[0]
        porta = int(ip_porta[1])
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        resultado = s.connect_ex((ip, porta))
        s.close()
        if resultado == 0:
            return f"Serviço ativo em {ip}:{porta}"
        else:
            return f"Sem serviço ativo em {ip}:{porta}"
    except Exception as e:
        return f"Erro no /service: {e}"

def cmd_dns():
    """
    Comando /dns: mostra o(s) servidor(es) DNS configurado(s) localmente.
    """
    try:
        if platform.system() == "Windows":
            saida = subprocess.check_output(["ipconfig", "/all"], text=True, errors="ignore")
            dns_servers = re.findall(r"Servidor DNS[^\d]*(\d+\.\d+\.\d+\.\d+)", saida)
            if dns_servers:
                return f"DNS: {', '.join(dns_servers)}"
        else:
            with open("/etc/resolv.conf") as f:
                for linha in f:
                    if linha.startswith("nameserver"):
                        return f"DNS: {linha.split()[1]}"
        return "Servidor DNS não encontrado."
    except Exception as e:
        return f"Erro ao obter DNS: {e}"

def cmd_scan(host):
    """
    Comando /scan <host>: escaneia portas comuns (21,22,23,25,53,80,110,443) no host.
    """
    try:
        portas_abertas = []
        for porta in [21, 22, 23, 25, 53, 80, 110, 443]:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            if s.connect_ex((host, porta)) == 0:
                portas_abertas.append(porta)
            s.close()
        if portas_abertas:
            return f"Portas abertas: {', '.join(map(str, portas_abertas))}"
        else:
            return "Nenhuma porta comum aberta encontrada."
    except Exception as e:
        return f"Erro ao escanear: {e}"

def escanear_ip(ip, resultados):
    """
    Função auxiliar para escanear IP na porta 80 (HTTP) usada pelo comando /map.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.3)
    try:
        if s.connect_ex((ip, 80)) == 0:
            resultados.append(ip)
    except:
        pass
    finally:
        s.close()

def cmd_map():
    """
    Comando /map: escaneia a rede local (/24) procurando IPs ativos na porta 80.
    Usa threads para acelerar o processo.
    """
    try:
        ip_bot = obter_ip_local()
        prefixo = ".".join(ip_bot.split(".")[:3]) + "."

        resultados = []

        threads = []
        for i in range(1, 255):
            ip_teste = prefixo + str(i)
            t = threading.Thread(target=escanear_ip, args=(ip_teste, resultados))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        if not resultados:
            return "Nenhuma máquina ativa encontrada na rede local."

        return "Máquinas e portas ativas (porta 80):\n" + "\n".join(resultados)
    except Exception as e:
        return f"Erro no /map: {e}"

def baixar_imagem(url):
    """
    Baixa a imagem no URL via socket HTTPS.
    Salva localmente na pasta downloads.
    Retorna caminho do arquivo e mensagem de status.
    """
    try:
        url_parsed = urlparse(url)
        host = url_parsed.netloc
        path = url_parsed.path
        if not path:
            return None, "URL inválida: sem caminho da imagem."

        porta = 443 if url_parsed.scheme == "https" else 80

        contexto = ssl.create_default_context()
        sock = socket.create_connection((host, porta))
        if porta == 443:
            sock = contexto.wrap_socket(sock, server_hostname=host)

        req = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
        sock.send(req.encode())

        resposta = b""
        while True:
            dado = sock.recv(4096)
            if not dado:
                break
            resposta += dado
        sock.close()

        try:
            header, corpo = resposta.split(b"\r\n\r\n", 1)
        except:
            return None, "Resposta HTTP inválida."

        nome_arquivo = os.path.basename(path)
        if not nome_arquivo:
            nome_arquivo = "imagem_baixada"

        caminho_arquivo = os.path.join(PASTA_DOWNLOADS, nome_arquivo)

        with open(caminho_arquivo, "wb") as f:
            f.write(corpo)

        return caminho_arquivo, f"Imagem salva em {caminho_arquivo}"
    except Exception as e:
        return None, f"Erro ao baixar imagem: {e}"

def enviar_foto(chat_id, caminho_arquivo):
    """
    Envia uma foto para o chat_id usando multipart/form-data na API Telegram.
    """
    with open(caminho_arquivo, "rb") as f:
        conteudo_arquivo = f.read()

    boundary = "--------------------------" + uuid.uuid4().hex

    corpo = []
    corpo.append(f'--{boundary}\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n{chat_id}\r\n')
    nome_arquivo = os.path.basename(caminho_arquivo)
    corpo.append(
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="photo"; filename="{nome_arquivo}"\r\n'
        f'Content-Type: application/octet-stream\r\n\r\n'
    )
    corpo_bytes = b"".join([parte.encode() for parte in corpo])
    corpo_bytes += conteudo_arquivo
    corpo_bytes += f"\r\n--{boundary}--\r\n".encode()

    cabecalho = (
        f"POST /bot{TOKEN}/sendPhoto HTTP/1.1\r\n"
        f"Host: {HOST}\r\n"
        f"Content-Type: multipart/form-data; boundary={boundary}\r\n"
        f"Content-Length: {len(corpo_bytes)}\r\n"
        f"Connection: close\r\n\r\n"
    ).encode()

    contexto = ssl.create_default_context()
    sock = socket.create_connection((HOST, PORT))
    conexao_ssl = contexto.wrap_socket(sock, server_hostname=HOST)
    conexao_ssl.sendall(cabecalho + corpo_bytes)

    resposta = b""
    while True:
        dado = conexao_ssl.recv(4096)
        if not dado:
            break
        resposta += dado

    conexao_ssl.close()

    if b'"ok":true' in resposta:
        return "Foto enviada com sucesso!"
    else:
        return "Falha ao enviar foto."

# LOOP PRINCIPAL DO BOT
print("Bot iniciado...")

while True:
    try:
        updates = obter_atualizacoes()
        for update in updates:
            ULTIMO_UPDATE_ID = update["update_id"]

            mensagem = update.get("message", {})
            texto = mensagem.get("text", "")
            chat_id = mensagem.get("chat", {}).get("id")

            if not texto or not chat_id:
                continue

            print(f"[MSG] {chat_id}: {texto}")

            # Se o usuário não está cadastrado, pede nome para cadastro
            if chat_id not in usuarios_cadastrados:
                nome = texto.strip()
                if len(nome) < 2 or len(nome) > 30:
                    enviar_mensagem(chat_id, "Por favor, envie um nome entre 2 e 30 caracteres para se cadastrar.")
                else:
                    usuarios_cadastrados[chat_id] = nome
                    enviar_mensagem(chat_id, f"Olá, {nome}! Cadastro realizado com sucesso. Agora você pode usar os comandos do bot.")
                continue  # Não processa comandos enquanto não cadastrado

            # Usuário já cadastrado: processa comandos normalmente
            nome_usuario = usuarios_cadastrados[chat_id]

            try:
                if texto.startswith("/info"):
                    enviar_mensagem(chat_id, f"{nome_usuario}, aqui estão suas informações:\n{cmd_info()}")

                elif texto.startswith("/ping"):
                    enviar_mensagem(chat_id, f"{nome_usuario}, executando ping:\n{cmd_ping()}")

                elif texto.startswith("/active"):
                    partes = texto.split()
                    if len(partes) == 2:
                        enviar_mensagem(chat_id, cmd_active(partes[1]))
                    else:
                        enviar_mensagem(chat_id, "Uso: /active <ip>")

                elif texto.startswith("/service"):
                    partes = texto.split()
                    if len(partes) == 2:
                        enviar_mensagem(chat_id, cmd_service(partes[1]))
                    else:
                        enviar_mensagem(chat_id, "Uso: /service <ip:porta>")

                elif texto.startswith("/dns"):
                    enviar_mensagem(chat_id, cmd_dns())

                elif texto.startswith("/map"):
                    enviar_mensagem(chat_id, cmd_map())

                elif texto.startswith("/download"):
                    partes = texto.split(maxsplit=1)
                    if len(partes) == 2:
                        enviar_mensagem(chat_id, "Baixando imagem, aguarde...")
                        caminho, resultado = baixar_imagem(partes[1])
                        enviar_mensagem(chat_id, resultado)
                        if caminho:
                            enviar_mensagem(chat_id, "Enviando imagem para você...")
                            resultado_envio = enviar_foto(chat_id, caminho)
                            enviar_mensagem(chat_id, resultado_envio)
                    else:
                        enviar_mensagem(chat_id, "Uso: /download <url_imagem>")

                elif texto.startswith("/scan"):
                    partes = texto.split()
                    if len(partes) == 2:
                        enviar_mensagem(chat_id, cmd_scan(partes[1]))
                    else:
                        enviar_mensagem(chat_id, "Uso: /scan <host>")

                else:
                    enviar_mensagem(chat_id, "Comando não reconhecido.")

            except Exception as e:
                enviar_mensagem(chat_id, f"Erro ao processar comando: {e}")
                print(f"[ERRO COMANDO] {e}")

        time.sleep(2)

    except Exception as e:
        print(f"[ERRO LOOP] {e}")
        time.sleep(5)
