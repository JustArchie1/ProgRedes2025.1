def ler_jpg_info(caminho):
    with open(caminho, 'rb') as f:
        dados = f.read()

    if not dados.startswith(b'\xFF\xD8'):
        print("Não é um arquivo JPG válido.")
        return

    i = 2
    largura = altura = 0
    num_metadados = 0

    while i < len(dados):
        
        if dados[i] != 0xFF:

            break

        marcador = dados[i+1]

        tamanho_segmento = int.from_bytes(dados[i+2:i+4], byteorder='big')
        
        # EXIF geralmente está no APP1 (0xE1)...

        if marcador == 0xE1 and dados[i+4:i+10] == b'Exif\x00\x00':

            num_metadados += 1

        # SOF0 (0xC0) contém as dimensões da imagem...

        if 0xC0 <= marcador <= 0xC3:

            altura = int.from_bytes(dados[i+5:i+7], byteorder='big')

            largura = int.from_bytes(dados[i+7:i+9], byteorder='big')

        i += 2 + tamanho_segmento

    print(f"Largura: {largura}px")

    print(f"Altura: {altura}px")

    print(f"Número de blocos EXIF detectados: {num_metadados}")

caminho = "teste.jpg"  # Substitua pelo seu arquivo
ler_jpg_info(caminho)
