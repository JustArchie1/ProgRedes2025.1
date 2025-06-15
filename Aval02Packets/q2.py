import sys
import subprocess
import os

def extrair_gps_da_foto(caminho):

    # Detecta o nome correto do exiftool dependendo do sistema operacional...

    exiftool_cmd = "exiftool.exe" if os.name == "nt" else "exiftool"

    exiftool_path = os.path.join(".", exiftool_cmd)

    try:

        resultado = subprocess.run(
            [exiftool_path, caminho],
            capture_output=True,
            text=True,
            check=True
        )
    except FileNotFoundError:

        print("Erro: 'exiftool.exe' não foi encontrado na pasta do script.")
        sys.exit(1)

    except subprocess.CalledProcessError:

        print("Erro ao tentar ler os metadados da imagem.")
        sys.exit(1)

    latitude = longitude = None

    for linha in resultado.stdout.splitlines():

        if 'GPS Latitude' in linha and 'Ref' not in linha:

            latitude = converter_para_decimal(linha.split(':', 1)[1].strip())

        elif 'GPS Longitude' in linha and 'Ref' not in linha:

            longitude = converter_para_decimal(linha.split(':', 1)[1].strip())

    if latitude is None or longitude is None:

        print("Erro: A imagem não possui dados de geolocalização.")

        sys.exit(1)

    return latitude, longitude

def converter_para_decimal(valor):

    partes = valor.split()

    graus = float(partes[0])

    minutos = float(partes[2].strip("'"))

    segundos = float(partes[3].strip('"'))

    direcao = partes[4]

    decimal = graus + minutos / 60 + segundos / 3600
    if direcao in ['S', 'W']:
        decimal = -decimal
    return decimal

def abrir_mapa(latitude, longitude):
    url = f"https://www.openstreetmap.org/?mlat={latitude}&mlon={longitude}#map=15/{latitude}/{longitude}"
    if os.name == 'nt':

        # No Windows, precisamos adicionar "" depois de start...

        subprocess.run(f'start "" "{url}"', shell=True)
    else:
        subprocess.run(['xdg-open', url])

def main():
    if len(sys.argv) != 2:
        print("Uso: python script.py imagem.jpeg")
        sys.exit(1)

    caminho = sys.argv[1]

    if not os.path.isfile(caminho):

        print("Erro: Arquivo não encontrado.")

        sys.exit(1)

    latitude, longitude = extrair_gps_da_foto(caminho)

    print(f"Localização extraída: Latitude {latitude}, Longitude {longitude}")
    
    abrir_mapa(latitude, longitude)

if __name__ == "__main__":
    main()
