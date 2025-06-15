# Modulo para hacer append de las predicciones de potencia de los algoritmos black-box (LightGBM)
# preentrenados de solar (lgbm_model_wind.pkl) y eólica (lgbm_model_fv.pkl). Las columnas
# serán nombradas como `power_eol_W` y `power_sol_W`, respectivamente. Con este procesamiento,
# lograremos definir el archivo csv a emplear para la optimización evolutiva del problema.

import pandas as pd
import joblib
import lightgbm as lgb

# Importamos el archivo data.csv que hemos empleado como nuestro caso de uso real.
df = pd.read_csv("data/data_complete.csv")

# Cargamos los modelos preentrenados.
wind_model = joblib.load("models/lgbm_model_wind.pkl")
solar_model = joblib.load("models/lgbm_model_fv.pkl")

# Emplear el vector de predictors X correcto, utilizamos las variables con las que se han entrenado los modelos.
features_wind = wind_model.feature_name_
features_solar = solar_model.feature_name_

# Cambiamos los nombres de los feature solar, ya que el naming era distinto en el train al del caso real.
df = df.rename(columns={
    "WindSpeed_FV": "WindSpeed",
    "Sunshine_FV": "Sunshine",
    "Radiation_FV": "Radiation",
    "RelativeAirHumidity_FV": "RelativeAirHumidity"
})

# Definimos los vectores predictores para realizar las inferencias y hacer el append final.
X_wind = df[features_wind]
X_solar = df[features_solar]

# Realizamos las predicciones y las asignamos a las nuevas columnas correspondientes.
df["power_eol_W"] = wind_model.predict(X_wind)
df["power_sol_W"] = solar_model.predict(X_solar)

df["power_eol_W"] = df["power_eol_W"].clip(lower=0) # En ambos casos se hace un clip a cero para evitar potencias negativas (presentes sobre todo en solar).
df["power_sol_W"] = df["power_sol_W"].clip(lower=0) 

# Guardamos el .csv final que utilizaremos en el problema MOO.
df.to_csv("data/data_complete_w_pred.csv", index=False)