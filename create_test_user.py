from app import app, db, User
with app.app_context():
    new_user = User(
        name="Alex",
        age=28,
        gender="Male",
        height=180.0,
        weight=85.0,
        activity_level="moderately_active",
        dietary_preference="veg",
        health_conditions="Diabetes",
        fitness_goal="weight_loss"
    )
    db.session.add(new_user)
    db.session.commit()
    print(f"Created user with ID: {new_user.id}")
