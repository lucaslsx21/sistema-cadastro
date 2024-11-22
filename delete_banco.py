# Esse código serve para apagar todo o meu banco de dados
import sqlite3

try:
    
    banco = sqlite3.connect("tasks.db")

    cursor = banco.cursor()

    cursor.execute("DELETE FROM sqlite_sequence")

    banco.commit()

    banco.close()
    
    print("os dados foram removidos com sucesso!!")
    
except sqlite3.Error as erro:
    print("Erro ao excluir: ", erro)