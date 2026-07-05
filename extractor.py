import requests
import sqlite3
from datetime import datetime

# Cambiamos a la API de Energía Abierta de la CNE que es 100% libre y sin tokens
URL_API = "https://api.cne.cl/v1/combustibles/vehicular/estaciones"

def actualizar_base_datos():
    conn = sqlite3.connect("bencina_rm.db")
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registro_precios (
            fecha TEXT,
            id_estacion TEXT,
            comuna TEXT,
            distribuidor TEXT,
            direccion TEXT,
            latitud REAL,
            longitud REAL,
            g93 REAL,
            g95 REAL,
            g97 REAL,
            diesel REAL
        )
    ''')
    
    try:
        # Llamamos a la API abierta
        response = requests.get(URL_API, timeout=20)
        data = response.json()
        
        if "resultado" in data:
            fecha_hoy = datetime.now().strftime('%Y-%m-%d')
            contador = 0
            
            for est in data["resultado"]:
                # Filtramos manualmente por la Región Metropolitana (ID: 13)
                if str(est.get("id_region")) == "13" or est.get("region") == "Región Metropolitana de Santiago":
                    precios = est.get("precios", {})
                    
                    cursor.execute('''
                        INSERT INTO registro_precios VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        fecha_hoy,
                        est.get("id"),
                        est.get("comuna"),
                        est.get("distribuidor"),
                        est.get("direccion"),
                        float(est.get("latitud") or 0),
                        float(est.get("longitud") or 0),
                        float(precios.get("93", 0)),
                        float(precios.get("95", 0)),
                        float(precios.get("97", 0)),
                        float(precios.get("diesel", 0))
                    ))
                    contador += 1
                    
            conn.commit()
            print(f"[{fecha_hoy}] ¡Base de datos cargada con {contador} estaciones de la RM!")
        else:
            print("La API no entregó el formato 'resultado' esperado.")
    except Exception as e:
        print(f"Error al conectar con la API: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    actualizar_base_datos()
