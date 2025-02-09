from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_marshmallow import Marshmallow
import boto3

app = Flask(__name__)
CORS(app)


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///appo.db"
app.config["JWT_SECRET_KEY"] = "supersecret"  

db = SQLAlchemy(app)
ma = Marshmallow(app)


AWS_ACCESS_KEY_ID = "AKIA2AUOPH4PEF7QJUA5"  
AWS_SECRET_ACCESS_KEY = "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"  
AWS_REGION = "eu-north-1" 
S3_BUCKET_NAME = "bharatbuckettiny"  



s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)


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







@app.route("/get_presigned_url", methods=["POST"])
def get_presigned_url():
    data = request.get_json()
    file_name = data.get("file_name")
    content_type = data.get("content_type")
    
    presigned_url = s3_client.generate_presigned_url(
        "put_object",
        Params={"Bucket": S3_BUCKET_NAME, "Key": file_name, "ContentType": content_type},
        ExpiresIn=3600,
    )
    return jsonify({"url": presigned_url})





@app.route("/profile", methods=["POST"])
def profile():
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
    return jsonify({"message": "Profile created successfully"})







@app.route("/dashboard", methods=["GET"])
def dashboard():
    profiles = User.query.all()
    return jsonify(user_schema.dump(profiles))







if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
