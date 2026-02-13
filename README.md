# AI-Based Nutrition Recommender System

This is a Flask-based application that uses an Expert System (Rule-Based Logic) to generate customized diet plans based on user biometrics, preferences, and health goals.

## Features
- **User Profiling**: Collects age, gender, height, weight, activity level, and health conditions.
- **AI Analysis**: Calculates BMR, TDEE, and BMI Status.
- **Smart Recommendations**: Suggests meals (Breakfast, Lunch, Dinner, Snacks) filtering by dietary preference (Veg/Non-Veg) and health conditions (Diabetes, etc.).
- **Rich UI**: Modern, responsive interface with glassmorphism design.

## Setup Instructions

1.  **Install Python**: Ensure Python is installed and added to your system PATH.
2.  **Install Dependencies**:
    Open a terminal in this directory and run:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the Application**:
    ```bash
    python app.py
    ```
4.  **Access the App**:
    Open your browser and go to `http://127.0.0.1:5000/`

## Project Structure
- `app.py`: Main Flask application and database model.
- `recommender.py`: The logic engine for calculations and food selection.
- `data/food_data.json`: The database of foods used for recommendations.
- `templates/`: HTML files.
- `static/`: CSS and assets.
