import json
import random
import os

class NutritionRecommender:
    def __init__(self, data_path='data/food_data.json'):
        self.data_path = data_path
        self.foods = self.load_data()

    def load_data(self):
        try:
            with open(self.data_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading data: {e}")
            return []

    def calculate_bmr(self, age, gender, weight, height):
        # Mifflin-St Jeor Equation
        # Weight in kg, Height in cm
        if gender.lower() == 'male':
            return (10 * weight) + (6.25 * height) - (5 * age) + 5
        else:
            return (10 * weight) + (6.25 * height) - (5 * age) - 161

    def calculate_tdee(self, bmr, activity_level):
        activity_multipliers = {
            'sedentary': 1.2,
            'lightly_active': 1.375,
            'moderately_active': 1.55,
            'very_active': 1.725,
            'extra_active': 1.9
        }
        return bmr * activity_multipliers.get(activity_level, 1.2)

    def calculate_calories_and_macros(self, tdee, goal):
        if goal == 'weight_loss':
            target_calories = tdee - 500
            macros = {'protein': 0.40, 'carbs': 0.30, 'fats': 0.30}
        elif goal == 'weight_gain':
            target_calories = tdee + 500
            macros = {'protein': 0.30, 'carbs': 0.50, 'fats': 0.20}
        elif goal == 'muscle_building':
            target_calories = tdee + 250
            macros = {'protein': 0.35, 'carbs': 0.45, 'fats': 0.20}
        else: # healthy lifestyle
            target_calories = tdee
            macros = {'protein': 0.30, 'carbs': 0.40, 'fats': 0.30}
        
        return {
            'calories': int(target_calories),
            'protein_g': int((target_calories * macros['protein']) / 4),
            'carbs_g': int((target_calories * macros['carbs']) / 4),
            'fats_g': int((target_calories * macros['fats']) / 9)
        }

    def filter_foods(self, preferences, health_conditions):
        filtered = []
        for food in self.foods:
            # Check Veg/Non-Veg
            if preferences.lower() == 'veg' and food['veg_nonveg'].lower() == 'non-veg':
                continue
            
            # Check Health Conditions (Avoidance)
            # This is a simple rule-based avoidance. 
            # In a real ML system, this would be more complex.
            safe = True
            for condition in health_conditions:
                # Simple keyword matching in avoidance list or looking for "diabetes_friendly" tag
                condition = condition.lower()
                
                # If food explicitly says avoid for this condition
                for avoid in food.get('avoid_for', []):
                    if condition in avoid.lower():
                        safe = False
                        break
                
                # Special logic for Diabetes
                if condition == 'diabetes' and 'diabetes_friendly' not in food['tags']:
                     # If not explicitly marked friendly, maybe check carbs?
                     # For now, strict filtering based on tags/logic is better for safety
                     pass 

            if safe:
                filtered.append(food)
        return filtered

    def generate_daily_plan(self, filtered_foods, target_stats):
        # Organize by meal type
        meals = {'Breakfast': [], 'Lunch': [], 'Dinner': [], 'Snack': []}
        for food in filtered_foods:
            if food['type'] in meals:
                meals[food['type']].append(food)
        
        plan = {}
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fats = 0

        # Simple greedy selection or random selection to fill slots
        # In a real system, we'd use an optimization algorithm (knapsack-like)
        for meal_type in ['Breakfast', 'Lunch', 'Snack', 'Dinner']:
            options = meals.get(meal_type, [])
            if options:
                choice = random.choice(options)
                plan[meal_type] = choice
                total_calories += choice['calories']
                total_protein += choice['protein']
                total_carbs += choice['carbs']
                total_fats += choice['fats']
            else:
                plan[meal_type] = None

        return {
            'plan': plan,
            'totals': {
                'calories': total_calories,
                'protein': total_protein,
                'carbs': total_carbs,
                'fats': total_fats
            },
            'targets': target_stats
        }

    def recommend(self, user_data):
        bmr = self.calculate_bmr(
            user_data['age'], 
            user_data['gender'], 
            user_data['weight'], 
            user_data['height']
        )
        tdee = self.calculate_tdee(bmr, user_data['activity_level'])
        target_stats = self.calculate_calories_and_macros(tdee, user_data['goal'])
        
        # Parse health conditions
        # Assuming input is a list of strings
        health_conditions = user_data.get('health_conditions', [])
        
        filtered_foods = self.filter_foods(user_data['dietary_preference'], health_conditions)
        
        diet_plan = self.generate_daily_plan(filtered_foods, target_stats)
        
        # Calculate BMI
        bmi = user_data['weight'] / ((user_data['height']/100) ** 2)
        if bmi < 18.5:
            bmi_status = "Underweight"
        elif 18.5 <= bmi < 24.9:
            bmi_status = "Normal Weight"
        elif 25 <= bmi < 29.9:
            bmi_status = "Overweight"
        else:
            bmi_status = "Obese"

        return {
            'bmi': round(bmi, 2),
            'bmi_status': bmi_status,
            'bmr': int(bmr),
            'tdee': int(tdee),
            'diet_plan': diet_plan
        }
