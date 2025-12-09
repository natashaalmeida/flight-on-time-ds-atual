import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb
import joblib
import os

# 1. Configurar rutas
current_dir = os.path.dirname(__file__)
data_path = os.path.join(current_dir, '../data/BrFlights2.csv')
model_path = os.path.join(current_dir, 'flight_model_v2.joblib')

print("Cargando datos...")
try:
    df = pd.read_csv(data_path, encoding='latin1', low_memory=False)
except FileNotFoundError:
    print("❌ Error: No encuentro el CSV BrFlights2.csv en la carpeta data/")
    exit()

# 2. Limpieza y Target
df = df[df['Situacao.Voo'] == 'Realizado']
cols = ['Companhia.Aerea', 'Aeroporto.Origem', 'Aeroporto.Destino', 'Partida.Prevista', 'Partida.Real']
df = df[cols].dropna()

df['Partida.Prevista'] = pd.to_datetime(df['Partida.Prevista'])
df['Partida.Real'] = pd.to_datetime(df['Partida.Real'])
df['delay_minutes'] = (df['Partida.Real'] - df['Partida.Prevista']).dt.total_seconds() / 60
df['target'] = np.where(df['delay_minutes'] > 15, 1, 0)

# 3. Feature Engineering BÁSICO (Variables que no dependen de la historia)
print("Generando variables base...")
df['hora_partida'] = df['Partida.Prevista'].dt.hour
df['dia_semana'] = df['Partida.Prevista'].dt.dayofweek
df['mes'] = df['Partida.Prevista'].dt.month
df['dia_mes'] = df['Partida.Prevista'].dt.day

# Renombrar
df = df.rename(columns={'Companhia.Aerea': 'companhia', 'Aeroporto.Origem': 'origem', 'Aeroporto.Destino': 'destino'})

# Variables calculadas al vuelo
df['es_fin_semana'] = df['dia_semana'].isin([5, 6]).astype(int)
df['es_hora_pico'] = df['hora_partida'].isin([6,7,8,9,17,18,19,20]).astype(int)
df['temporada_alta'] = df['mes'].isin([1,2,7,12]).astype(int)
df['fin_inicio_mes'] = df['dia_mes'].isin(list(range(1,6)) + list(range(26,32))).astype(int)

# ---------------------------------------------------------
# DATA LEAKAGE
# ---------------------------------------------------------
print("Separando Train y Test ANTES de calcular estadísticas...")

# A. Primero separamos
X = df.drop(columns=['target', 'Partida.Prevista', 'Partida.Real', 'delay_minutes']) # Guardamos todo temporalmente
y = df['target']

X_train_raw, X_test_raw, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# B. Calculamos estadísticas SOLO con X_train (Lo que el modelo "conoce")
# Necesitamos volver a pegar 'target' y 'delay_minutes' temporalmente a X_train para calcular medias
train_full = X_train_raw.copy()
train_full['target'] = y_train
# Recuperamos delay_minutes usando el índice (un truco para no perderlo)
train_full['delay_minutes'] = df.loc[train_full.index, 'delay_minutes']

print("Calculando estadísticas históricas (Target Encoding)...")
stats_companhia = train_full.groupby('companhia')['delay_minutes'].mean().to_dict()
stats_ruta = train_full.groupby(['origem', 'destino'])['delay_minutes'].mean().to_dict()
stats_hora = train_full.groupby('hora_partida')['target'].mean().to_dict()

# C. Aplicamos esas estadísticas a Train y a Test
# Función auxiliar para mapear con valor por defecto
def apply_stats(dataset):
    dataset = dataset.copy()
    dataset['airline_avg_delay'] = dataset['companhia'].map(stats_companhia).fillna(0)
    dataset['route_avg_delay'] = dataset.set_index(['origem', 'destino']).index.map(stats_ruta).fillna(0)
    dataset['hour_delay_rate'] = dataset['hora_partida'].map(stats_hora).fillna(0)
    return dataset

X_train = apply_stats(X_train_raw)
X_test = apply_stats(X_test_raw)  # ¡OJO! A Test le aplicamos las stats de Train. ¡Eso es legal!

# 4. Encoding
le_companhia = LabelEncoder()
le_origem = LabelEncoder()
le_destino = LabelEncoder()

# Ajustamos los encoders solo con Train
X_train['companhia_encoded'] = le_companhia.fit_transform(X_train['companhia'].astype(str))
X_train['origem_encoded'] = le_origem.fit_transform(X_train['origem'].astype(str))
X_train['destino_encoded'] = le_destino.fit_transform(X_train['destino'].astype(str))

# 5. Entrenamiento XGBoost
features_finales = [
    'companhia_encoded', 'origem_encoded', 'destino_encoded',
    'hora_partida', 'dia_semana', 'mes', 
    'es_fin_semana', 'es_hora_pico', 'temporada_alta', 'fin_inicio_mes',
    'airline_avg_delay', 'route_avg_delay', 'hour_delay_rate'
]

print("Entrenando XGBoost Optimizado (Sin Data Leakage)...")
scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
model = xgb.XGBClassifier(
    n_estimators=100, 
    max_depth=8, 
    learning_rate=0.01, 
    subsample=0.7, 
    colsample_bytree=0.8,
    scale_pos_weight=scale_pos_weight,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train[features_finales], y_train)

# 6. Guardar Todo 
artifacts = {
    'model': model,
    'features': features_finales,
    'encoders': {
        'companhia': le_companhia,
        'origem': le_origem,
        'destino': le_destino
    },
    'stats': { # Guardamos los diccionarios calculados SOLO con train
        'companhia': stats_companhia,
        'ruta': stats_ruta,
        'hora': stats_hora
    },
    'threshold': 0.53 
}

joblib.dump(artifacts, model_path)
print(f"✅ Modelo V2 (FIXED) guardado en: {model_path}")