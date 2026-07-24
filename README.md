# Analizador Optoelectrónico de Aceite Dieléctrico de Bajo Costo ⚡🔬

Sistema embebido de diagnóstico optoelectrónico impulsado por Machine Learning para evaluar el nivel de degradación en aceites dieléctricos de transformadores de potencia.

---

## 🔬 Descripción
El sistema utiliza sensores optoelectrónicos para medir la absorbancia y transmitancia óptica en muestras de aceite dieléctrico. Un modelo de **Machine Learning** clasifica el estado de degradación del aceite en tiempo real.

### 🌟 Componentes:
* **Hardware & Simulación:** Proyecto de Proteus VSM (`.pdsprj`) y código C para microcontrolador PIC (`PIC/`).
* **Machine Learning:** Modelo supervisado (`modelo_aceite.pkl`, `entrenar_modelo.py`).
* **Base de Datos:** Almacenamiento SQLite (`lecturas_aceite.db`).
* **Dashboard Web:** Interfaz web interactiva (`app.py`).

---

## 🚀 Ejecución

```bash
git clone https://github.com/godkiun/analizador-aceite-dielectrico.git
cd analizador-aceite-dielectrico
pip install -r requirements.txt
python app.py
```
