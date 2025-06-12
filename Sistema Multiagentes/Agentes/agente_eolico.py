import socket
import joblib
import pandas as pd
import random
from fipa_acl import create_message, parse_message

HOST = "localhost"
PORT = 8002

wind_model = joblib.load("wind_model.pkl")
wind_features = list(wind_model.feature_names_in_)
ingresos = 0.0

def aplicar_estrategia(energia, estrategia):
    if estrategia == "reveal":
        return round(energia, 2)
    if estrategia == "hide":
        return round(energia * random.uniform(0.85, 1.0), 2)
    if estrategia == "bluffing":
        return round(energia * random.uniform(1.1, 1.3), 2)
    return round(energia, 2)

def manejar_peticion(conn):
    global ingresos
    msg = parse_message(conn.recv(2048).decode())
    pf, contenido = msg["performative"], msg["content"]

    if pf == "request":
        estr = contenido["estrategia"]
        feats = contenido["features"]
        demanda = contenido["demanda"]
        df = pd.DataFrame([[feats[f] for f in wind_features]], columns=wind_features)
        pred = wind_model.predict(df)[0]
        ener = aplicar_estrategia(pred, estr)
        servido = min(ener, demanda)
        precio = round(servido * 0.03, 4)
        ingresos += precio
        reply = create_message("propose", "AE", msg["sender"],
                               {"energia": servido, "precio": precio})
        conn.sendall(reply.encode())

    elif pf == "accept-proposal":
        print(f"[AE] Oferta aceptada por {msg['sender']}.")

    elif pf == "reject-proposal":
        motivo = contenido.get("motivo","")
        print(f"[AE] Oferta rechazada por {msg['sender']}: {motivo}")

    elif pf == "inform" and "penalizacion" in contenido:
        penal = contenido["penalizacion"]
        ingresos -= penal
        print(f"[AE] Penalización: -{penal:.2f}€ → Ingresos totales: {ingresos:.2f}€")

    elif pf == "inform" and "beneficio" in contenido:
        ben = contenido["beneficio"]
        ingresos += ben
        print(f"[AE] Beneficio: +{ben:.2f}€ → Ingresos totales: {ingresos:.2f}€")

with socket.socket() as s:
    s.bind((HOST, PORT)); s.listen()
    print("[AE] Eólico listo en puerto", PORT)
    while True:
        conn, _ = s.accept()
        with conn: manejar_peticion(conn)
