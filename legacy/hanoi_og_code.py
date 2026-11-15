#Metodo Iterativo - IQ humano

def hanoi_iterativo(n, origen, destino, auxiliar):
    total_moves = 2**n - 1
    torres = {origen: list(range(n,0,-1)), destino: [], auxiliar: []}

    def mover(origen, destino):
        disco = torres[origen].pop()
        torres[destino].append(disco)
        print(f"Mover disco {disco} de {origen} a {destino}")

    for i in range(1, total_moves+1):
        if i % 3 == 1:
            mover(origen if len(torres[origen])>0 else destino,
                  destino if len(torres[destino])<1 or
                   (torres[origen] and torres[origen][-1] < torres[destino][-1]) else origen)
        elif i % 3 == 2:
            mover(origen if len(torres[origen])>0 else auxiliar,
                  auxiliar if len(torres[auxiliar])<1 or
                   (torres[origen] and torres[origen][-1] < torres[auxiliar][-1]) else origen)
        else:
            mover(auxiliar if len(torres[auxiliar])>0 else destino,
                  destino if len(torres[destino])<1 or
                   (torres[auxiliar] and torres[auxiliar][-1] < torres[destino][-1]) else auxiliar)

n = 3
hanoi_iterativo(n,"A","C","B")

# Metodo usando Recursividad - IA

def hanoi(n, origen, destino, auxiliar):

  '''
  Argumentos:
  n -- número de discos
  origen -- poste de origen
  destino -- poste de destino
  auxiliar -- poste auxiliar
  '''

  # Caso base: si solo queda 1 disco, lo movemos directamente.
  if n == 1:
    print(f"Mover disco {n} de {origen} a {destino}")
    return
  # Paso 1: Mover n-1 discos del poste de origen al poste auxiliar
  hanoi(n-1, origen, auxiliar, destino)
  # Paso 2: Mover el disco n del poste de origen al poste de destino
  print(f"Mover disco {n} de {origen} a {destino}")
  # Paso 3: Mover n-1 discos del poste auxiliar al poste de destino
  hanoi(n-1, auxiliar, destino, origen)

