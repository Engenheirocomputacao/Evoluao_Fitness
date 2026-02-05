import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_treinamento.settings')
django.setup()

from treinamento.models import RegistroTreinamento

def debug_records():
    print("Fetching all IDs...")
    try:
        # Fetch only IDs first to avoid triggering the decimal converter on bad data
        ids = list(RegistroTreinamento.objects.values_list('id', flat=True))
        print(f"Found {len(ids)} records. Checking each one...")
    except Exception as e:
        print(f"Error fetching IDs: {e}")
        return

    for pk in ids:
        try:
            # Fetch full object
            obj = RegistroTreinamento.objects.get(pk=pk)
            # Access decimal fields to force conversion
            val = obj.valor_alcançado
            conf = obj.confiabilidade
            # print(f"ID {pk} OK: val={val}, conf={conf}")
        except Exception as e:
            print(f"CRASH at ID {pk}: {e}")
            try:
                # Try to inspect raw data for this ID using direct SQL
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute("SELECT valor_alcançado, confiabilidade FROM treinamento_registrotreinamento WHERE id = %s", [pk])
                    row = cursor.fetchone()
                    print(f"RAW DATA for ID {pk}: valor_alcançado={repr(row[0])}, confiabilidade={repr(row[1])}")
            except Exception as sql_e:
                print(f"Could not fetch raw data: {sql_e}")

if __name__ == "__main__":
    debug_records()
