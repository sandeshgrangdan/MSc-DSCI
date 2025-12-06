import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from imblearn.over_sampling import SMOTE

# ---------------------------------------
# 1. HELPER FUNCTIONS
# ---------------------------------------
def risk_level(frp):
    """Classifies risk based on Fire Radiative Power (FRP)."""
    if frp < 51:
        return "Low"
    elif frp < 151:
        return "Medium"
    else:
        return "High"

def main():
    # ---------------------------------------
    # 2. LOAD DATA
    # ---------------------------------------
    # Ensure this file exists in your directory
    try:
        df = pd.read_csv("forest_fire.csv")
        print("✅ Data Loaded Successfully.")
    except FileNotFoundError:
        print("❌ Error: 'forest_fire.csv' not found.")
        return

    # ---------------------------------------
    # 3. FEATURE SELECTION & ENGINEERING
    # ---------------------------------------
    # Target Features
    features = [
        'LATITUDE', 'LONGITUDE', 'BRIGHTNESS', 'CONFIDENCE', 'BRIGHT_T31', 
        'FRP', 'ELEVATION', 'SLOPE', 'LCCODE'
    ]
    
    # Filter to ensure we only use columns that actually exist in the CSV
    features = [f for f in features if f in df.columns]
    X = df[features].copy()

    # Create Target Variable
    df["RISK_CLASS"] = df["FRP"].apply(risk_level)
    y = df["RISK_CLASS"]

    print(f"🔹 Class Distribution before Split:\n{y.value_counts()}")

    # ---------------------------------------
    # 4. ENCODE CATEGORICAL COLUMNS
    # ---------------------------------------
    # We store encoders in a dictionary so we can use them later for new predictions
    feature_encoders = {}
    
    for col in X.columns:
        if X[col].dtype == 'object':
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col])
            feature_encoders[col] = le

    # Encode Target (y)
    target_encoder = LabelEncoder()
    y_encoded = target_encoder.fit_transform(y)

    # ---------------------------------------
    # 5. TRAIN / TEST SPLIT (CRITICAL FIX)
    # ---------------------------------------
    # IMPROVEMENT: Use stratify=y to maintain class percentages in train/test
    # IMPROVEMENT: Fixed test_size to 0.2 (20%)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )

    # ---------------------------------------
    # 6. SCALING (CRITICAL FIX)
    # ---------------------------------------
    # Standardize features (Mean=0, Std=1)
    # IMPORTANT: Fit ONLY on X_train, then transform both
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # ---------------------------------------
    # 7. SMOTE (OVERSAMPLING)
    # ---------------------------------------
    print("\n🔹 Applying SMOTE to balance training data...")
    # IMPROVEMENT: k_neighbors=3 is safer for very small classes (like 'Low' risk)
    sm = SMOTE(random_state=43, k_neighbors=3)
    X_train_bal, y_train_bal = sm.fit_resample(X_train_scaled, y_train)

    print(f"   Training samples before SMOTE: {len(y_train)}")
    print(f"   Training samples after SMOTE:  {len(y_train_bal)}")

    # ---------------------------------------
    # 8. TRAIN KNN MODEL
    # ---------------------------------------
    # Using 'distance' weights helps significantly with class overlap
    knn = KNeighborsClassifier(n_neighbors=8, weights='distance')
    knn.fit(X_train_bal, y_train_bal)

    # ---------------------------------------
    # 9. EVALUATE MODEL
    # ---------------------------------------
    y_pred = knn.predict(X_test_scaled)

    print("\n" + "="*40)
    print("MODEL PERFORMANCE RESULTS")
    print("="*40)
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    
    print("\nClassification Report:")
    # We use target_names to show 'Low', 'Medium', 'High' instead of 0, 1, 2
    print(classification_report(y_test, y_pred, target_names=target_encoder.classes_))

    print("\nConfusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(cm)

    # ---------------------------------------
    # 10. TEST MULTIPLE PREDICTIONS
    # ---------------------------------------
    print("\n" + "="*40)
    print("TESTING DIFFERENT RISK SCENARIOS")
    print("="*40)

    test_cases = [
        {
            "Label": "TEST CASE 1 (Should be LOW)",
            "Data": {
                'LATITUDE': 27.2, 'LONGITUDE': 87.6, 
                'BRIGHTNESS': 310.0, 'CONFIDENCE': 50.0, 'BRIGHT_T31': 290.0, 
                'FRP': 20.0, # Low FRP
                'ELEVATION': 400.0, 'SLOPE': 5.0, 'LCCODE': 11.0
            }
        },
        {
            "Label": "TEST CASE 2 (Should be MEDIUM)",
            "Data": {
                'LATITUDE': 27.2, 'LONGITUDE': 87.6, 
                'BRIGHTNESS': 350.0, 'CONFIDENCE': 80.0, 'BRIGHT_T31': 300.0, 
                'FRP': 100.0, # Medium FRP (51-150)
                'ELEVATION': 400.0, 'SLOPE': 15.0, 'LCCODE': 11.0
            }
        },
        {
            "Label": "TEST CASE 3 (Should be HIGH)",
            "Data": {
                'LATITUDE': 27.2, 'LONGITUDE': 87.6, 
                'BRIGHTNESS': 400.0, 'CONFIDENCE': 100.0, 'BRIGHT_T31': 310.0, 
                'FRP': 200.0, # High FRP (>151)
                'ELEVATION': 400.0, 'SLOPE': 30.0, 'LCCODE': 11.0
            }
        }
    ]

    for case in test_cases:
        # Create DataFrame
        new_df = pd.DataFrame([case["Data"]])
        
        # Select Features
        new_df = new_df[features]

        # Encode Categorical (LCCODE usually)
        for col, le in feature_encoders.items():
            if col in new_df.columns:
                # Handle potential unseen labels
                try:
                    new_df[col] = le.transform(new_df[col])
                except ValueError:
                    new_df[col] = 0

        # Scale
        new_point_scaled = scaler.transform(new_df)

        # Predict
        pred_idx = knn.predict(new_point_scaled)[0]
        pred_label = target_encoder.inverse_transform([pred_idx])[0]

        print(f"\n{case['Label']}")
        print(f"Input Data:\n{new_df.iloc[0].to_dict()}")
        print(f"Input FRP: {case['Data']['FRP']}")
        print(f"🔥 Prediction: {pred_label}")

if __name__ == "__main__":
    main()
