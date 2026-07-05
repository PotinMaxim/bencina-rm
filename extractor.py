import requests
import sqlite3
from datetime import datetime

# URL pública de la CNE (Región Metropolitana = 13)
URL_API = "https://api.cne.cl/v1/combustibles/vehicular/estaciones?region=13"

def actualizar_base_datos():
    # Conexión automática con la base de datos SQLite local
    conn = sqlite3.connect("bencina_rm.db")
    cursor = conn.cursor()
    
    # Estructura de la tabla para almacenar el histórico diario
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
        # Llamada a la API de Energía Abierta
        response = requests.get(URL_API, timeout=15)
        data = response.json()
        
        if "resultado" in data:
            fecha_hoy = datetime.now().strftime('%Y-%m-%d')
            
            for est in data["resultado"]:
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
            conn.commit()
            print(f"[{fecha_hoy}] ¡Base de datos actualizada con éxito!")
        else:
            print("La API no entregó resultados válidos.")
    except Exception as e:
        print(f"Error al conectar con la API: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    actualizar_base_datos()
