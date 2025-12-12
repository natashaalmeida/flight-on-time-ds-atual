import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import os
import holidays  # <--- Importante

app = FastAPI(title="FlightOnTime AI Service (V3)")

# --- 1. CARGA ---
MODEL_FILENAME = "flight_classifier_mvp.joblib"
current_dir = os.path.dirname(__file__)
model_path = os.path.join(current_dir, MODEL_FILENAME)

artifacts = None
br_holidays = holidays.Brazil() # Cargar calendario una vez al inicio

try:
    artifacts = joblib.load(model_path)
    model = artifacts['model']
    encoders = artifacts['encoders']
    expected_features = artifacts.get('features', [])
    # Leer el threshold del metadata si existe, sino usar 0.40 por defecto
    THRESHOLD = artifacts.get('metadata', {}).get('threshold', 0.40)
    
    print(f"✅ Modelo V3 carregado. Features esperadas: {len(expected_features)}")
    print(f"⚙️ Threshold de decisão: {THRESHOLD}")
except Exception as e:
    print(f"⚠️ Erro crítico carregando modelo: {e}")
    THRESHOLD = 0.40

# --- 2. INPUT ---
class FlightInput(BaseModel):
    companhia: str
    origem: str
    destino: str
    data_partida: str
    distancia_km: float

# --- 3. HELPER ---
def safe_encode(encoder, value):
    try:
        return int(encoder.transform([str(value)])[0])
    except:
        return 0 

# --- 4. ENDPOINT ---
@app.post("/predict")
def predict_flight(flight: FlightInput):
    if not artifacts:
        raise HTTPException(status_code=500, detail="Modelo não carregado")

    try:
        # A. Processar Data e Feriado
        dt = pd.to_datetime(flight.data_partida)
        is_holiday = 1 if dt in br_holidays else 0 # Cálculo automático

        # B. Criar DataFrame
        input_data = pd.DataFrame([{
            'companhia_encoded': safe_encode(encoders['companhia'], flight.companhia),
            'origem_encoded': safe_encode(encoders['origem'], flight.origem),
            'destino_encoded': safe_encode(encoders['destino'], flight.destino),
            'distancia_km': float(flight.distancia_km),
            'hora': dt.hour,
            'dia_semana': dt.dayofweek,
            'mes': dt.month,
            'is_holiday': is_holiday # <--- Nova feature entrando no modelo
        }])
        
        # Garantir ordem das colunas
        if expected_features:
            input_data = input_data[expected_features]
        
        # C. Predição
        prob = float(model.predict_proba(input_data)[0][1])
        
        # D. Lógica de Semáforo (Usando o Threshold do Metadata)
        if prob < THRESHOLD:
            status = "PONTUAL"
            risco = "BAIXO"
            msg = "Voo com boas condições operacionais."
        elif THRESHOLD <= prob < 0.60:
            status = "ALERTA"
            risco = "MEDIO"
            msg = "Risco moderado devido a condições operacionais (ex: feriado/horário)."
        else:
            status = "ATRASADO"
            risco = "ALTO"
            msg = f"Alta probabilidade de atraso ({prob:.1%})."

        return {
            "previsao": status,
            "probabilidade": round(prob, 4),
            "nivel_risco": risco,
            "mensagem": msg,
            "detalles": {
                "is_feriado": bool(is_holiday), # Devolvemos esto para que el Frontend sepa por qué
                "distancia": flight.distancia_km
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)