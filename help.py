from app import app, db , Swipe

with app.app_context():
    Swipe.__table__.drop(db.engine)





