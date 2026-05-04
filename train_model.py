import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib

# 🔹 Generate synthetic dataset
X = np.random.normal(loc=[25, 50], scale=[5, 10], size=(1000, 2))

# 🔹 Create labels (0 = normal, 1 = anomaly)
y = []
for temp, hum in X:
    if temp > 45 or hum > 90:
        y.append(1)
    else:
        y.append(0)

y = np.array(y)

# 🔹 Train model
model = RandomForestClassifier()
model.fit(X, y)

# 🔹 Save model
joblib.dump(model, "rf_model.pkl")

print("✅ Model trained and saved as rf_model.pkl")