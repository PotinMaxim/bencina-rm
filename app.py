import streamlit as st
import sqlite3
import pandas as pd
import folium
from streamlit_folium import st_folium

# Configuración de pantalla para teléfonos inteligentes
st.set_page_config(page_title="BencinaRM", page_icon="⛽", layout="centered")
st.title("⛽ BencinaRM")

def cargar_datos_comuna(comuna, combustible):
    conn = sqlite3.connect("bencina_rm.db")
    
    # Buscar la última fecha con datos en SQLite
    df_max_fecha = pd.read_sql_query("SELECT MAX(fecha) as f FROM registro_precios", conn)
    ultima_fecha = df_max_fecha['f'].iloc[0]
    
    if not ultima_fecha:
        conn.close()
        return pd.DataFrame(), None

    # Consulta SQL filtrada por comuna y combustible activo
    query = f"""
        SELECT distribuidor, direccion, latitud, longitud, {combustible} as precio 
        FROM registro_precios 
        WHERE comuna = '{comuna}' AND fecha = '{ultima_fecha}' AND precio > 0
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df, ultima_fecha

# Listado oficial de comunas de la RM mapeadas idénticas a la API de la CNE
comunas_rm = [
    "Santiago", "Cerrillos", "Cerro Navia", "Conchalí", "El Bosque", 
    "Estación Central", "Huechuraba", "Independencia", "La Cisterna", 
    "La Florida", "La Granja", "La Pintana", "La Reina", "Las Condes", 
    "Lo Barnechea", "Lo Espejo", "Lo Prado", "Macul", "Maipú", 
    "Ñuñoa", "Pedro Aguirre Cerda", "Peñalolén", "Providencia", 
    "Pudahuel", "Quilicura", "Quinta Normal", "Recoleta", "Renca", 
    "San Joaquín", "San Miguel", "San Ramón", "Vitacura", "Puente Alto", 
    "Pirque", "San José de Maipo", "San Bernardo", "Buin", "Paine"
]

comuna_sel = st.selectbox("Selecciona tu Comuna:", sorted(comunas_rm))
combustible_sel = st.radio("Combustible:", ["g93", "g95", "g97", "diesel"], 
                           format_func=lambda x: "Diésel" if x=="diesel" else f"Gasolina {x.replace('g', '')}")

df_estaciones, fecha_data = cargar_datos_comuna(comuna_sel, combustible_sel)

if not df_estaciones.empty:
    min_p = df_estaciones['precio'].min()
    max_p = df_estaciones['precio'].max()
    
    # Cálculo del punto medio de la comuna para centrar la cámara del mapa
    centro_lat = df_estaciones['latitud'].mean()
    centro_lon = df_estaciones['longitud'].mean()
    
    m = folium.Map(location=[centro_lat, centro_lon], zoom_start=13, tiles="OpenStreetMap")
    
    # Inyección de los pines interactivos en el mapa
    for _, row in df_estaciones.iterrows():
        if row['precio'] == min_p:
            color_pin = "green"   # El más económico
        elif row['precio'] == max_p:
            color_pin = "red"     # El más costoso
        else:
            color_pin = "orange"  # Precio normal
            
        popup_html = f"<b>{row['distribuidor']}</b><br>{row['direccion']}<br>Precio: ${int(row['precio'])}"
        folium.Marker(
            location=[row['latitud'], row['longitud']],
            popup=popup_html,
            icon=folium.Icon(color=color_pin, icon="info-sign")
        ).add_to(m)
        
    # Renderizar mapa dinámico
    st_folium(m, width=340, height=400)
    st.caption(f"Precios oficiales actualizados al: {fecha_data}. Verde: Más barato / Rojo: Más caro.")
else:
    st.warning(f"No se encontraron datos para {comuna_sel} en la última actualización. Selecciona otra comuna para probar.")
