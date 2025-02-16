from app import app, db , Message

with app.app_context():
    Message.__table__.drop(db.engine)





