# train_agwind_model.py

import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_squared_error

#  1. Cargar datos
df = pd.read_csv("WindTrain.csv")

# 2. Escalar la potencia (W)
df["Power"] *= 50.0 # Ajustar escala

X = df[["windspeed_100m", "windspeed_10m", "windgusts_10m"]]
y = df["Power"]

# 3. División de datos
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. Entrenar modelo
model = GradientBoostingRegressor(random_state=42)
model.fit(X_train, y_train)

# 5. Evaluación
y_pred = model.predict(X_test)
r2 = r2_score(y_test, y_pred)
rmse = mean_squared_error(y_test, y_pred) ** 0.5  # <-- Corrección aquí

print("Modelo Gradient Boosting Solar entrenado")
print(f"R²: {r2:.4f}")
print(f"RMSE: {rmse:.4f} Wh")

# 6. Guardar modelo
joblib.dump(model, "wind_model.pkl")

# 7. Prueba de predicción
test_input = pd.DataFrame([[7.5, 2.5, 3.0]], columns=["windspeed_100m", "windspeed_10m", "windgusts_10m"])
pred = model.predict(test_input)[0]
print(f"[CHECK] Predicción para viento 7.5 m/s → {pred:.2f} W")
