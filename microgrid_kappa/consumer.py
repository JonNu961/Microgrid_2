# consumer_multired.py

from confluent_kafka import Consumer
from influxdb_client import InfluxDBClient, Point
import json
import time
from datetime import datetime, timezone

conf = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'multired-consumer',
    'auto.offset.reset': 'earliest'
}
consumer = Consumer(conf)
consumer.subscribe(['topic-solar', 'topic-eolico'])

influx = InfluxDBClient(
    url="http://localhost:8086",
    token="Qui0C7yAqzVUTWHywzaOqKp7H1wjopYvN1g-c4oy6SGXTtHIgBjqUtjTVxXCvnIaWarZcJU7ouxcacZgZOIjsg==",  
    org="mondragon"
)
write_api = influx.write_api()

buffer_solar = {}
buffer_eolico = {}

TOLERANCIA = 0.5  # Wh

print("\n[Consumer MultiRed] Iniciado y escuchando topics...\n")

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"[ERROR] Kafka: {msg.error()}")
            continue

        data = json.loads(msg.value().decode('utf-8'))
        tipo = data['tipo']
        hora = data['hora']
        key = (data['fecha'], hora)

        if tipo == "solar":
            buffer_solar[key] = data
        elif tipo == "eolico":
            buffer_eolico[key] = data

        if key in buffer_solar and key in buffer_eolico:
            oferta_s = buffer_solar.pop(key)
            oferta_e = buffer_eolico.pop(key)

            print(f"\n[Hora {hora}] Procesando ofertas para {key[0]}:")

            demanda = oferta_s['demanda']
            e_s, p_s = oferta_s['energia'], oferta_s['precio']
            e_e, p_e = oferta_e['energia'], oferta_e['precio']

            print(f"  → Solar: {e_s:.2f} Wh @ {p_s:.4f} €/Wh [{oferta_s['estrategia']}]")
            print(f"  → Eólico: {e_e:.2f} Wh @ {p_e:.4f} €/Wh [{oferta_e['estrategia']}]")

            ofertas = [("AS", e_s, p_s), ("AE", e_e, p_e)]
            full = [o for o in ofertas if o[1] >= demanda - TOLERANCIA]

            if full:
                ganador = min(full, key=lambda x: x[2])
                orden = [ganador] + [o for o in ofertas if o is not ganador]
            else:
                orden = sorted(ofertas, key=lambda x: x[2])

            restante = demanda
            entregado = {"AS": 0.0, "AE": 0.0}

            for ag, ener, _ in orden:
                if restante <= TOLERANCIA:
                    continue
                tomar = min(ener, restante)
                entregado[ag] += tomar
                restante -= tomar

            penal = round((restante * 0.01) / 2, 2) if restante > 0 else 0.0 
            bono_s = round(entregado["AS"] * 0.05, 2)
            bono_e = round(entregado["AE"] * 0.05, 2)

            print(f"  → Solar entrega {entregado['AS']:.2f} Wh, Bono: +{bono_s:.2f}€, Penal: {penal:.2f}€")
            print(f"  → Eólico entrega {entregado['AE']:.2f} Wh, Bono: +{bono_e:.2f}€, Penal: {penal:.2f}€")

            point = Point("negociacion_multired") \
                .tag("fuente", "solar") \
                .tag("estrategia", oferta_s["estrategia"]) \
                .field("energia", float(entregado["AS"])) \
                .field("precio",  float(p_s)) \
                .field("demanda", float(demanda)) \
                .field("penalizacion", float(penal)) \
                .time(datetime.now(timezone.utc))
            write_api.write(bucket="microgrid_v2", record=point)

            point = Point("negociacion_multired") \
                .tag("fuente", "eolico") \
                .tag("estrategia", oferta_e["estrategia"]) \
                .field("energia", float(entregado["AE"])) \
                .field("precio",  float(p_e)) \
                .field("demanda", float(demanda)) \
                .field("penalizacion", float(penal)) \
                .time(datetime.now(timezone.utc))
            write_api.write(bucket="microgrid_v2", record=point)

except KeyboardInterrupt:
    print("\n[Consumer MultiRed] Detenido por usuario.")
finally:
    consumer.close()