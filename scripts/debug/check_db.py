import sqlite3
import sys

def check_decimals():
    try:
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        
        # Check RegistroTreinamento table
        print("Checking treinamento_registrotreinamento table...")
        cursor.execute("SELECT id, valor_alcançado, confiabilidade FROM treinamento_registrotreinamento")
        rows = cursor.fetchall()
        
        invalid_count = 0
        for row in rows:
            id, valor, confiabilidade = row
            
            # Check valor_alcançado
            try:
                if valor is not None:
                    float(valor)
            except ValueError:
                print(f"Invalid valor_alcançado at ID {id}: {repr(valor)}")
                invalid_count += 1
                
            # Check confiabilidade
            try:
                if confiabilidade is not None:
                    float(confiabilidade)
            except ValueError:
                print(f"Invalid confiabilidade at ID {id}: {repr(confiabilidade)}")
                invalid_count += 1
                
        print(f"Finished checking. Found {invalid_count} invalid records.")
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_decimals()
