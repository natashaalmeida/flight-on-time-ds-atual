import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import recall_score, accuracy_score
import joblib
import holidays
import os
from catboost import CatBoostClassifier

# --- FUNCIONES AUXILIARES ---
def haversine_distance(lat1, lon1, lat2, lon2):
    r = 6371
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)
    a = np.sin(delta_phi / 2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2)**2
    return r * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

# --- CONFIGURACIÓN ---
print(" Iniciando Pipeline de Treinamento V3.0-CAT (Produção)...")
current_dir = os.path.dirname(__file__)
data_path = os.path.join(current_dir, '../data/BrFlights2.csv') 
model_path = os.path.join(current_dir, 'flight_classifier_mvp.joblib')

# 1. CARGA
if not os.path.exists(data_path):
    print(f" Erro: Arquivo não encontrado em {data_path}")
    exit()

df = pd.read_csv(data_path, encoding='latin1', low_memory=False)

# 2. LIMPEZA E PREPARAÇÃO
df.drop_duplicates(inplace=True)
for col in ['LatOrig', 'LongOrig', 'LatDest', 'LongDest']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

df = df[df['Situacao.Voo'] == 'Realizado'].dropna(subset=['Partida.Prevista', 'Partida.Real', 'Chegada.Real'])

# 3. FEATURE ENGINEERING
df['distancia_km'] = haversine_distance(df['LatOrig'], df['LongOrig'], df['LatDest'], df['LongDest'])

for col in ['Partida.Prevista', 'Partida.Real', 'Chegada.Real']:
    df[col] = pd.to_datetime(df[col], errors='coerce')
df.dropna(subset=['distancia_km', 'Partida.Prevista'], inplace=True)

# Outliers
df['delay_minutes'] = (df['Partida.Real'] - df['Partida.Prevista']).dt.total_seconds() / 60
df['duration_minutes'] = (df['Chegada.Real'] - df['Partida.Real']).dt.total_seconds() / 60
mask_clean = (df['duration_minutes'] > 0) & (df['delay_minutes'] > -60) & (df['delay_minutes'] < 1440)
df = df[mask_clean].copy()

# Feriados (Lógica Otimizada .date)
br_holidays = holidays.Brazil()
df['data_voo'] = df['Partida.Prevista'].dt.date
df['is_holiday'] = df['data_voo'].apply(lambda x: 1 if x in br_holidays else 0)

# Temporais
df['hora'] = df['Partida.Prevista'].dt.hour
df['dia_semana'] = df['Partida.Prevista'].dt.dayofweek
df['mes'] = df['Partida.Prevista'].dt.month

# Target
df['target'] = np.where(df['delay_minutes'] > 15, 1, 0)

# Renomear
df.rename(columns={'Companhia.Aerea': 'companhia', 'Aeroporto.Origem': 'origem', 'Aeroporto.Destino': 'destino'}, inplace=True)

# 4. ENCODING
encoders = {}
for col in ['companhia', 'origem', 'destino']:
    le = LabelEncoder()
    df[col] = df[col].astype(str)
    df[f'{col}_encoded'] = le.fit_transform(df[col])
    encoders[col] = le

# 5. TREINO FINAL (FULL DATASET)
features_finais = ['companhia_encoded', 'origem_encoded', 'destino_encoded', 
                   'distancia_km', 'hora', 'dia_semana', 'mes', 'is_holiday']
X = df[features_finais]
y = df['target']

print(" Treinando CatBoost Classifier (Full Dataset)...")
model = CatBoostClassifier(
    iterations=100, learning_rate=0.1, depth=6,
    auto_class_weights='Balanced', random_seed=42, verbose=False, allow_writing_files=False
)
model.fit(X, y)

# 6. EXPORTAR COM METADADOS DE NEGÓCIO
# Decisão tomada no Notebook de Análise:
THRESHOLD_FINAL = 0.40 

artifact = {
    'model': model,
    'encoders': encoders,
    'features': features_finais,
    'metadata': {
        'autor': 'Time Data Science',
        'versao': '3.0.0-CAT',
        'tecnologia': 'CatBoost',
        'threshold_recomendado': THRESHOLD_FINAL,
        'nota_tecnica': 'Threshold 0.40 fixado manualmente (Business Override) para garantir Recall > 89%'
    }
}

joblib.dump(artifact, model_path)
print(f"✅ Modelo salvo em: {model_path}")
print(f" Threshold definido: {THRESHOLD_FINAL} (Priorizando Segurança)")