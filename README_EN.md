# Low-Cost Optoelectronic Dielectric Oil Analyzer ⚡🔬

Machine Learning-powered optoelectronic embedded diagnostic system designed to evaluate degradation levels in transformer dielectric oils.

---

## 🔬 Overview
The system utilizes optoelectronic sensors to measure optical absorbance and transmittance in dielectric oil samples. A **Machine Learning** model classifies oil degradation in real time.

### 🌟 Components:
* **Hardware & Simulation:** Proteus VSM project (`.pdsprj`) and PIC microcontroller C code (`PIC/`).
* **Machine Learning:** Supervised classification model (`modelo_aceite.pkl`, `entrenar_modelo.py`).
* **Database:** SQLite storage (`lecturas_aceite.db`).
* **Web Dashboard:** Interactive web interface (`app.py`).

---

## 🚀 Usage

```bash
git clone https://github.com/godkiun/analizador-aceite-dielectrico.git
cd analizador-aceite-dielectrico
pip install -r requirements.txt
python app.py
```
