# --- 1. IMPORTACIÓN DE LIBRERÍAS (Las herramientas que vamos a usar) ---
import streamlit as st       # Se encarga de crear toda la interfaz web (botones, textos, diseño).
import pandas as pd          # Es como un "Excel" para Python. Organiza los datos en filas y columnas.
import plotly.express as px  # La librería "mágica" para hacer las gráficas interactivas.
import requests              # Sirve para entrar a internet y descargar cosas 
import io                    # Ayuda a leer el texto que descargamos de internet como si fuera un archivo físico.
import time                  # Nos permite manejar el tiempo, como hacer pausas o saber la hora actual.

# ========== CONFIGURACION ==========
st.set_page_config(page_title="Monitor ESP32", layout="wide")

# Si GitHub canceló tu token por seguridad, puedes dejarlo en blanco así: "" (si tu repo es público)
TOKEN = "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" 
REPO = "saavedra990625-arch/ESP-Pruebas"
PATH = "datos/reporte_esp32.csv"
BRANCH = "main" # <--- DEBE SER MAIN
URL_RAW = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{PATH}"

# Ponemos el título principal en nuestra página web
st.title("Panel de Control en Vivo - Monitoreo ESP32")

# --- 3. FUNCIÓN PARA DESCARGAR Y PREPARAR LOS DATOS ---
def cargar_datos():
    # Creamos un "pase" usando tu TOKEN para que GitHub nos deje ver el archivo
    headers = {'Authorization': f'token {TOKEN}'}
    
    # Truco informático: Le agregamos la hora actual al final del enlace. 
    # Esto engaña a internet para que siempre descargue la versión más nueva y no una vieja guardada en memoria.
    url_sin_cache = f"{URL_RAW}?t={int(time.time())}"
    
    try: # Intentamos hacer lo siguiente:
        # Vamos a internet y traemos la información
        respuesta = requests.get(url_sin_cache, headers=headers)
        
        # El código "200" en internet significa "Todo salió perfecto"
        if respuesta.status_code == 200:
            
            # Usamos Pandas (pd) para leer el texto que descargamos.
            # sep=r'\s*;\s*' le dice: "Corta los datos cada vez que veas un punto y coma (;)"
            # names=[...] le pone título a cada columna para que sepamos qué es qué.
            df = pd.read_csv(
                io.StringIO(respuesta.text), 
                sep=r'\s*;\s*', 
                engine='python', 
                header=None, 
                names=['Fecha', 'Voltaje (V)', 'Corriente (mA)']
            )
            
            # Convertimos la columna de texto de fecha a un formato de Fecha real que Python entienda
            df['Fecha'] = pd.to_datetime(df['Fecha'])
            
            # Devolvemos la tabla de datos ordenada de más vieja a más nueva
            return df.sort_values(by='Fecha')
        else:
            # Si el código no es 200, mostramos un error rojo en la pantalla
            st.error(f"Error de conexion con GitHub: {respuesta.status_code}")
            return None
            
    except Exception as e: # Si ocurre cualquier otro desastre (como que te quedes sin internet):
        st.error(f"Excepcion al leer los datos: {e}")
        return None

# --- 4. CONSTRUCCIÓN DE LA INTERFAZ VISUAL ---

# Partimos la pantalla en dos pedazos (1 pequeño para el botón, 5 grandes para el mensaje)
col_btn, col_msg = st.columns([1, 5])

# En el pedazo pequeño ponemos un botón. 
# st.rerun() hace que toda la página web se recargue inmediatamente si lo presionas.
with col_btn:
    if st.button("Actualizar"):
        st.rerun()

# Llamamos a nuestra función de arriba para que traiga los datos y los guarde en la variable "df"
df = cargar_datos()

# Si logramos descargar los datos y la tabla no está vacía, procedemos:
if df is not None and not df.empty:
    
    # En el pedazo grande de arriba, mostramos un mensaje verde con la hora exacta del último registro
    with col_msg:
        st.success(f"Ultima registro recibido a las: {df['Fecha'].iloc[-1].strftime('%H:%M:%S')}")
    
    # --- ZONA DE GRAFICAS ---
    # Partimos la pantalla exactamente por la mitad
    grafica1, grafica2 = st.columns(2)
    
    with grafica1:
        st.subheader("Monitoreo de Voltaje (V)")
        # Creamos la gráfica de Plotly: Usamos la tabla "df", eje X es la Fecha, eje Y es el Voltaje.
        fig_vol = px.line(df, x='Fecha', y='Voltaje (V)', markers=True, template='plotly_dark')
        fig_vol.update_traces(line_color='#00f0ff') # Color azul neón
        fig_vol.update_layout(xaxis_title="Tiempo", yaxis_title="Voltaje (V)", margin=dict(l=0, r=0, t=30, b=0))
        # Dibujamos la gráfica en la página web
        st.plotly_chart(fig_vol, use_container_width=True)

    with grafica2:
        st.subheader("Monitoreo de Corriente (mA)")
        # Creamos la gráfica de Corriente
        fig_curr = px.line(df, x='Fecha', y='Corriente (mA)', markers=True, template='plotly_dark')
        fig_curr.update_traces(line_color='#ff9900') # Color naranja
        fig_curr.update_layout(xaxis_title="Tiempo", yaxis_title="Corriente (mA)", margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_curr, use_container_width=True)

    # --- ZONA DE DATOS Y DESCARGA ---
    st.divider() # Dibuja una línea horizontal separadora
    st.subheader("Ultimos 12 registros")
    
    # Agarramos la tabla completa (df), sacamos la "cola" (tail) que son las últimas 12 filas, 
    # y las ordenamos al revés para que la más nueva quede de primera.
    df_ultimos_12 = df.tail(12).sort_values(by='Fecha', ascending=False)
    
    # Dibujamos la tabla en pantalla
    st.dataframe(df_ultimos_12, use_container_width=True, hide_index=True)
    
    # Preparamos el archivo para que sea descargable
    csv = df.to_csv(index=False, sep=';').encode('utf-8')
    
    # Creamos el botón de descarga
    st.download_button(
        label="Descargar Historial Completo (CSV)",
        data=csv,
        file_name='historial_bateria_esp32.csv',
        mime='text/csv',
    )

else:
    # Si por alguna razón la tabla está vacía o falló el internet, mostramos un aviso amarillo
    st.warning("No se encontraron datos validos para procesar.")

# --- AUTO REFRESH (Actualización automática) ---
# El programa "duerme" por 120 segundos
time.sleep(120)
# Luego de los 120 segundos, obliga a la página a recargarse sola para buscar datos nuevos
st.rerun()
