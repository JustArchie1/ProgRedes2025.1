def ip_para_int(ip_str):

    # Converte uma string de IP para um inteiro...

    partes = list(map(int, ip_str.split('.')))

    return (partes[0] << 24) | (partes[1] << 16) | (partes[2] << 8) | partes[3]

def int_para_ip(ip_int):

    # Converte um inteiro para string de IP...

    return f"{(ip_int >> 24) & 0xFF}.{(ip_int >> 16) & 0xFF}.{(ip_int >> 8) & 0xFF}.{ip_int & 0xFF}"

def calcular():

    # Entrada do usuário...

    ip_str = input("Digite o endereço IPv4 (ex: 200.17.143.131): ")

    mascara_bits = int(input("Digite a máscara em bits (ex: 18): "))

    # Converte o IP para inteiro...

    ip_int = ip_para_int(ip_str)

    # Calcula a máscara de sub-rede como inteiro...

    mascara = (0xFFFFFFFF << (32 - mascara_bits)) & 0xFFFFFFFF

    # a) Endereço da rede: IP AND máscara...

    endereco_rede = ip_int & mascara

    # b) Endereço de broadcast: IP OR complemento da máscara...

    endereco_broadcast = ip_int | (~mascara & 0xFFFFFFFF)

    # c) Endereço do gateway: último IP válido (broadcast - 1)...

    gateway = endereco_broadcast - 1

    # d) Número de hosts possíveis: 2^(32 - bits) - 2 (desconta rede e broadcast)...

    num_hosts = 2 ** (32 - mascara_bits) - 2 if mascara_bits < 31 else 0

    # Resultados!

    print(f"\nResultados:")
    print(f"a) Endereço da rede: {int_para_ip(endereco_rede)}")
    print(f"b) Endereço de broadcast: {int_para_ip(endereco_broadcast)}")
    print(f"c) Endereço do gateway: {int_para_ip(gateway)}")
    print(f"d) Número de hosts possíveis: {num_hosts}")

# Executa o programa...
calcular()