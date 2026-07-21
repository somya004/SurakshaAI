import joblib

model = joblib.load("models_artifacts/risk_model.joblib")

print(type(model))
print(model)