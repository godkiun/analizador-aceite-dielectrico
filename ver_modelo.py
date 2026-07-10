import joblib
import matplotlib.pyplot as plt
from sklearn import tree

# 1. Cargar el "cerebro" congelado
modelo_ia = joblib.load('modelo_aceite.pkl')

# 2. Configurar el tamaño del lienzo de la gráfica
plt.figure(figsize=(10, 6))

# 3. Dibujar el mapa mental (Árbol)
# feature_names: lo que le damos de comer (Voltaje)
# class_names: las etiquetas que aprendió automáticamente
tree.plot_tree(modelo_ia, 
               feature_names=['Voltaje'],  
               class_names=modelo_ia.classes_, 
               filled=True, 
               rounded=True,
               fontsize=12)

# 4. Mostrar la ventana gráfica
plt.title("Mapa de Decisión del Analizador de Aceite")
plt.show()