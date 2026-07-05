import requests
import sqlite3
from datetime import datetime

# La URL oficial, real y actualizada al día de hoy según la documentación de la CNE
URL_API = "https://api.cne.cl/api/v4/estaciones"

def actualizar_base_datos():
    conn = sqlite3.connect("bencina_rm.db")
    cursor = conn.cursor()
    
    # Mantenemos la estructura limpia para el histórico diario
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
        print("Conectando a la API Real de la CNE (v4)...")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(URL_API, headers=headers, timeout=25)
        
        print(f"Código de respuesta del servidor CNE: {response.status_code}")
        
        # Si responde un 200, estamos al otro lado
        if response.status_code == 200:
            data = response.json()
            fecha_hoy = datetime.now().strftime('%Y-%m-%d')
            contador = 0
            
            # Recorremos la lista directa de estaciones que manda la API nueva
            for est in data:
                # Filtramos por la Región Metropolitana (id_region: 13)
                if str(est.get("id_region")) == "13":
                    precios = est.get("precios", {})
                    
                    cursor.execute('''
                        INSERT INTO registro_precios VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        fecha_hoy,
                        str(est.get("id")),
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
            print(f"--> ¡ÉXITO TOTAL! Se guardaron {contador} estaciones de la RM en tu base de datos.")
        else:
            print(f"--> El servidor de la CNE respondió con error {response.status_code}")
            
    except Exception as e:
        print(f"--> FALLÓ EL PROCESAMIENTO: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    actualizar_base_datos()
