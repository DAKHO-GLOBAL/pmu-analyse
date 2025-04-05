import sys
import logging
from datetime import datetime
from logging.config import fileConfig
from scrapping.scrapping import call_api_between_dates
from model_training.trainer import train_model
from prediction.predictor import predict_race

fileConfig('logger/logging_config.ini')

def show_help():
    print("Usage:")
    print("  python main.py scrape <start_date> <end_date>  # Scrape races between dates (format: DD-MM-YYYY)")
    print("  python main.py train                         # Train the prediction model")
    print("  python main.py predict <course_id>           # Predict results for a specific course")

def main():
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1]
    
    if command == "scrape":
        if len(sys.argv) < 4:
            print("Error: Missing date parameters")
            show_help()
            return
        
        try:
            start_date = datetime.strptime(sys.argv[2], "%d-%m-%Y")
            end_date = datetime.strptime(sys.argv[3], "%d-%m-%Y")
            
            print(f"Scraping races from {start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')}...")
            call_api_between_dates(start_date, end_date)
            print("Scraping completed!")
        
        except ValueError:
            print("Error: Invalid date format. Use DD-MM-YYYY")
    
    elif command == "train":
        print("Training prediction model...")
        train_model()
        print("Model training completed!")
    
    elif command == "predict":
        if len(sys.argv) < 3:
            print("Error: Missing course ID")
            show_help()
            return
        
        course_id = int(sys.argv[2])
        print(f"Predicting results for course {course_id}...")
        predict_race(course_id)
    
    else:
        print(f"Unknown command: {command}")
        show_help()

if __name__ == "__main__":
    main()
