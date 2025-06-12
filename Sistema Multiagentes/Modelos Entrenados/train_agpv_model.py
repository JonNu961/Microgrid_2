# train_agpv_model.py

import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_squared_error

# 1. Cargar datos
df = pd.read_csv("FVTrain.csv")

# 2. Escalar el objetivo (Wh)
df["SystemProduction"] *= 50

X = df[["Radiation", "Sunshine"]]
y = df["SystemProduction"]

# === 3. División de datos ===
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
joblib.dump(model, "pv_model.pkl")

# 7. Prueba de predicción
test_input = pd.DataFrame([[300, 5]], columns=["Radiation", "Sunshine"])
pred = model.predict(test_input)[0]
print(f"[CHECK] Predicción para Radiation=300 y Sunshine=5 → {pred:.2f} Wh")
