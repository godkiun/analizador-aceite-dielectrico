# ==============================================================================
# SCRIPT DE ENTRENAMIENTO DE MACHINE LEARNING: CLASIFICACIÓN DE ACEITE
# Script Principal (entrenar_modelo.py)
# ==============================================================================

# Importamos la biblioteca estándar 'sqlite3' para conectar y consultar nuestra base de datos.
import sqlite3

# Importamos la biblioteca 'pandas' para cargar la consulta SQL y convertirla en una estructura de datos DataFrame.
import pandas as pd

# Importamos 'train_test_split' de scikit-learn, el cual divide de forma aleatoria nuestro dataset en conjuntos de entrenamiento y prueba.
from sklearn.model_selection import train_test_split

# Importamos 'DecisionTreeClassifier' de scikit-learn, que es el algoritmo de árbol de decisión para clasificación supervisada.
from sklearn.tree import DecisionTreeClassifier

# Importamos 'accuracy_score' de scikit-learn para calcular el porcentaje de predicciones correctas sobre el conjunto de test.
from sklearn.metrics import accuracy_score

# Importamos 'joblib', que nos permite guardar (serializar) el objeto del modelo entrenado de Python en un archivo físico (.pkl).
import joblib

def entrenar_modelo():
    """
    Función principal que ejecuta el pipeline de Machine Learning:
    Carga de datos -> Conteo de Clases -> Preparación -> División -> Entrenamiento -> Evaluación -> Almacenamiento.
    """
    # 1. Establecemos la conexión de lectura con la base de datos SQLite 'lecturas_aceite.db'.
    conn = sqlite3.connect('lecturas_aceite.db')
    
    # 2. Definimos la consulta SQL para extraer únicamente los voltajes y las etiquetas.
    # Excluimos los registros que tengan "Sin Etiqueta", ya que en el aprendizaje supervisado
    # necesitamos que cada entrada de entrenamiento (voltaje) tenga su clase objetivo real definida.
    query = "SELECT voltaje, etiqueta FROM datos_sensor WHERE etiqueta != 'Sin Etiqueta'"
    
    # Ejecutamos la consulta y depositamos el resultado directamente en un DataFrame de Pandas.
    df = pd.read_sql_query(query, conn)
    
    # Cerramos la conexión con la base de datos para no bloquear el archivo.
    conn.close()
    
    # 3. Validación de datos: Comprobamos si el DataFrame contiene información suficiente.
    # Si la base de datos está vacía o no tiene lecturas etiquetadas, el flujo de entrenamiento no puede continuar.
    if df.empty:
        print("[ERROR] La base de datos no contiene registros etiquetados para entrenar.")
        print("        Por favor, ejecute app.py, capture datos y asigne etiquetas antes de entrenar el modelo.")
        return
        
    # Después de cargar tu dataframe df
    # Esto tomará solo 100 muestras aleatorias de cada categoría para que el modelo sea justo
    df = df.groupby('etiqueta').sample(n=100, replace=True)
        
    # Validamos que haya al menos 2 registros para poder realizar una división de datos (entrenamiento y prueba).
    if len(df) < 2:
        print("[ERROR] Se necesitan al menos 2 registros etiquetados para poder dividir y entrenar el modelo.")
        return
        
    # 4. Separación de Variables Independientes (X) y Dependientes (y):
    # - X: Características de entrada (Features). Usamos doble corchete [['voltaje']] para asegurar que X sea
    #      un DataFrame bidimensional (matriz), requerimiento estricto de scikit-learn.
    X = df[['voltaje']]
    
    # - y: Variable objetivo o clase que queremos predecir (Label). Es una Serie unidimensional (vector).
    y = df['etiqueta']

    # Validamos que tengamos al menos 2 clases distintas en los datos de entrenamiento
    if y.nunique() < 2:
        print("[ERROR] Se necesitan al menos 2 clases distintas etiquetadas para entrenar el modelo.")
        print(f"        Actualmente solo se encuentra la clase: '{y.unique()[0]}'.")
        print("        Por favor, capture y etiquete otras categorías en el panel de laboratorio antes de entrenar.")
        return
        
    print(f"[*] Registros aptos para entrenamiento encontrados: {len(df)}")
    
    # Conteo de muestras por cada clase antes de iniciar el entrenamiento, usando value_counts() de pandas
    print("[*] Distribución de muestras por clase (value_counts):")
    conteos = y.value_counts()
    for clase, count in conteos.items():
        print(f"    - {clase}: {count} muestras")
    
    # 5. División del conjunto de datos (Train/Test Split):
    # Dividimos los datos en:
    # - Entrenamiento (70%): Usado para que el árbol aprenda los umbrales de voltaje.
    # - Prueba (30%): Usado para evaluar la capacidad de generalización del modelo frente a datos que no ha visto.
    # - random_state=42: Semilla de reproducibilidad.
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    
    # 6. Instanciación del Modelo de Clasificación:
    # Añadimos los parámetros max_depth=3 y min_samples_split=5 para evitar sobreajuste y
    # garantizar un árbol más generalizable y simple.
    modelo = DecisionTreeClassifier(max_depth=3, min_samples_split=5, random_state=42)
    
    # 7. Entrenamiento del Modelo (Ajuste / Fit):
    # El algoritmo analiza las características de entrenamiento (X_train) y sus etiquetas correctas (y_train)
    # construyendo las reglas lógicas de decisión (ej: "si voltaje > 3.2, entonces Aceite Optimo").
    modelo.fit(X_train, y_train)
    print("[*] Entrenamiento del Árbol de Decisión completado.")
    
    # 8. Evaluación del Modelo (Predicción y Métricas):
    # Usamos el conjunto de prueba (X_test) para hacer predicciones y guardamos los resultados en y_pred.
    y_pred = modelo.predict(X_test)
    
    # Evaluamos la exactitud (Accuracy)
    precision = accuracy_score(y_test, y_pred)
    print(f"[+] Precisión del Modelo (Accuracy): {precision * 100:.2f}%")
    
    # 9. Serialización y Almacenamiento del Modelo:
    # Usamos joblib.dump para guardar el objeto del modelo entrenado en 'modelo_aceite.pkl'.
    joblib.dump(modelo, 'modelo_aceite.pkl')
    print("[*] Archivo de modelo serializado guardado exitosamente como 'modelo_aceite.pkl'.")

if __name__ == '__main__':
    # Punto de entrada de ejecución del script.
    entrenar_modelo()
