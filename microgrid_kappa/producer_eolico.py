from confluent_kafka import Producer
import joblib
import pandas as pd
import random
import json
import time

conf = {
    'bootstrap.servers': 'localhost:9092',
}

p = Producer(conf)

wind_model = joblib.load("models/wind_model.pkl")
wind_features = list(wind_model.feature_names_in_)

df = pd.read_csv("data/data_complete.csv", parse_dates=["Date"])
df = df.dropna(subset=["demanda_W", "windspeed_100m", "windspeed_10m", "windgusts_10m"]).sort_values("Date").reset_index(drop=True)

def aplicar_estrategia(energia, estrategia):
    if estrategia == "reveal":
        return round(energia, 2)
    elif estrategia == "hide":
        return round(energia * random.uniform(0.85, 1.0), 2)
    elif estrategia == "bluffing":
        return round(energia * random.uniform(1.1, 1.3), 2)
    return round(energia, 2)

def send_offer(row):
    estrategia = random.choice(["reveal", "hide", "bluffing"])
    feats = {
        "windspeed_100m": row["windspeed_100m"],
        "windspeed_10m": row["windspeed_10m"],
        "windgusts_10m": row["windgusts_10m"]
    }
    demanda = row["demanda_W"]
    df_feat = pd.DataFrame([[feats[f] for f in wind_features]], columns=wind_features)
    pred = wind_model.predict(df_feat)[0]
    pred = max(pred, 0)
    ener = aplicar_estrategia(pred, estrategia)
    servido = min(ener, demanda)
    precio = round(servido * 0.03, 4)
    oferta = {
        "tipo": "eolico",
        "hora": row["Date"].hour,
        "fecha": str(row["Date"].date()),
        "estrategia": estrategia,
        "energia": servido,
        "precio": precio,
        "demanda": demanda
    }
    p.produce('topic-eolico', json.dumps(oferta).encode('utf-8'), callback=delivery_report)
    p.poll(0)

def delivery_report(err, msg):
    if err:
        print(f"[ERROR] {err}")
    else:
        print(f"[Producer Eólico] Oferta enviada a {msg.topic()} offset {msg.offset()}")

try:
    while True:
        for _, row in df.iterrows():
            send_offer(row)
            time.sleep(5)
except KeyboardInterrupt:
    p.flush()
    print("\n[Producer Eólico] Detenido.")
