# model_training/trainer.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.setup_database import Course, Participant, engine

def prepare_training_data():
    """Prépare les données pour l'entraînement du modèle"""
    # Créer une requête SQL pour joindre les courses et les participants
    query = """
    SELECT p.*, c.distance, c.discipline, c.specialite, c.corde
    FROM pmu_participants p
    JOIN pmu_courses c ON p.course_id = c.id
    WHERE p.ordreArrivee IS NOT NULL
    """
    
    # Exécuter la requête et obtenir un DataFrame
    df = pd.read_sql(query, engine)
    
    # Prétraitement des données
    df = preprocess_data(df)
    
    return df

def preprocess_data(df):
    """Prétraite les données pour l'entraînement"""
    # Convertir les variables catégorielles en variables numériques
    df['sexe_code'] = df['sexe'].map({'MALES': 1, 'HONGRES': 2, 'FEMELLES': 3})
    df['discipline_code'] = df['discipline'].map({'ATTELE': 1, 'MONTE': 2})
    df['corde_code'] = df['corde'].map({'CORDE_GAUCHE': 1, 'CORDE_DROITE': 2})
    
    # Extraire des features à partir de la musique
    df['nb_courses'] = df['musique'].apply(lambda x: len(str(x).split()) if pd.notna(x) else 0)
    
    # Créer des variables cibles
    df['gagnant'] = (df['ordreArrivee'] == 1).astype(int)
    df['place'] = (df['ordreArrivee'] <= 3).astype(int)
    
    # Sélectionner les features pertinentes
    features = ['age', 'sexe_code', 'distance', 'discipline_code', 'corde_code', 'nb_courses']
    
    # Supprimer les lignes avec des valeurs manquantes
    df = df.dropna(subset=features + ['gagnant', 'place'])
    
    return df

def train_model():
    """Entraîne le modèle de prédiction"""
    df = prepare_training_data()
    
    # Sélectionner les features et les cibles
    X = df[['age', 'sexe_code', 'distance', 'discipline_code', 'corde_code', 'nb_courses']]
    y_win = df['gagnant']
    y_place = df['place']
    
    # Diviser les données en ensembles d'entraînement et de test
    X_train, X_test, y_win_train, y_win_test = train_test_split(X, y_win, test_size=0.2, random_state=42)
    _, _, y_place_train, y_place_test = train_test_split(X, y_place, test_size=0.2, random_state=42)
    
    # Entraîner un modèle pour prédire le gagnant
    win_model = RandomForestClassifier(n_estimators=100, random_state=42)
    win_model.fit(X_train, y_win_train)
    
    # Entraîner un modèle pour prédire les places
    place_model = RandomForestClassifier(n_estimators=100, random_state=42)
    place_model.fit(X_train, y_place_train)
    
    # Évaluer les modèles
    win_preds = win_model.predict(X_test)
    place_preds = place_model.predict(X_test)
    
    print("Modèle de prédiction du gagnant:")
    print(f"Accuracy: {accuracy_score(y_win_test, win_preds):.4f}")
    print(f"Precision: {precision_score(y_win_test, win_preds, zero_division=0):.4f}")
    print(f"Recall: {recall_score(y_win_test, win_preds, zero_division=0):.4f}")
    print(f"F1 Score: {f1_score(y_win_test, win_preds, zero_division=0):.4f}")
    
    print("\nModèle de prédiction des places:")
    print(f"Accuracy: {accuracy_score(y_place_test, place_preds):.4f}")
    print(f"Precision: {precision_score(y_place_test, place_preds, zero_division=0):.4f}")
    print(f"Recall: {recall_score(y_place_test, place_preds, zero_division=0):.4f}")
    print(f"F1 Score: {f1_score(y_place_test, place_preds, zero_division=0):.4f}")
    
    # Sauvegarder les modèles
    joblib.dump(win_model, 'model_training/models/win_model.joblib')
    joblib.dump(place_model, 'model_training/models/place_model.joblib')
    
    return win_model, place_model
