def etiquetas(terminos, n):
    salida = {}
    for pauli, qubits, coef in terminos:
        letras = ["I"] * n
        for letra, qubit in zip(pauli, qubits):
            letras[qubit] = letra
        salida["".join(letras)] = float(coef)
    return salida
