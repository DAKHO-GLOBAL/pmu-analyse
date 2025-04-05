import logging
from datetime import datetime

from sqlalchemy.orm import sessionmaker
from database.setup_database import engine, Hippodrome, Pays, Reunion, Course


def save_pays(pays_data):
    Session = sessionmaker(bind=engine)
    session = Session()
    existing_pays = session.query(Pays).filter_by(code=pays_data.get('code')).first()
    if not existing_pays:
        pays_obj = Pays(**pays_data)
        session.add(pays_obj)
        logging.info("Saving pays data")
    session.commit()

def save_hippodrome(hippodrome_data):
    Session = sessionmaker(bind=engine)
    session = Session()
    existing_hippodrome = session.query(Hippodrome).filter_by(code=hippodrome_data.get('code')).first()
    if not existing_hippodrome:
        hippodrome_obj = Hippodrome(**hippodrome_data)
        session.add(hippodrome_obj)
        logging.info("Saving hippodrome data")
    session.commit()

def save_reunions(reunion_data):
    Session = sessionmaker(bind=engine)
    session = Session()
    existing_reunion = (session.query(Reunion)
                        .filter_by(
        dateReunion=reunion_data.get('dateReunion'),
        numOfficiel=reunion_data.get('numOfficiel')
    ).first())
    if not existing_reunion:
        reunion_data.pop('hippodrome', None)
        reunion_data.pop('pays', None)
        reunion_data.pop('courses', None)
        reunion_obj = Reunion(**reunion_data, hippodrome_code=reunion_data.get('hippodrome', {}).get('code'), pays_code=reunion_data.get('pays', {}).get('code'))
        session.add(reunion_obj)
        logging.info("Saving reunion data")
    session.commit()

def save_courses(courses_data):
    Session = sessionmaker(bind=engine)
    session = Session()

    for course_data in courses_data:
        course_data['heureDepart'] = datetime.utcfromtimestamp(course_data['heureDepart'] / 1000.0)
        existing_course = (session.query(Course).filter_by(
            heureDepart=course_data.get('heureDepart'),
            numReunion=course_data.get('numReunion'),
            numOrdre=course_data.get('numOrdre')
        ).first())
        if not existing_course:
            hipodrome_code = course_data.get('hippodrome', {}).get('codeHippodrome')
            # Définissez une liste des noms d'attributs valides de la classe Course
            valid_attributes = [attr.name for attr in Course.__table__.columns]

            # Créez un nouveau dictionnaire avec seulement les attributs valides
            filtered_course_data = {key: value for key, value in course_data.items() if key in valid_attributes}

            course_obj = Course(**filtered_course_data, hippodrome_code=hipodrome_code)
            session.add(course_obj)
            logging.info("Saving Course data")
            session.commit()


def save_participants_data(participants_data, course_id):
    """Sauvegarde les données des participants dans la base de données"""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Récupérer l'ID de la course
    course = session.query(Course).filter_by(
        numReunion=int(course_id.split('R')[1].split('C')[0]),
        numOrdre=int(course_id.split('C')[1])
    ).first()
    
    if not course:
        logging.error(f"Course {course_id} not found in database")
        session.close()
        return
    
    participants = participants_data.get('participants', [])
    
    for participant_data in participants:
        # Vérifier si le participant existe déjà
        existing_participant = session.query(Participant).filter_by(
            course_id=course.id,
            numPmu=participant_data.get('numPmu')
        ).first()
        
        if not existing_participant:
            # Filtrer les attributs valides
            valid_attributes = [attr.name for attr in Participant.__table__.columns]
            filtered_data = {key: value for key, value in participant_data.items() if key in valid_attributes}
            
            # Traiter les champs spécifiques
            if 'dernierRapportDirect' in participant_data:
                filtered_data['cote'] = participant_data['dernierRapportDirect'].get('rapport')
            
            if 'commentaireApresCourse' in participant_data:
                filtered_data['commentaire'] = participant_data['commentaireApresCourse'].get('texte')
            
            # Créer et sauvegarder le participant
            participant = Participant(course_id=course.id, **filtered_data)
            session.add(participant)
            logging.info(f"Saving participant {participant_data.get('nom')} for course {course_id}")
    
    session.commit()
    session.close()
