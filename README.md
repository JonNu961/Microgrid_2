# Microgrid\_2

**Microgrid\_2** is a research sandbox that blends **multi‑agent negotiation**, **explainable forecasting**, **multi‑objective optimisation** and **real‑time visualisation** to study renewable micro‑grids with solar‑PV and wind resources.

---

## Repository layout

| Path                    | Key contents                                                                                                                                                                                                                    | Role                                                                                                             |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `Sistema_Multiagentes/` | `Agentes/` (Python classes for Solar & Wind agents and negotiation rules) · `CSV_Generados/` (logs) · `Data/` (weather & demand) · `Modelos_Entrenados/` (pre‑trained forecasters) · `Analisis.ipynb` (>8 000 simulated rounds) | Hour‑by‑hour market simulation                                                                                   |
| `moo_optimization/`     | `data/` (forecast matrices) · `models/` (Pareto fronts) · `figures/` · `data_adaptation.py` · `moo_microgrid.ipynb`                                                                                                             | Day‑ahead scheduling via NSGA‑II/III & SPEA2                                                                     |
| `microgrid_kappa/`      | `data/`, `image/`, `import_dashboard/`, `models/` · `consumer.py`, `producer_solar.py`, `producer_eolico.py` · `generacion_datos.ipynb` · `docker-compose.yml`                                                                  | Real‑time dashboard & synthetic‑data generator powered by **Kappa** architecture (producers → Kafka → dashboard) |
| `xAI/`                  | `FV_xAI.ipynb`, `Wind_xAI.ipynb`, `xAI_multiagente.ipynb`                                                                                                                                                                       | Links model insights with agent decisions                                                                        |


---

## Quick start

```bash
# clone repo and create environment
git clone https://github.com/<user>/Microgrid_2.git
cd Microgrid_2
python -m venv .venv && source .venv/bin/activate  # optional but recommended
pip install -r requirements.txt
```

1. **Hourly negotiation** – open `Sistema_Multiagentes/Analisis.ipynb` and run all cells.
2. **Day‑ahead optimisation** – execute `moo_optimization/data_adaptation.py` then `moo_optimization/moo_microgrid.ipynb`.
3. **Explainability** – explore notebooks inside `xAI/`.
4. **Real‑time visualisation (optional)** –

   ```bash
   cd microgrid_kappa
   docker-compose up --build
   ```

   Stream processors will publish solar/wind data; open the generated dashboard URL to monitor the micro‑grid live.

---



