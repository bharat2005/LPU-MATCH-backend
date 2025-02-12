from app import app, db 

with app.app_context():
    db.metadata.tables['message'].drop(db.engine)  

