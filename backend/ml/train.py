"""
Train binary classifier for drug-target relevance.
Source: backend/data/processed/final_training_set.csv
Artifact: backend/ml/artifacts/model.joblib
"""
import os
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import sys

# Ensure we can import from backend
sys.path.append(os.path.join(os.getcwd(), "backend"))
from ml.feature_engineering import get_fingerprint, get_target_vector

def train_model():
    data_path = "backend/data/processed/final_training_set.csv"
    if not os.path.exists(data_path):
        print(f"Error: Data file not found at {data_path}")
        return

    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    
    # Binarize labels: Potency < 1000 nM is Relevant (1)
    # Note: standard_value is potency in nM as seen in earlier view_file
    print("Pre-processing data...")
    df['relevance'] = df['standard_value'].apply(lambda x: 1 if x < 1000 else 0)
    
    X = []
    y = []
    
    total = len(df)
    print(f"Generating features for {total} records...")
    
    for i, row in df.iterrows():
        if i % 500 == 0:
            print(f" Progress: {i}/{total}")
        
        target_v = get_target_vector(str(row['target_chembl_id']))
        drug_fp = get_fingerprint(str(row['smiles']))
        
        # Combine: 500 + 2048 = 2548
        combined = np.concatenate([target_v, drug_fp])
        X.append(combined)
        y.append(row['relevance'])
        
    X = np.array(X)
    y = np.array(y)
    
    print(f"Splitting data (X shape: {X.shape})...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training RandomForestClassifier...")
    model = RandomForestClassifier(n_estimators=100, max_depth=15, n_jobs=-1, random_state=42)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Model Accuracy: {acc:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # Attach metadata
    model.version = "1.0.0"
    model.feature_dim = 2548
    
    artifact_path = "backend/ml/artifacts/model.joblib"
    os.makedirs(os.path.dirname(artifact_path), exist_ok=True)
    joblib.dump(model, artifact_path)
    print(f"Model saved to {artifact_path}")

if __name__ == "__main__":
    train_model()
