from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from recommender import NutritionRecommender
import os
from datetime import datetime
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nutrition.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Initialize Recommender
recommender = NutritionRecommender()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    height = db.Column(db.Float, nullable=False) # cm
    weight = db.Column(db.Float, nullable=False) # kg
    activity_level = db.Column(db.String(50), nullable=False)
    dietary_preference = db.Column(db.String(20), nullable=False)
    health_conditions = db.Column(db.String(200)) # stored as CSV
    fitness_goal = db.Column(db.String(50), nullable=False)

def init_db():
    with app.app_context():
        db.create_all()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/plan', methods=['GET', 'POST'])
def plan():
    if request.method == 'POST':
        # Collect Data
        name = request.form['name']
        age = int(request.form['age'])
        gender = request.form['gender']
        height = float(request.form['height'])
        weight = float(request.form['weight'])
        activity_level = request.form['activity_level']
        dietary_preference = request.form['dietary_preference']
        
        # Handle checkbox list for conditions
        conditions_list = request.form.getlist('health_conditions')
        health_conditions = ",".join(conditions_list)
        
        fitness_goal = request.form['fitness_goal']
        
        new_user = User(
            name=name,
            age=age,
            gender=gender,
            height=height,
            weight=weight,
            activity_level=activity_level,
            dietary_preference=dietary_preference,
            health_conditions=health_conditions,
            fitness_goal=fitness_goal
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for('dashboard', user_id=new_user.id))
    
    return render_template('form.html')

@app.route('/result/<int:user_id>')
def result(user_id):
    user = User.query.get_or_404(user_id)
    
    user_data = {
        'age': user.age,
        'gender': user.gender,
        'height': user.height,
        'weight': user.weight,
        'activity_level': user.activity_level,
        'dietary_preference': user.dietary_preference,
        'health_conditions': user.health_conditions.split(',') if user.health_conditions else [],
        'goal': user.fitness_goal
    }
    
    recommendation = recommender.recommend(user_data)
    
    return render_template('result.html', user=user, recommendation=recommendation)

class DailyLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    calories_consumed = db.Column(db.Integer, default=0)
    water_intake = db.Column(db.Float, default=0.0) # Liters
    weight = db.Column(db.Float) # kg
    bmi = db.Column(db.Float)
    mood = db.Column(db.String(50))
    notes = db.Column(db.Text)

@app.route('/dashboard/<int:user_id>')
def dashboard(user_id):
    user = User.query.get_or_404(user_id)
    logs = DailyLog.query.filter_by(user_id=user_id).order_by(DailyLog.date).all()
    
    user_data = {
        'age': user.age, 
        'gender': user.gender, 
        'height': user.height,
        'weight': user.weight, 
        'activity_level': user.activity_level,
        'dietary_preference': user.dietary_preference,
        'health_conditions': user.health_conditions.split(',') if user.health_conditions else [],
        'goal': user.fitness_goal
    }
    recommendation = recommender.recommend(user_data) 
    
    # Process trend data
    trendLabels = [log.date.strftime('%b %d') for log in logs]
    trendCalories = [log.calories_consumed for log in logs]
    trendWeight = [log.weight for log in logs]
    trendBMI = [log.bmi for log in logs]
    
    return render_template('dashboard.html', user=user, logs=logs, recommendation=recommendation,
                           trendLabels=trendLabels, trendCalories=trendCalories, 
                           trendWeight=trendWeight, trendBMI=trendBMI)

@app.route('/ai-coach/<int:user_id>')
def ai_coach(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('ai_coach.html', user=user)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('message', '').lower()
    user_id = data.get('user_id')
    
    user = User.query.get(user_id)
    if not user:
        return {'response': "User not found."}

    today = datetime.utcnow().date()
    log = DailyLog.query.filter_by(user_id=user_id, date=today).first()
    if not log:
        log = DailyLog(user_id=user_id, date=today, weight=user.weight)
        # Calculate initial BMI for the log
        log.bmi = round(user.weight / ((user.height / 100) ** 2), 2)
        db.session.add(log)
        db.session.commit()

    response = ""
    action = None
    
    # --- Health Condition & Data Analysis Logic ---
    
    # 1. BMI / Health Status Analysis
    if "health" in user_input or "status" in user_input or "condition" in user_input or "bmi" in user_input:
        bmi = log.bmi
        status = ""
        advice = ""
        if bmi < 18.5:
            status = "Underweight"
            advice = "You might need to increase your calorie intake with nutrient-dense foods."
        elif 18.5 <= bmi < 24.9:
            status = "Normal weight"
            advice = "Great job! Your weight is in the healthy range. Keep focusing on balanced nutrition."
        elif 25 <= bmi < 29.9:
            status = "Overweight"
            advice = "You are slightly above the healthy range. Consider increasing physical activity and monitoring portion sizes."
        else:
            status = "Obese"
            advice = "Your BMI indicates obesity, which can increase health risks. We recommend consulting a nutritionist for a tailored weight management plan."
        
        response = f"Based on your current data (Weight: {log.weight}kg, Height: {user.height}cm), your BMI is **{bmi}**, which is categorized as **{status}**. {advice}"
        
        if "diabetes" in user.health_conditions.lower() or "diabetes" in user_input:
            response += "\n\n**Note for Diabetes:** Be sure to monitor your carbohydrate intake and choose low-glycemic foods as per your plan."
        if "hypertension" in user.health_conditions.lower() or "hypertension" in user_input:
            response += "\n\n**Note for Hypertension:** Keep an eye on your sodium intake and prioritize potassium-rich foods like bananas and spinach."

    # 2. Logging Water
    elif "water" in user_input and ("drunk" in user_input or "add" in user_input or "log" in user_input):
        try:
            amount = [float(s) for s in user_input.replace('l', '').split() if s.replace('.','',1).isdigit()]
            if amount:
                log.water_intake += amount[0]
                db.session.commit()
                response = f"Great! I've logged **{amount[0]}L** of water. Your total for today is **{log.water_intake}L**. Stay hydrated!"
                action = {'type': 'update_water', 'value': log.water_intake}
            else:
                response = "How much water did you drink? You can say things like 'I drank 0.5L'."
        except:
             response = "I couldn't understand the amount. Try 'add 0.5L water'."
             
    # 3. Logging Weight
    elif "weight" in user_input and ("log" in user_input or "set" in user_input or "is" in user_input):
         try:
            # Clean string to find numbers
            import re
            numbers = re.findall(r"[-+]?\d*\.\d+|\d+", user_input)
            if numbers:
                weight_val = float(numbers[0])
                log.weight = weight_val
                log.bmi = round(weight_val / ((user.height / 100) ** 2), 2)
                db.session.commit()
                response = f"Weight logged: **{weight_val}kg**. Updated BMI: **{log.bmi}**. I've adjusted your tracking for today."
                action = {'type': 'update_weight', 'value': weight_val, 'bmi': log.bmi}
            else:
                response = "Please specify your weight in kg, e.g., 'My weight is 72kg'."
         except:
             response = "I couldn't catch the weight value. Try 'Log weight 70'."

    # 4. Logging Meal / Calories
    elif "meal" in user_input or "ate" in user_input or "calories" in user_input:
        import re
        numbers = re.findall(r"\d+", user_input)
        if numbers:
            cals = int(numbers[0])
            log.calories_consumed += cals
            db.session.commit()
            response = f"Logged **{cals}** calories. You've consumed a total of **{log.calories_consumed}** kcal today."
            action = {'type': 'update_calories', 'value': log.calories_consumed}
        else:
            response = "That sounds good! Approximately how many calories was that? (e.g., 'I ate 400 calories')"
        
    # 5. General AI / Chat Context
    elif "hello" in user_input or "hi" in user_input or "hey" in user_input:
        response = f"Hello {user.name}! I'm your AI Nutrition Assistant. I can analyze your health data, give you status updates, or help you log your progress. How can I help you today?"
        
    elif "tips" in user_input or "advice" in user_input:
        tips = [
            "Eat more fiber-rich foods like oats and lentils to stay full longer.",
            "Try to limit processed sugars and opt for whole fruits instead.",
            "Consistency is key! Logging your meals daily helps you stay on track.",
            "Don't forget to get 7-8 hours of sleep for better metabolic health.",
            "Drink a glass of water before every meal to aid digestion."
        ]
        response = "Here's a tip for you: " + random.choice(tips)

    elif "who are you" in user_input or "what can you do" in user_input:
        response = "I am NutriAI, your personal nutrition companion. I can track your calories, water, and weight, provide BMI assessments, and offer personalized health advice based on your profile."

    else:
        # Fallback to generic smart response
        response = f"I'm here to help, {user.name}. You can ask about your health status, log your weight/water, or get nutrition tips. (e.g. 'How is my health condition?')"

    return {'response': response, 'action': action}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
