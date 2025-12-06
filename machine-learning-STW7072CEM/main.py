import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# ---------------------------------------
# 1. LOAD DATA
# ---------------------------------------
df = pd.read_csv("forest_fire.csv")

# ---------------------------------------
# 2. SELECT FEATURES FOR KNN
# ---------------------------------------
features = [
    'LATITUDE', 'LONGITUDE', 'BRIGHTNESS', 'CONFIDENCE', 'BRIGHT_T31',
    'FRP', 'ELEVATION', 'SLOPE', 'LCCODE'
]

# Keep only available columns
features = [f for f in features if f in df.columns]

# ---------------------------------------
# 3. CREATE WILDFIRE RISK CLASSES FROM FRP
# ---------------------------------------
def risk_level(frp):
    if frp < 50:
        return "Low"
    elif frp < 150:
        return "Medium"
    else:
        return "High"


def main():
    X = df[features]

    df["RISK_CLASS"] = df["FRP"].apply(risk_level)
    y = df["RISK_CLASS"]

    # ---------------------------------------
    # 4. ENCODE CATEGORICAL COLUMNS
    # ---------------------------------------
    label_encoders = {}
    for col in X.columns:
        if X[col].dtype == 'object':
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col])
            label_encoders[col] = le

    # Encode target labels
    y_le = LabelEncoder()
    y = y_le.fit_transform(y)

    # ---------------------------------------
    # 5. TRAIN / TEST SPLIT
    # ---------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # ---------------------------------------
    # 6. FEATURE SCALING (VERY IMPORTANT FOR KNN)
    # ---------------------------------------
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # ---------------------------------------
    # 7. KNN MODEL
    # ---------------------------------------
    knn = KNeighborsClassifier(n_neighbors=5)
    knn.fit(X_train_scaled, y_train)

    # ---------------------------------------
    # 8. EVALUATION
    # ---------------------------------------
    y_pred = knn.predict(X_test_scaled)

    print("Accuracy:", accuracy_score(y_test, y_pred))
    print("\nClassification Report:\n", classification_report(y_test, y_pred))

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    # ---------------------------------------
    # 9. EXAMPLE PREDICTION FOR A NEW LOCATION
    # ---------------------------------------
    #new_point = np.array([[27.2, 87.6, 350, 80, 290, 120, 400, 15, 11]])
    new_point_df = pd.DataFrame([{
        'LATITUDE': 27.2,
        'LONGITUDE': 87.6,
        'BRIGHTNESS': 350,
        'CONFIDENCE': 80,
        'BRIGHT_T31': 290,
        'FRP': 120,
        'ELEVATION': 400,
        'SLOPE': 15,
        'LCCODE': 11
    }])

    new_point_scaled = scaler.transform(new_point_df)

    predicted_class = y_le.inverse_transform(knn.predict(new_point_scaled))[0]
    print("\nPredicted Wildfire Risk:", predicted_class)

    print("Hello from machine-learning-stw7072cem!")


if __name__ == "__main__":
    main()
