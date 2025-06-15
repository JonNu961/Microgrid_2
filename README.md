# Microgrid_2

**Microgrid\_2** is an academic prototype that explores how solar‑photovoltaic and wind generators can coordinate in a smart micro‑grid through:

1. **Multi‑Agent Negotiation** – solar and wind agents place hourly bids using *reveal*, *hide* and *bluffing* strategies.
2. **Explainable Forecasting** – LightGBM models predict next‑day production and are dissected with SHAP, ICE and LIME.
3. **Multi‑Objective Optimisation (MOO)** – day‑ahead schedules are optimised to maximise producer revenue and minimise consumer cost under reliability constraints.

---

## Repository layout

| Path                    | Main contents                                                                                                                                                                                                                                                                                                                                  | Purpose                                  |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| `Sistema_Multiagentes/` | • `Agentes/` – Python classes for Solar & Wind agents and negotiation logic.  • `CSV_Generados/` – logs from simulation runs (offers, penalties, balances).  • `Data/` – pre‑processed weather & demand series.  • `Modelos_Entrenados/` – pickled forecasting models.  • `Analisis.ipynb` – notebook that executes >8 000 negotiation rounds. | Core hourly market simulation            |
| `moo_optimization/`     | • `data/` – matrices for the optimiser (predicted generation, tariffs, demand).  • `models/` – Pareto fronts & checkpoints.  • `figures/` – plots produced by the notebooks.  • `data_adaptation.py` – reshapes simulation output.  • `moo_microgrid.ipynb` – NSGA‑II/III & SPEA2 experiments.                                                 | Finds cost‑efficient day‑ahead schedules |
| `xAI/`                  | • `FV_xAI.ipynb` – explainability for the solar model.  • `Wind_xAI.ipynb` – explainability for the wind model.  • `xAI_multiagente.ipynb` – links model insights with agent decisions.                                                                                                                                                        | Explains why bluffing emerges as optimal |
| `requirements.txt`      | Python dependencies                                                                                                                                                                                                                                                                                                                            | Reproducibility                          |

---

## Quick start

1. Open `Sistema_Multiagentes/Analisis.ipynb` to reproduce the hourly negotiation study.
2. Run `moo_optimization/data_adaptation.py` followed by `moo_optimization/moo_microgrid.ipynb` for the optimisation stage.
3. Explore the notebooks in `xAI/` for model interpretability.


