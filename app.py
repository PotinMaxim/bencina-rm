import streamlit as st
import sqlite3
import pandas as pd
import folium
from streamlit_folium import st_folium

# Configuración de página optimizada para celulares
st.set_page_config(page_title="BencinaRM", page_icon="⛽", layout="centered")
st.title("⛽ BencinaRM")

def cargar_datos_comuna(comuna, combustible):
    # Conectamos a la base de datos que descargó GitHub Actions
    conn = sqlite3.connect("bencina_rm.db")
    
    # Buscamos la fecha más reciente que tengamos registrada
    df_max_fecha = pd.read_sql_query("SELECT MAX(fecha) as f FROM registro_precios", conn)
    ultima_fecha = df_max_fecha['f'].iloc[0]
    
    # Traemos los datos específicos de la comuna elegida
    query = f"""
        SELECT distribuidor, direccion, latitud, longitud, {combustible} as precio 
        FROM registro_precios 
        WHERE comuna = '{comuna}' AND fecha = '{ultima_fecha}' AND precio > 0
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df, ultima_fecha

# Selectores simples para usar con el pulgar en el teléfono
comunas_rm = [
    "Santiago", "Providencia", "Las Condes", "Vitacura", "Ñuñoa", "Maipú", 
    "La Florida", "Puente Alto", "San Miguel", "Recoleta", "Independencia",
    "Estación Central", "Peñalolén", "Macul", "Quinta Normal", "Pudahuel"
]

comuna_sel = st.selectbox("Selecciona tu Comuna:", sorted(comunas_rm))
combustible_sel = st.radio("Combustible:", ["g93", "g95", "g97", "diesel"], 
                           format_func=lambda x: "Diésel" if x=="diesel" else f"Gasolina {x.replace('g', '')}")

# Cargar los datos filtrados
df_estaciones, fecha_data = cargar_datos_comuna(comuna_sel, combustible_sel)

if not df_estaciones.empty:
    min_p = df_estaciones['precio'].min()
    max_p = df_estaciones['precio'].max()
    
    # Centrar el mapa automáticamente según las estaciones de la comuna
    centro_lat = df_estaciones['latitud'].mean()
    centro_lon = df_estaciones['longitud'].mean()
    
    m = folium.Map(location=[centro_lat, centro_lon], zoom_start=13, tiles="OpenStreetMap")
    
    # Dibujar los pines en el mapa
    for _, row in df_estaciones.iterrows():
        # Lógica de semáforo de precios
        if row['precio'] == min_p:
            color_pin = "green"  # El más barato de la comuna
        elif row['precio'] == max_p:
            color_pin = "red"    # El más caro de la comuna
        else:
            color_pin = "orange" # Promedio
            
        popup_html = f"<b>{row['distribuidor']}</b><br>{row['direccion']}<br>Precio: ${int(row['precio'])}"
        folium.Marker(
            location=[row['latitud'], row['longitud']],
            popup=popup_html,
            icon=folium.Icon(color=color_pin, icon="info-sign")
        ).add_to(m)
        
    # Mostrar el mapa adaptado al ancho del celular
    st_folium(m, width=340, height=400)
    st.caption(f"Precios oficiales actualizados al: {fecha_data}. Verde: Más barato / Rojo: Más caro.")
else:
    st.warning("No se encontraron registros activos para la comuna seleccionada.")
