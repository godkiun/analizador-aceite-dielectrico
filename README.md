# Analizador Dieléctrico Optoelectrónico

Sistema de diagnóstico no destructivo para la evaluación de la degradación dieléctrica en aceites de transformadores de potencia mediante espectrometría óptica y Machine Learning.

## Principio de funcionamiento

- **Sensor Óptico:** Emisión de luz a longitudes de onda específicas para medir la absorbancia y transmitancia del aceite.
- **Procesamiento de Señal:** Filtrado de ruido y acondicionamiento analógico mediante amplificadores operacionales de precisión.
- **Clasificación por IA:** Modelo entrenado en Scikit-Learn que clasifica el estado del dieléctrico (Normal, Humedad Alta, Oxidado, Contaminado) enviando alertas de mantenimiento predictivo a la API Flask.
