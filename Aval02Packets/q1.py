import sys
import struct

# Dicionário com tipos de ICMP para mostrar o nome...

tipos_icmp = {
    0: "Echo Reply",
    3: "Destino Inalcançável",
    5: "Redirect",
    8: "Echo Request",
    11: "Tempo Excedido"
}

# Dicionário para armazenar dados TCP para mostrar 200 bytes de aplicação...

dados_tcp_ja_vistos = {}

# Verifica se o nome do arquivo foi passado...

if len(sys.argv) != 2:

    print("Uso: python analisador.py arquivo.pcap")

    sys.exit(1)

nome_arquivo = sys.argv[1]

arquivo = open(nome_arquivo, 'rb')

# Ler cabeçalho global do PCAP (24 bytes)...

cabecalho_global = arquivo.read(24)

if len(cabecalho_global) < 24:
    print("Arquivo PCAP inválido.")
    sys.exit(1)

contador_pacotes = 0

while True:

    cabecalho_pacote = arquivo.read(16)
    if len(cabecalho_pacote) < 16:

        break  # fim do arquivo...

    ts_sec, ts_usec, tam_incluido, tam_original = struct.unpack('=IIII', cabecalho_pacote)
    dados_pacote = arquivo.read(tam_incluido)

    if len(dados_pacote) < 14:

        continue  # pacote muito pequeno...

    contador_pacotes += 1
    print(f"\n=== Pacote {contador_pacotes} ===")

    mac_destino = dados_pacote[0:6]

    mac_origem = dados_pacote[6:12]

    tipo_ethernet = struct.unpack('!H', dados_pacote[12:14])[0]

    mac_destino_str = ':'.join(f'{b:02x}' for b in mac_destino)

    mac_origem_str = ':'.join(f'{b:02x}' for b in mac_origem)

    print(f"MAC Origem: {mac_origem_str} -> MAC Destino: {mac_destino_str}")

    payload = dados_pacote[14:]

    # ARP ou RARP...

    if tipo_ethernet == 0x0806 and len(payload) >= 28:
        tipo_hardware, tipo_protocolo, tam_mac, tam_ip, operacao = struct.unpack('!HHBBH', payload[0:8])

        if tipo_protocolo == 0x0800:
            mac_remetente = ':'.join(f'{b:02x}' for b in payload[8:14])

            ip_remetente = '.'.join(str(b) for b in payload[14:18])

            mac_destinatario = ':'.join(f'{b:02x}' for b in payload[18:24])

            ip_destinatario = '.'.join(str(b) for b in payload[24:28])

            nome_operacao = "ARP" if operacao in [1, 2] else "RARP"

            print(f"[{nome_operacao}] Operação: {operacao}")
            print(f"  MAC Remetente: {mac_remetente} -> MAC Destinatário: {mac_destinatario}")
            print(f"  IP Remetente: {ip_remetente} -> IP Destinatário: {ip_destinatario}")

    # IPv4
    elif tipo_ethernet == 0x0800 and len(payload) >= 20:
        versao_ihl = payload[0]
        versao = versao_ihl >> 4
        tamanho_header = (versao_ihl & 0x0F) * 4
        tamanho_total = struct.unpack('!H', payload[2:4])[0]
        protocolo = payload[9]
        ip_origem = '.'.join(str(b) for b in payload[12:16])
        ip_destino = '.'.join(str(b) for b in payload[16:20])
        print(f"[IPv4] {ip_origem} -> {ip_destino}")
        print(f"  Tamanho do Cabeçalho: {tamanho_header} bytes")
        print(f"  TTL: {payload[8]}")
        print(f"  Protocolo: {protocolo}")
        print(f"  ID do Pacote: {struct.unpack('!H', payload[4:6])[0]}")

        camada4 = payload[tamanho_header:tamanho_total]

        # ICMP
        if protocolo == 1 and len(camada4) >= 4:
            tipo_icmp = camada4[0]
            codigo_icmp = camada4[1]
            print(f"  [ICMP] Tipo: {tipo_icmp} ({tipos_icmp.get(tipo_icmp, 'Outro')})")
            if tipo_icmp in [0, 8]:
                identificador, sequencia = struct.unpack('!HH', camada4[4:8])
                print(f"    Identificador: {identificador}")
                print(f"    Sequência: {sequencia}")

        # UDP
        elif protocolo == 17 and len(camada4) >= 8:
            porta_origem, porta_destino = struct.unpack('!HH', camada4[0:4])
            print(f"  [UDP] Porta Origem: {porta_origem}, Porta Destino: {porta_destino}")

        # TCP
        elif protocolo == 6 and len(camada4) >= 20:
            porta_origem, porta_destino, seq, ack, offset_flags = struct.unpack('!HHIIH', camada4[0:14])
            tamanho_tcp = (offset_flags >> 12) * 4
            flags = offset_flags & 0x01FF
            janela = struct.unpack('!H', camada4[14:16])[0]

            print(f"  [TCP] Porta Origem: {porta_origem}, Porta Destino: {porta_destino}")

            print(f"    Número de Sequência: {seq}")

            print(f"    Número de Confirmação: {ack}")

            print(f"    Flags: 0x{flags:03x}")
            
            print(f"    Janela: {janela}")

            dados_aplicacao = camada4[tamanho_tcp:]
            fluxo_id = (ip_origem, porta_origem, ip_destino, porta_destino)

            if flags & 0x002:  # flag SYN...

                dados_tcp_ja_vistos[fluxo_id] = 0

            elif fluxo_id in dados_tcp_ja_vistos and len(dados_aplicacao) > 0:

                faltam = 200 - dados_tcp_ja_vistos[fluxo_id]

                mostrar = dados_aplicacao[:faltam]

                print(f"    Dados da Aplicação (até 200 bytes): {mostrar}")

                dados_tcp_ja_vistos[fluxo_id] += len(mostrar)

                if dados_tcp_ja_vistos[fluxo_id] >= 200:
                    
                    del dados_tcp_ja_vistos[fluxo_id]

arquivo.close()