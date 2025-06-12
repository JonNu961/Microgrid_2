# agente_consumo.py

import socket, random, pandas as pd
from fipa_acl import create_message, parse_message

HOST        = "localhost"
PORT_SOLAR  = 8001
PORT_EOLICO = 8002
TOLERANCIA  = 0.5             # Wh

# helpers de red
def solicitar(host, port, msg):
    with socket.socket() as s:
        s.connect((host, port))
        s.sendall(msg.encode())
        data = s.recv(4096).decode()
    return parse_message(data)

def avisar(host, port, msg):
    with socket.socket() as s:
        s.connect((host, port))
        s.sendall(msg.encode())

# simulación de un día
def simular_dia_aleatorio():
    df = pd.read_csv("data_complete.csv", parse_dates=["Date"])

    # elegir sólo días con todos los datos necesarios
    df["Day"] = df["Date"].dt.floor("D")
    dias_validos = (
        df.dropna(subset=["demanda_W", "Radiation_FV", "windspeed_100m"])
          .groupby("Day").size().index
    )
    if dias_validos.empty:
        print("No hay días completos con datos válidos.")
        return

    dia   = random.choice(dias_validos)
    fecha = pd.to_datetime(dia).date()
    df_d  = df[df["Day"] == dia].reset_index(drop=True)

    print(f"\n=== Simulando día aleatorio: {fecha} ===\n")
    log = []

    for h, row in df_d.iterrows():
        demanda   = row["demanda_W"]
        hora_real = row["Date"].hour
        periodo   = "dia" if 6 <= hora_real <= 18 else "noche"

        estr_s = random.choice(["reveal", "hide", "bluffing"])
        estr_e = random.choice(["reveal", "hide", "bluffing"])

        print(f"[Hora {h:02d} – {periodo}] Demanda: {demanda:.1f} Wh | "
              f"Solar: {estr_s}  Eólico: {estr_e}")

        # pedir ofertas
        req_s = create_message("request","AC","AS",{
            "estrategia":estr_s,
            "features":{"Radiation":row["Radiation_FV"],"Sunshine":row["Sunshine_FV"]},
            "demanda":demanda})
        prop_s = solicitar(HOST, PORT_SOLAR, req_s)
        e_s, p_s = prop_s["content"]["energia"], prop_s["content"]["precio"]
        print(f"  → AS propone {e_s:.2f} Wh @ {p_s:.4f} €/Wh")

        req_e = create_message("request","AC","AE",{
            "estrategia":estr_e,
            "features":{
                "windspeed_100m":row["windspeed_100m"],
                "windspeed_10m": row["windspeed_10m"],
                "windgusts_10m":row["windgusts_10m"]},
            "demanda":demanda})
        prop_e = solicitar(HOST, PORT_EOLICO, req_e)
        e_e, p_e = prop_e["content"]["energia"], prop_e["content"]["precio"]
        print(f"  → AE propone {e_e:.2f} Wh @ {p_e:.4f} €/Wh")

        ofertas = [("AS", e_s, p_s, PORT_SOLAR),
                   ("AE", e_e, p_e, PORT_EOLICO)]

        # regla de prioridad
        full   = [o for o in ofertas if o[1] >= demanda - TOLERANCIA]
        if full:                                  # alguien cubre todo
            ganador = min(full, key=lambda x:x[2])          # menor €/Wh
            orden   = [ganador] + [o for o in ofertas if o is not ganador]
        else:                                     # nadie cubre → ordenar por €/Wh
            orden   = sorted(ofertas, key=lambda x:x[2])

        restante   = demanda
        entregado  = {"AS":0.0, "AE":0.0}
        aceptado   = {"AS":False, "AE":False}

        for ag, ener, _, port in orden:
            if restante <= TOLERANCIA:
                avisar(HOST, port,
                       create_message("reject-proposal","AC",ag,
                                      {"motivo":"demanda cubierta"}))
                print(f"    → {ag} recibe propuesta-rechazada")
                continue

            tomar = min(ener, restante)
            avisar(HOST, port,
                   create_message("accept-proposal","AC",ag,{"energia":tomar}))
            print(f"    → {ag} recibe propuesta-aceptada")
            entregado[ag] += tomar
            aceptado[ag]   = True
            restante      -= tomar

        # penalizaciones / beneficios
        penal = round((restante*0.01)/2, 2) if restante > 0 else 0
        if penal:
            for ag, port in [("AS",PORT_SOLAR), ("AE",PORT_EOLICO)]:
                avisar(HOST, port,
                       create_message("inform","AC",ag,{"penalizacion":penal}))
            print(f"  → PENALIZACIÓN {penal:.2f} € a AS y AE")

        for ag, port in [("AS",PORT_SOLAR), ("AE",PORT_EOLICO)]:
            if aceptado[ag]:
                bono = round(entregado[ag]*0.05, 2)
                avisar(HOST, port,
                       create_message("inform","AC",ag,{"beneficio":bono}))
                print(f"  → BENEFICIO +{bono:.2f} € a {ag}")

        # registro
        log.append({
            "dia":fecha,"hora":h,"periodo":periodo,
            "estr_solar":estr_s,"estr_eolico":estr_e,
            "demanda_wh":demanda,
            "energia_solar":entregado["AS"],"precio_solar":p_s,
            "energia_eolico":entregado["AE"],"precio_eolico":p_e,
            "acepta_solar":aceptado["AS"],"acepta_eolico":aceptado["AE"],
            "restante_wh":restante,"penalizacion":penal
        })

    # guardar CSV
    pd.DataFrame(log).to_csv(f"resultado_sim_{fecha}.csv", index=False)
    print(f"\n[Simulación completada] Guardado en 'resultado_sim_{fecha}.csv'")

#
if __name__ == "__main__":
    simular_dia_aleatorio()
