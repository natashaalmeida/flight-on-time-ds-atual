import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import recall_score, accuracy_score
import joblib
import holidays
import os

# --- FUNCIONES AUXILIARES ---
def haversine_distance(lat1, lon1, lat2, lon2):
    r = 6371
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)
    a = np.sin(delta_phi / 2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2)**2
    return r * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

def eh_feriado(data, calendario):
    return 1 if data in calendario else 0

# --- CONFIGURACIÓN ---
print("🚀 Iniciando treinamento V4 (Limpeza Avançada + Outliers)...")
current_dir = os.path.dirname(__file__)
data_path = os.path.join(current_dir, '../data/BrFlights2.csv')
model_path = os.path.join(current_dir, 'flight_classifier_mvp.joblib')

# 1. CARGA
try:
    df = pd.read_csv(data_path, encoding='latin1', low_memory=False)
except FileNotFoundError:
    print("❌ Erro: BrFlights2.csv não encontrado.")
    exit()

# 2. LIMPIEZA INICIAL (NUEVO)
print(f"📊 Registros iniciais: {len(df)}")
df.drop_duplicates(inplace=True)
print(f"📉 Após remover duplicados: {len(df)}")

df = df[df['Situacao.Voo'] == 'Realizado'].dropna(subset=['Partida.Prevista', 'Partida.Real', 'Chegada.Real', 'LatOrig', 'LongDest'])

# 3. FEATURE ENGINEERING
print("⚙️ Criando features e limpando outliers...")

# A. Distância
df['distancia_km'] = haversine_distance(df['LatOrig'], df['LongOrig'], df['LatDest'], df['LongDest'])

# B. Datas e Tempos
cols_datas = ['Partida.Prevista', 'Partida.Real', 'Chegada.Real']
for col in cols_datas:
    df[col] = pd.to_datetime(df[col], errors='coerce')

# Remover falhas de conversão de data
df = df.dropna(subset=cols_datas)

# C. Cálculos para Filtros (NUEVO)
df['delay_minutes'] = (df['Partida.Real'] - df['Partida.Prevista']).dt.total_seconds() / 60
df['duration_minutes'] = (df['Chegada.Real'] - df['Partida.Real']).dt.total_seconds() / 60

# D. Filtros de Consistência e Outliers (NUEVO - Igual al Notebook)
# Regra 1: Duração deve ser positiva
# Regra 2: Atraso entre -60 min (adiantado) e 1440 min (24h)
mask_clean = (df['duration_minutes'] > 0) & (df['delay_minutes'] > -60) & (df['delay_minutes'] < 1440)
df = df[mask_clean].copy()
print(f"✅ Registros limpos para treino: {len(df)}")

# E. Feriados e Outras Features
br_holidays = holidays.Brazil()
df['is_holiday'] = df['Partida.Prevista'].apply(lambda x: eh_feriado(x, br_holidays))
df['hora'] = df['Partida.Prevista'].dt.hour
df['dia_semana'] = df['Partida.Prevista'].dt.dayofweek
df['mes'] = df['Partida.Prevista'].dt.month

# F. Target (> 15 min atraso)
df['target'] = np.where(df['delay_minutes'] > 15, 1, 0)

# Renomear
df = df.rename(columns={'Companhia.Aerea': 'companhia', 'Aeroporto.Origem': 'origem', 'Aeroporto.Destino': 'destino'})

# 4. ENCODING
print("🔠 Codificando variáveis categóricas...")
encoders = {}
for col in ['companhia', 'origem', 'destino']:
    le = LabelEncoder()
    df[col] = df[col].astype(str)
    df[f'{col}_encoded'] = le.fit_transform(df[col])
    encoders[col] = le

# 5. TREINO
features = [
    'companhia_encoded', 'origem_encoded', 'destino_encoded', 
    'distancia_km', 'hora', 'dia_semana', 'mes', 'is_holiday'
]

X = df[features]
y = df['target']

print(f"🧠 Treinando Random Forest (n=100, depth=15)...")
model = RandomForestClassifier(n_estimators=100, max_depth=15, class_weight='balanced', random_state=42, n_jobs=-1)
model.fit(X, y)

# 6. EXPORTAR ARTEFATOS
print("💾 Salvando modelo V4...")
artifact = {
    'model': model,
    'encoders': encoders,
    'features': features,
    'metadata': {
        'version': '4.0',
        'desc': 'Cleaned Data + Outlier Removal',
        'threshold': 0.40, 
        'author': 'Dragos Team'
    }
}
joblib.dump(artifact, model_path)
print(f"✅ Modelo V4 salvo em: {model_path}")