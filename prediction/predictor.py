# prediction/predictor.py
import joblib
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.setup_database import Course, Participant, engine

def load_models():
    """Charge les modèles entraînés"""
    win_model = joblib.load('model_training/models/win_model.joblib')
    place_model = joblib.load('model_training/models/place_model.joblib')
    return win_model, place_model

def prepare_prediction_data(course_id):
    """Prépare les données pour la prédiction"""
    # Créer une session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Récupérer la course
    course = session.query(Course).filter_by(id=course_id).first()
    
    if not course:
        print(f"Course {course_id} not found")
        session.close()
        return None
    
    # Récupérer les participants
    participants = session.query(Participant).filter_by(course_id=course_id).all()
    
    if not participants:
        print(f"No participants found for course {course_id}")
        session.close()
        return None
    
    # Créer un DataFrame avec les participants
    data = []
    for p in participants:
        row = {
            'numPmu': p.numPmu,
            'nom': p.nom,
            'age': p.age,
            'sexe': p.sexe,
            'distance': course.distance,
            'discipline': course.discipline,
            'corde': course.corde,
            'musique': p.musique
        }
        data.append(row)
    
    df = pd.DataFrame(data)
    
    # Prétraitement des données
    df['sexe_code'] = df['sexe'].map({'MALES': 1, 'HONGRES': 2, 'FEMELLES': 3})
    df['discipline_code'] = df['discipline'].map({'ATTELE': 1, 'MONTE': 2})
    df['corde_code'] = df['corde'].map({'CORDE_GAUCHE': 1, 'CORDE_DROITE': 2})
    df['nb_courses'] = df['musique'].apply(lambda x: len(str(x).split()) if pd.notna(x) else 0)
    
    session.close()
    
    return df

def predict_race(course_id):
    """Prédire les résultats d'une course"""
    # Charger les modèles
    win_model, place_model = load_models()
    
    # Préparer les données
    df = prepare_prediction_data(course_id)
    
    if df is None:
        return None
    
    # Sélectionner les features
    X = df[['age', 'sexe_code', 'distance', 'discipline_code', 'corde_code', 'nb_courses']]
    
    # Prédire les probabilités
    win_probs = win_model.predict_proba(X)[:, 1]
    place_probs = place_model.predict_proba(X)[:, 1]
    
    # Ajouter les prédictions au DataFrame
    df['prob_gagnant'] = win_probs
    df['prob_place'] = place_probs
    
    # Trier par probabilité de gagner
    df = df.sort_values('prob_gagnant', ascending=False)
    
    # Afficher les prédictions
    print(f"\nPrédictions pour la course {course_id}:")
    print("\nPronostics pour la victoire:")
    for i, row in df.head(3).iterrows():
        print(f"{row['numPmu']}. {row['nom']} - {row['prob_gagnant']*100:.1f}%")
    
    print("\nPronostics pour les places:")
    for i, row in df.sort_values('prob_place', ascending=False).head(5).iterrows():
        print(f"{row['numPmu']}. {row['nom']} - {row['prob_place']*100:.1f}%")
    
    return df
