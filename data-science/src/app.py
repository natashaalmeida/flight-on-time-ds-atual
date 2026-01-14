# data-science/src/app.py
import joblib
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
import os
import holidays
import requests
from datetime import datetime

app = FastAPI(title="FlightOnTime AI Service (V5.0 Live Weather)")

# --- CONFIGURAÇÃO CORS ---
# Permite que qualquer origem conecte (necessário para testes de front-end)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Aceita tudo
    allow_credentials=True,
    allow_methods=["*"], # Aceita GET, POST, OPTIONS, etc.
    allow_headers=["*"], # Aceita todos os headers
)

# --- CARGA ROBUSTA ---
current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, "flight_classifier_v4.joblib")

model = None
features_list = []
airport_coords = {}
THRESHOLD = 0.35

# Função Haversine
def calculate_distance(lat1, lon1, lat2, lon2):
    r = 6371
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda/2)**2
    return r * 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))

# --- NOVA FUNÇÃO: FETCH WEATHER ---
def get_live_weather(lat, long, date_time_str):
    """
    Consulta OpenMeteo para a data/hora específica.
    Retorna (precipitation, wind_speed)
    """
    try:
        dt = pd.to_datetime(date_time_str)
        date_str = dt.strftime('%Y-%m-%d')
        hour = dt.hour
        
        # OpenMeteo Endpoint
        # Nota: Pedimos timezone Sao_Paulo para alinhar com a API, 
        # mas a hora de entrada já está alinhada com o modelo.
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={long}&hourly=precipitation,wind_speed_10m&start_date={date_str}&end_date={date_str}&timezone=UTC"
        response = requests.get(url, timeout=3) # Timeout curto para não travar a API
        if response.status_code == 200:
            data = response.json()
            # O OpenMeteo retorna lista por horas (0 a 23). Pegamos o índice da hora do voo.
            if 'hourly' in data:
                precip = data['hourly']['precipitation'][hour]
                wind = data['hourly']['wind_speed_10m'][hour]
                return float(precip), float(wind), "✅ LIVE (OpenMeteo)"
    except Exception as e:
        print(f" Weather API Error: {e}")
    
    return 0.0, 5.0, " Offline/Date Limit" # Fallback se falhar ou data for longe

# Carga do Modelo
if os.path.exists(model_path):
    try:
        print(f" Carregando: {model_path}")
        artifact = joblib.load(model_path)
        model = artifact['model']
        features_list = artifact['features']
        airport_coords = artifact.get('airport_coords', {})
        meta = artifact.get('metadata', {})
        THRESHOLD = meta.get('threshold', 0.35)
        print(f"✅ V5.0 Online | Live Weather Ready")
    except Exception as e:
        print(f" Erro fatal: {e}")
else:
    print(f" Modelo não encontrado.")

class FlightInput(BaseModel):
    companhia: str
    origem: str
    destino: str
    data_partida: str
    distancia_km: Optional[float] = None
    # Clima agora é opcional, pois tentaremos buscar sozinhos
    precipitation: Optional[float] = None
    wind_speed: Optional[float] = None

@app.post("/predict")
def predict(flight: FlightInput):
    if not model: raise HTTPException(status_code=503, detail="Service Unavailable")
    
    try:
        # 1. Distância Automática
        dist_final = flight.distancia_km
        orig_lat, orig_long = 0, 0
        
        if flight.origem in airport_coords:
            orig_lat = airport_coords[flight.origem]['lat']
            orig_long = airport_coords[flight.origem]['long']

        if dist_final is None or dist_final == 0:
            if flight.origem in airport_coords and flight.destino in airport_coords:
                dest = airport_coords[flight.destino]
                dist_final = calculate_distance(orig_lat, orig_long, dest['lat'], dest['long'])
            else:
                dist_final = 800.0

        # 2. CLIMA AUTOMÁTICO (A GRANDE MUDANÇA)
        precip_final = flight.precipitation
        wind_final = flight.wind_speed
        weather_source = "Manual Input"

        # Se o usuário NÃO mandou clima, nós buscamos
        if precip_final is None and wind_final is None:
            if orig_lat != 0:
                # Buscamos o clima na ORIGEM (onde o voo decola é o mais crítico)
                p, w, source = get_live_weather(orig_lat, orig_long, flight.data_partida)
                precip_final = p
                wind_final = w
                weather_source = source
            else:
                precip_final, wind_final = 0.0, 5.0
                weather_source = "No Coords Found"
        else:
            # Se o usuário mandou algo, usamos (mas garantimos que não seja None)
            precip_final = precip_final if precip_final is not None else 0.0
            wind_final = wind_final if wind_final is not None else 5.0

        # 3. Pipeline ML
        dt = pd.to_datetime(flight.data_partida)
        is_holiday = 1 if dt.date() in holidays.Brazil() else 0
        
        input_df = pd.DataFrame([{
            'companhia': str(flight.companhia),
            'origem': str(flight.origem),
            'destino': str(flight.destino),
            'distancia_km': float(dist_final),
            'hora': dt.hour,
            'dia_semana': dt.dayofweek,
            'mes': dt.month,
            'is_holiday': is_holiday,
            'precipitation': float(precip_final),
            'wind_speed': float(wind_final),
            'clima_imputado': 0
        }])
        
        if features_list:
            input_df = input_df[features_list]
        
        prob = float(model.predict_proba(input_df)[0][1])
        
        if prob < THRESHOLD:
            status, color = "🟢 PONTUAL", "green"
        elif prob < 0.70:
            status, color = "🟡 ALERTA", "yellow"
        else:
            status, color = "🔴 ATRASO PROVÁVEL", "red"
            
        return {
            "previsao": status,
            "probabilidade": round(prob, 4),
            "cor": color,
            "dados_utilizados": {
                "distancia": round(dist_final, 1),
                "chuva": precip_final,
                "vento": wind_final,
                "fonte_clima": weather_source
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)