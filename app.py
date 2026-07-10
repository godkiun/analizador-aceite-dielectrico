# ==============================================================================
# BACKEND AUTOMATIZADO CON INFERENCIA DE IA Y RECOLECCIÓN MANUAL DE DATOS
# Script Backend Principal (app.py)
# ==============================================================================

# Importamos la biblioteca estándar 'sqlite3' para realizar operaciones sobre la base de datos local SQLite.
import sqlite3

# Importamos la biblioteca estándar 'threading' para soportar el hilo de lectura del puerto serial.
import threading

# Importamos la biblioteca estándar 'time' para pausar temporalmente los hilos y evitar bucles acelerados.
import time

# Importamos del micro-framework Flask las utilidades web requeridas:
# - Flask: Clase de la aplicación.
# - jsonify: Para formatear respuestas JSON.
# - render_template: Para servir la interfaz del dashboard.
# - request: Para recibir datos en las solicitudes de la API.
from flask import Flask, jsonify, render_template, request

# Importamos 'joblib', indispensable para cargar el archivo binario del modelo preentrenado (.pkl).
import joblib

# Importamos 'pandas' para estructurar entradas en DataFrames, evitando advertencias de compatibilidad de sklearn.
import pandas as pd

# Importamos 'serial' (PySerial) para gestionar la lectura de señales eléctricas del puerto COM2.
import serial

# ------------------------------------------------------------------------------
# CONFIGURACIÓN E INICIALIZACIÓN DE LA APLICACIÓN FLASK Y VARIABLES GLOBALES
# ------------------------------------------------------------------------------

# Creamos la instancia principal de nuestro backend web.
app = Flask(__name__)

# Definimos el nombre del archivo para almacenar las lecturas históricas.
DATABASE_NAME = 'lecturas_aceite.db'

# Restauramos la variable global estado_actual e inicializamos en "Sin Etiqueta"
# para el modo de recolección manual de datos.
estado_actual = "Sin Etiqueta"

# Intentamos cargar de forma segura el modelo de IA para uso en el hilo serial.
try:
    modelo_ia = joblib.load('modelo_aceite.pkl')
    print("[*] Modelo de IA 'modelo_aceite.pkl' cargado exitosamente.")
except FileNotFoundError:
    modelo_ia = None
    print("[!] ADVERTENCIA: No se encontró 'modelo_aceite.pkl'. Se cargará dinámicamente cuando esté listo.")


# ------------------------------------------------------------------------------
# SECCIÓN DE BASE DE DATOS (SQLite)
# ------------------------------------------------------------------------------

def init_db():
    """
    Crea la tabla en SQLite si no existe para almacenar voltajes y etiquetas.
    """
    # Conectamos con el archivo SQLite.
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    # Creamos la tabla 'datos_sensor' con las columnas: id, voltaje, etiqueta y timestamp.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS datos_sensor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voltaje REAL NOT NULL,
            etiqueta TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Aseguramos que los cambios queden aplicados.
    conn.commit()
    
    # Liberamos la base de datos.
    conn.close()
    
    print(f"[*] Base de datos '{DATABASE_NAME}' inicializada correctamente.")


# ------------------------------------------------------------------------------
# HILO DE LECTURA SERIAL CON MANEJO DUAL
# ------------------------------------------------------------------------------

def read_serial_port():
    """
    Hilo secundario que adquiere datos en tiempo real de COM2,
    y guarda en SQLite tanto el voltaje leído como la etiqueta (ya sea manual o predicción de IA).
    Mantiene bloques try-except para asegurar máxima estabilidad ante fallos de conexión física.
    """
    global estado_actual, modelo_ia
    print("[*] Hilo secundario de lectura en puerto serial COM2 activo.")
    
    ultimo_control_modelo = 0
    
    # Bucle de reconexión para fallas físicas de conexión del hardware serial.
    while True:
        try:
            # Abrimos el puerto de comunicación serial COM2 a 9600 baudios.
            ser = serial.Serial('COM2', 9600, timeout=1)
            print("[+] Puerto COM2 conectado de manera exitosa.")
            
            # Limpiamos el buffer físico para descartar basura inicial acumulada.
            ser.reset_input_buffer()
            
            # Bucle de lectura activa de bytes.
            while True:
                try:
                    # Leemos los datos entrantes del buffer serial.
                    raw_data = ser.readline()
                    
                    if raw_data:
                        # Decodificamos omitiendo caracteres no-ASCII basura para mantener la estabilidad.
                        clean_data = raw_data.decode('utf-8', errors='ignore').strip()
                        
                        if clean_data:
                            # Parseamos la lectura de texto a valor flotante.
                            voltaje = float(clean_data)
                            
                            # Manejo Dual:
                            # Si estado_actual es "Sin Etiqueta", usamos la IA en tiempo real.
                            # Para evitar lecturas constantes de disco, intentamos recargar/cargar el modelo cada 5 segundos.
                            etiqueta_a_guardar = estado_actual
                            if estado_actual == "Sin Etiqueta":
                                ahora = time.time()
                                if ahora - ultimo_control_modelo > 5:
                                    try:
                                        modelo_ia = joblib.load('modelo_aceite.pkl')
                                    except Exception:
                                        pass
                                    ultimo_control_modelo = ahora
                                    
                                if modelo_ia is not None and len(getattr(modelo_ia, 'classes_', [])) >= 2:
                                    try:
                                        df_input = pd.DataFrame([[voltaje]], columns=['voltaje'])
                                        etiqueta_a_guardar = str(modelo_ia.predict(df_input)[0])
                                    except Exception:
                                        etiqueta_a_guardar = "Sin Etiqueta"
                                else:
                                    # Fallback a reglas lógicas de umbral si el modelo no tiene suficientes clases o no existe
                                    if voltaje > 3.4:
                                        etiqueta_a_guardar = "Aceite Optimo"
                                    elif voltaje >= 1.8:
                                        etiqueta_a_guardar = "Aceite Degradado"
                                    else:
                                        etiqueta_a_guardar = "Falla - Carbonizado"
                            
                            # Almacenamos el registro en SQLite encapsulando la operación en un try-except local.
                            try:
                                conn = sqlite3.connect(DATABASE_NAME)
                                cursor = conn.cursor()
                                cursor.execute(
                                    'INSERT INTO datos_sensor (voltaje, etiqueta) VALUES (?, ?)',
                                    (voltaje, etiqueta_a_guardar)
                                )
                                conn.commit()
                                conn.close()
                                
                                print(f"[SERIAL] Guardado: {voltaje} V | Etiqueta: '{etiqueta_a_guardar}'")
                                
                            except sqlite3.Error as db_err:
                                print(f"[DATABASE ERROR] Falla al insertar registro: {db_err}")
                                
                except (ValueError, UnicodeDecodeError) as parse_err:
                    # Ignoramos interferencias eléctricas o tramas incompletas que no sean flotantes puros.
                    print(f"[SERIAL WARNING] Basura serial ignorada: {parse_err}")
                
                # Pausa de 100 ms para moderar el consumo del hilo.
                time.sleep(0.1)
                
        except serial.SerialException as ser_err:
            # Reporta problemas de apertura física (ej. COM2 ocupado o ausente).
            print(f"[SERIAL ERROR] Error en puerto COM2: {ser_err}")
            print("[*] Reintentando conectar en 5 segundos...")
            time.sleep(5)


# ------------------------------------------------------------------------------
# RUTAS DE FRONTEND
# ------------------------------------------------------------------------------

@app.route('/')
def index():
    """
    Retorna la plantilla 'index.html' (Modo Producción / Dashboard IA).
    """
    return render_template('index.html')


@app.route('/laboratorio')
def laboratorio():
    """
    Retorna la plantilla 'laboratorio.html' (Modo Recolección / Datos Manuales).
    """
    return render_template('laboratorio.html')


# ------------------------------------------------------------------------------
# RUTAS DE BACKEND (API REST)
# ------------------------------------------------------------------------------

@app.route('/api/datos_recientes', methods=['GET'])
def get_datos_recientes():
    """
    Se mantiene igual: retorna los últimos 20 registros recopilados en base de datos.
    Estructurado en JSON cronológico ascendente.
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        query = "SELECT id, voltaje, etiqueta, timestamp FROM datos_sensor ORDER BY id DESC LIMIT 20"
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            return jsonify([]), 200
            
        # Invertimos el orden para conservar la secuencia temporal de las lecturas.
        df_cronologico = df.iloc[::-1]
        
        # Convertimos la salida a una lista de diccionarios de Python y la retornamos.
        return jsonify(df_cronologico.to_dict(orient='records')), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/set_etiqueta', methods=['POST'])
def set_etiqueta():
    """
    Ruta POST que recibe una etiqueta y actualiza la variable global estado_actual.
    """
    global estado_actual
    
    # Obtenemos la etiqueta de la solicitud (soportando JSON, Form data, o Query Args)
    nueva_etiqueta = None
    if request.is_json:
        data = request.get_json(silent=True)
        if data:
            nueva_etiqueta = data.get('etiqueta')
    if not nueva_etiqueta:
        nueva_etiqueta = request.form.get('etiqueta')
    if not nueva_etiqueta:
        nueva_etiqueta = request.args.get('etiqueta')
        
    if nueva_etiqueta is not None:
        estado_actual = str(nueva_etiqueta).strip()
        print(f"[*] Etiqueta de recolección manual actualizada a: '{estado_actual}'")
        return jsonify({"status": "success", "estado_actual": estado_actual}), 200
    else:
        return jsonify({"status": "error", "message": "No se recibió el campo 'etiqueta'."}), 400


@app.route('/api/estado_ia', methods=['GET'])
def get_estado_ia():
    """
    Endpoint de Inferencia de IA.
    Consulta el voltaje más reciente en base de datos, carga modelo_aceite.pkl con joblib,
    ejecuta la predicción y retorna el resultado en formato JSON.
    """
    try:
        # Cargamos el modelo modelo_aceite.pkl con joblib en cada petición para que refleje
        # de inmediato cualquier reentrenamiento del modelo.
        try:
            modelo_ia_local = joblib.load('modelo_aceite.pkl')
        except FileNotFoundError:
            return jsonify({
                "status": "error", 
                "message": "El modelo 'modelo_aceite.pkl' no está cargado o no existe. Ejecute entrenar_modelo.py primero."
            }), 500
            
        # Obtenemos la última lectura de voltaje registrada.
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT voltaje FROM datos_sensor ORDER BY id DESC LIMIT 1")
        fila = cursor.fetchone()
        conn.close()
        
        # Validamos que existan lecturas en la base de datos.
        if not fila:
            return jsonify({
                "status": "error", 
                "message": "No hay lecturas registradas para realizar la inferencia."
            }), 404
            
        # Extraemos el valor flotante de voltaje de la consulta.
        voltaje_reciente = fila[0]
        
        # Estructuramos la entrada en un DataFrame con nombres de columnas idénticas al entrenamiento
        # para neutralizar los warnings de Scikit-Learn.
        df_entrada = pd.DataFrame([[voltaje_reciente]], columns=['voltaje'])
        
        # Realizamos la inferencia y obtenemos la predicción del tipo de aceite.
        # Fallback a reglas de umbral si el modelo no tiene suficientes clases (por ejemplo, si se entrenó
        # con una sola categoría temporalmente).
        if len(getattr(modelo_ia_local, 'classes_', [])) >= 2:
            prediccion = str(modelo_ia_local.predict(df_entrada)[0])
        else:
            if voltaje_reciente > 3.4:
                prediccion = "Aceite Optimo"
            elif voltaje_reciente >= 1.8:
                prediccion = "Aceite Degradado"
            else:
                prediccion = "Falla - Carbonizado"
        
        # Retornamos el JSON con el voltaje actual y la predicción generada automáticamente por la IA.
        return jsonify({
            "voltaje": voltaje_reciente,
            "prediccion": prediccion
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ------------------------------------------------------------------------------
# PUNTO DE ENTRADA PRINCIPAL DE LA APLICACIÓN
# ------------------------------------------------------------------------------

if __name__ == '__main__':
    # 1. Aseguramos la existencia y consistencia de la base de datos relacional SQLite.
    init_db()
    
    # 2. Iniciamos el hilo de lectura y almacenamiento serial en segundo plano.
    hilo_serial = threading.Thread(target=read_serial_port, daemon=True)
    hilo_serial.start()
    
    # 3. Iniciamos el servidor de Flask con la configuración exacta especificada.
    # El uso de 'use_reloader=False' evita duplicación de procesos y colisiones con el puerto COM2.
    app.run(debug=True, host='0.0.0.0', use_reloader=False)
