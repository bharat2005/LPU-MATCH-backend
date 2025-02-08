from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_marshmallow import Marshmallow

app = Flask(__name__)
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["JWT_SECRET_KEY"] = "supersecret"  


db = SQLAlchemy(app)
ma = Marshmallow(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    gender = db.Column(db.String(), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    images = db.Column(db.JSON)
    reason = db.Column(db.String(), nullable=False)

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True

user_schema = UserSchema(many=True)
single_user_schema = UserSchema()

@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        reg_no = data.get("regNo")
        password = data.get("password")

        if reg_no and password:
            return jsonify({"message": "Login successful"}), 200
        else:
            return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/profile", methods=["POST"])
def profile():
    try:
        data = request.get_json()
        user = User(
            name=data["name"],
            gender=data["gender"],
            age=data["age"],
            images=data["images"],
            reason=data["reason"],
        )
        db.session.add(user)
        db.session.commit()
        return jsonify({"message": "Profile created successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/dashboard", methods=["GET"])
def dashboard():
    try:
        profiles = User.query.all()
        return jsonify(user_schema.dump(profiles))

        
    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)