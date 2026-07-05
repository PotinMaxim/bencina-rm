import requests
import sqlite3
from datetime import datetime

# URL oficial v4 de la CNE (Respuesta 200 confirmada)
URL_API = "https://api.cne.cl/api/v4/estaciones"

def limpiar_texto(texto):
    if not texto:
        return ""
    # Reemplaza tildes y deja en minúsculas para un emparejamiento perfecto con Streamlit
    remplazos = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U"}
    texto_limpio = str(texto).strip()
    for origen, destino in remplazos.items():
        texto_limpio = texto_limpio.replace(origen, destino)
    return texto_limpio.lower()

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
        print("Conectando a la API Real de la CNE (v4)...")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(URL_API, headers=headers, timeout=25)
        
        if response.status_code == 200:
            data = response.json()
            fecha_hoy = datetime.now().strftime('%Y-%m-%d')
            contador = 0
            
            # Recorremos la lista de estaciones directa de la v4
            for est in data:
                # Filtramos por la Región Metropolitana (id_region: 13)
                if str(est.get("id_region")) == "13":
                    
                    # CORRECCIÓN V4: Los precios vienen directo en la raíz de la estación
                    p_93 = est.get("93") or est.get("g93") or 0
                    p_95 = est.get("95") or est.get("g95") or 0
                    p_97 = est.get("97") or est.get("g97") or 0
                    p_diesel = est.get("diesel") or est.get("petroleo") or 0
                    
                    cursor.execute('''
                        INSERT INTO registro_precios VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        fecha_hoy,
                        str(est.get("id")),
                        est.get("comuna"),  # Guardamos el nombre tal cual
                        est.get("distribuidor"),
                        est.get("direccion"),
                        float(est.get("latitud") or 0),
                        float(est.get("longitud") or 0),
                        float(p_93),
                        float(p_95),
                        float(p_97),
                        float(p_diesel)
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
