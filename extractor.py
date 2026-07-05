import requests
import sqlite3
from datetime import datetime

# URL oficial de la CNE
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
        print("Conectando con la API de la CNE...")
        # Forzamos un User-Agent para que la API no bloquee a GitHub pensando que es un ataque
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(URL_API, headers=headers, timeout=25)
        
        print(f"Código de respuesta del servidor CNE: {response.status_code}")
        data = response.json()
        
        if "resultado" in data and data["resultado"]:
            fecha_hoy = datetime.now().strftime('%Y-%m-%d')
            contador = 0
            
            for est in data["resultado"]:
                # Filtramos por Región Metropolitana buscando texto o ID
                nom_region = str(est.get("region", "")).lower()
                id_reg = str(est.get("id_region", ""))
                
                if "metropolitana" in nom_region or id_reg == "13":
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
            print(f"--> ¡ÉXITO! Se guardaron {contador} estaciones de la RM en la base de datos.")
        else:
            print("--> ERROR: La API respondió pero el formato de los datos no es el esperado o está vacío.")
            print(f"Contenido recibido (primeros 200 caracteres): {str(data)[:200]}")
            
    except Exception as e:
        print(f"--> FALLÓ LA CONEXIÓN: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    actualizar_base_datos()
