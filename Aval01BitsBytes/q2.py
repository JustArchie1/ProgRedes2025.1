import hashlib
import time

def encontrarNonce(dadosParaHash, bitsParaSerZero):
    tempo_inicio = time.time()
    nonce = 0
    while True:
        # Converte o nonce para 4 bytes em big-endian...

        nonce_bytes = nonce.to_bytes(4, byteorder='big')
        # Concatena nonce + dados...

        dados_com_nonce = nonce_bytes + dadosParaHash
        # Calcula o hash SHA-256...

        hash_resultado = hashlib.sha256(dados_com_nonce).digest()
        # Converte o hash para um inteiro de 256 bits para verificar os bits iniciais...

        hash_int = int.from_bytes(hash_resultado, byteorder='big')

        # Calcula quantos bits zerados são necessários no início...

        deslocamento_necessario = 256 - bitsParaSerZero

        # Verifica se os primeiros 'bitsParaSerZero' bits são zero...

        if hash_int >> deslocamento_necessario == 0:

            tempo_fim = time.time()

            tempo_decorrido = tempo_fim - tempo_inicio

            return nonce, hash_resultado.hex(), tempo_decorrido
        
        nonce += 1

# Dados para testar...
casos_de_teste = [
    ("Esse um texto elementar", 8),
    ("Esse um texto elementar", 10),
    ("Esse um texto elementar", 15),
    ("Textinho", 8),
    ("Textinho", 18),
    ("Textinho", 22),
    ("Meu texto médio", 18),
    ("Meu texto médio", 19),
    ("Meu texto médio", 20)
]

# Executa os testes e imprime a tabela...

print("{:<25} {:<15} {:<15} {:<20}".format("Texto", "Bits em zero", "Nonce", "Tempo em segundos"))

print("-" * 75)
for texto, bits in casos_de_teste:

    dados = texto.encode('utf-8')

    nonce, hash_encontrado, tempo_gasto = encontrarNonce(dados, bits)

    print("{:<25} [Bits em zero: {:<3}] [Nonce: {:<10}] [Tempo em segundos: {:.6f}]".format(

        f'"{texto}"', bits, nonce, tempo_gasto))
