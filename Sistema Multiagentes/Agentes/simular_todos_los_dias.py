# simular_todos_los_dias.py

import socket, time, random, pandas as pd
from fipa_acl import create_message, parse_message

HOST = "localhost"
PORT_SOLAR, PORT_EOLICO = 8001, 8002
TOLERANCIA = 0.5   # Wh

# utilidades de red
def solicitar(host, port, msg, retries=3):
    for _ in range(retries):
        try:
            with socket.socket() as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.connect((host, port))
                s.sendall(msg.encode())
                data = s.recv(4096).decode()
            return parse_message(data)
        except OSError:
            time.sleep(0.05)
    return None

def avisar(host, port, msg):
    try:
        with socket.socket() as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.connect((host, port))
            s.sendall(msg.encode())
    except OSError:
        pass

# simulación global
def simular_todos_los_dias():
    df = pd.read_csv("data_complete.csv", parse_dates=["Date"])

    # descartar filas con NaN en columnas críticas
    cols_chk = ["demanda_W","Radiation_FV","Sunshine_FV",
                "windspeed_100m","windspeed_10m","windgusts_10m"]
    df = df.dropna(subset=cols_chk)

    df["Day"] = df["Date"].dt.floor("D")
    dias = df["Day"].unique()

    master_log = []

    for dia in dias:
        fecha = pd.to_datetime(dia).date()
        df_d = df[df["Day"] == dia].reset_index(drop=True)
        print(f"--- Simulando día {fecha} ({len(df_d)}h) ---")

        for _, row in df_d.iterrows():
            demanda   = row["demanda_W"]
            hora_real = row["Date"].hour
            periodo   = "dia" if 6 <= hora_real <= 18 else "noche"

            estr_s = random.choice(["reveal","hide","bluffing"])
            estr_e = random.choice(["reveal","hide","bluffing"])

            # pedir ofertas
            msg_s = create_message("request","AC","AS",{
                "estrategia":estr_s,
                "features":{"Radiation":row["Radiation_FV"],"Sunshine":row["Sunshine_FV"]},
                "demanda":demanda})
            prop_s = solicitar(HOST, PORT_SOLAR, msg_s)
            if prop_s is None: continue
            e_s, p_s = prop_s["content"]["energia"], prop_s["content"]["precio"]

            msg_e = create_message("request","AC","AE",{
                "estrategia":estr_e,
                "features":{
                    "windspeed_100m":row["windspeed_100m"],
                    "windspeed_10m": row["windspeed_10m"],
                    "windgusts_10m":row["windgusts_10m"]},
                "demanda":demanda})
            prop_e = solicitar(HOST, PORT_EOLICO, msg_e)
            if prop_e is None: continue
            e_e, p_e = prop_e["content"]["energia"], prop_e["content"]["precio"]

            ofertas = [("AS",e_s,p_s,PORT_SOLAR),
                       ("AE",e_e,p_e,PORT_EOLICO)]

            # prioridad: quien cubra todo
            full = [o for o in ofertas if o[1] >= demanda - TOLERANCIA]
            if full:
                ganador = min(full, key=lambda x:x[2])      # menor €/Wh
                orden   = [ganador] + [o for o in ofertas if o is not ganador]
            else:
                orden = sorted(ofertas, key=lambda x:x[2])

            restante   = demanda
            entreg_s = entreg_e = 0.0
            acept_s = acept_e = False

            for ag, ener, _, port in orden:
                if restante <= TOLERANCIA:
                    avisar(HOST, port,
                           create_message("reject-proposal","AC",ag,
                                           {"motivo":"demanda cubierta"}))
                    continue
                tomar = min(ener, restante)
                avisar(HOST, port,
                       create_message("accept-proposal","AC",ag,{"energia":tomar}))
                if ag == "AS":
                    entreg_s += tomar; acept_s = True
                else:
                    entreg_e += tomar; acept_e = True
                restante -= tomar

            # penalización / beneficio
            penal = round((restante*0.01)/2, 2) if restante > 0 else 0.0
            if penal:
                for ag, port in [("AS",PORT_SOLAR),("AE",PORT_EOLICO)]:
                    avisar(HOST, port,
                           create_message("inform","AC",ag,{"penalizacion":penal}))

            for ag, port, entreg in [("AS",PORT_SOLAR,entreg_s),
                                     ("AE",PORT_EOLICO,entreg_e)]:
                if entreg > 0:
                    bono = round(entreg*0.05,2)
                    avisar(HOST, port,
                           create_message("inform","AC",ag,{"beneficio":bono}))

            # registro
            master_log.append({
                "dia":fecha,"hora":hora_real,"periodo":periodo,
                "estr_solar":estr_s,"estr_eolico":estr_e,
                "demanda_wh":demanda,
                "energia_solar":entreg_s,"precio_solar":p_s,
                "energia_eolico":entreg_e,"precio_eolico":p_e,
                "acepta_solar":acept_s,"acepta_eolico":acept_e,
                "restante_wh":restante,"penalizacion":penal
            })
        time.sleep(0.05)   # micro-pausa entre días

    pd.DataFrame(master_log)\
        .to_csv("resultado_simulacion_todos_los_dias.csv", index=False)
    print("\n¡Listo! Resultado en resultado_simulacion_todos_los_dias.csv")

#
if __name__ == "__main__":
    simular_todos_los_dias()
