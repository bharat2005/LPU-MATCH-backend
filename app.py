from flask import Flask, request, jsonify, make_response, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_marshmallow import Marshmallow
import hashlib
import base64
import os
from werkzeug.utils import secure_filename
import boto3
from datetime import datetime
from lpu import verify_user_shallow, verify_user_deep
import random
from flask_socketio import SocketIO, join_room
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager


app = Flask(__name__)

CORS(app, supports_credentials=True, origins=["http://localhost:3003"])

app.config["JWT_SECRET_KEY"] = "dev_secret_key"
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_ACCESS_COOKIE_NAME"] = "access_token"
app.config["JWT_COOKIE_SECURE"] = False  
app.config["JWT_COOKIE_SAMESITE"] = "Lax"  
app.config["JWT_COOKIE_CSRF_PROTECT"] = False


jwt = JWTManager(app)


socketio = SocketIO(app, cors_allowed_origins="*")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///hiii.db"
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
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    gender = db.Column(db.String())
    age = db.Column(db.Integer)
    images = db.Column(db.JSON)
    reason = db.Column(db.String())
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True

user_schema = UserSchema(many=True)
single_user_schema = UserSchema()

class Swipe(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    target_user_id = db.Column(db.Integer)
    swipe_action = db.Column(db.String())
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class SwipeSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Swipe
        load_instance = True

swipe_schema = SwipeSchema(many=True)
single_swipe_schema = SwipeSchema()

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer)
    user_1_id = db.Column(db.Integer)
    user_2_id = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class MatchSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Match
        load_instance = True

match_schema = MatchSchema(many=True)
single_match_schema = MatchSchema()

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_user_id = db.Column(db.Integer)
    receiver_user_id = db.Column(db.Integer)
    content = db.Column(db.String())
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class MessageSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Message
        load_instance = True

message_schema = MessageSchema(many=True)
single_message_schema = MessageSchema()


class Notifications(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_user_id = db.Column(db.Integer)
    receiver_user_id = db.Column(db.Integer)
    type = db.Column(db.String())
    is_seen = db.Column(db.String())
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class NotificationsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Notifications
        load_instance = True

notifications_schema = NotificationsSchema(many=True)
single_notifications_schema = NotificationsSchema()


class LpuData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String())
    name = db.Column(db.String())

class LpuDataSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = LpuData
        load_instance = True

lpuData_schema = LpuDataSchema(many=True)
single_lpuData_schema = LpuDataSchema()






def clean_base64(data):
    if not data:
        return None
    if data.startswith("data:image"):  
        data = data.split(",")[1] 
    
    missing_padding = len(data) % 4
    if missing_padding:
        data += "=" * (4 - missing_padding)
    
    return data





@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    reg_no, password = data["regNo"], data["password"]
    
    lpuDataX = LpuData.query.filter_by(id = data['user_id']).first()

    if lpuDataX:
        lpuData = verify_user_shallow(reg_no, password)
    else:
        lpuData = verify_user_deep(reg_no, password)

    if lpuData['status'] != 'Login Successful':
        return jsonify({'message': 'NoLogin'})
    
    if not lpuDataX:
        lpuDatacheck = LpuData.query.filter_by(name = lpuData['profile_name']).first()
    
    if not lpuDatacheck:
        base64_string = clean_base64(lpuData["profile_img_url"])
        image_data = base64.b64decode(base64_string)
        filename = secure_filename(f"{len(os.listdir('.')) + 1}.png")
        s3_key = f"uploads/{filename}"
        s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=s3_key, Body=image_data, ContentType="image/png")
        s3_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"

        db.session.add(LpuData(image=s3_url, name=lpuData['profile_name']))
        db.session.commit()

    if User.query.filter_by(user_id=data['user_id']).first() :
        user_exists = True
    else:
        user_exists = False
    
    access_token = create_access_token(identity=reg_no)
    response = jsonify({"message": "Login", 'nbool': user_exists})
    response.set_cookie("access_token", access_token, httponly=True, samesite="None", secure=True)
    
    return response



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
        name = data["name"],
        gender=data["gender"],
        age=data["age"],
        images=data["images"],
        reason=data["reason"],
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({"message":'Profile Created Successfully'})








@app.route("/dashboard", methods=["POST"])
def dashboard():
    data = request.get_json()
    lpuselfprofile = LpuData.query.filter_by(id = data['user_id']).first()
    selfprofile = User.query.filter_by(user_id = 1).first()
    profiles = User.query.filter(User.user_id != data['user_id'] ).all()
    random.shuffle(profiles)

    likesNoti = Notifications.query.filter((Notifications.receiver_user_id == data['user_id'])&(Notifications.type == 'like')).all()
    matchesNoti = Notifications.query.filter((Notifications.receiver_user_id == data['user_id'])&(Notifications.type == 'match')).all()

    return jsonify({'cards': user_schema.dump(profiles),
                    'lpuselfprofile':single_lpuData_schema.dump(lpuselfprofile),
                    'selfprofile': single_user_schema.dump(selfprofile), 
                    'likesNoti': notifications_schema.dump(likesNoti),
                    'matchesNoti': notifications_schema.dump(matchesNoti)})




@app.route("/filtered_dashboard", methods=["POST"])
def filtered_dashboard():
    data = request.get_json()
    age_min, age_max = data['ageRange']  
    gender = data['gender']  
    reason = data['reason']  

    filtered_profiles = User.query.filter(
        (User.age >= age_min)&
        (User.age <= age_max)&
        (User.gender == gender)&
        (User.reason == reason)&
        (User.user_id != data['user_id'] )
     ).all()

    return jsonify(user_schema.dump(filtered_profiles))


@app.route('/notidel',methods=["PATCH"])
def notidel():
    data = request.get_json()

    if 'target_user_id' in data:
        noti = Notifications.query.filter((Notifications.receiver_user_id == data['user_id'])&(Notifications.sender_user_id == data['target_user_id'])&(Notifications.type == 'like')).first()
        if noti:
            db.session.delete(noti)
            db.session.commit()

        likesNoti = Notifications.query.filter((Notifications.receiver_user_id == data['user_id'])&(Notifications.type == 'like')).all()

        return jsonify({'likesNoti':notifications_schema.dump(likesNoti)})
    
    elif 'sender_user_id' in data:
        noti = Notifications.query.filter((Notifications.receiver_user_id == data['user_id'])&(Notifications.sender_user_id == data['sender_user_id'])&(Notifications.type == 'match')).first()
        if noti:
            db.session.delete(noti)
            db.session.commit()

        MatchesNoti = Notifications.query.filter((Notifications.receiver_user_id == data['user_id'])&(Notifications.type == 'like')).all()

        return jsonify({'MatchesNoti':notifications_schema.dump(MatchesNoti)})



@app.route('/delaccount', methods = ["POST"])  
def delaccount():
    data = request.get_json()
    user = User.query.filter_by(user_id = data['user_id']).first()
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message':'Account Deleted Successfully!'})






@app.route("/swipeadd", methods=["POST"])
def swipeadd():
    
    data = request.get_json()
    if data['swipe_action'] == 'right':
        swipe = Swipe(
            user_id=data['user_id'],
            target_user_id= data['target_user_id'],
            swipe_action=data['swipe_action'],
        )
        db.session.add(swipe)
        db.session.commit()
    
        notification = Notifications(
            sender_user_id = data['user_id'],
            receiver_user_id = data['target_user_id'],
            type = 'like',
            is_seen = 'unseen',
        )
        db.session.add(notification)
        db.session.commit()

    return jsonify({'message':'Added to Database'})




@app.route('/likes', methods=['POST'])
def likes():
    data = request.get_json()
    liked_users = Swipe.query.filter((Swipe.user_id == data['user_id']) & (Swipe.swipe_action == 'right')).all()
    liked_users_ids = [a.target_user_id for a in liked_users]
    liked_users_data = user_schema.dump(User.query.filter(User.user_id.in_(liked_users_ids)))

    likes_users = Swipe.query.filter((Swipe.target_user_id == data['user_id']) & (Swipe.swipe_action=="right")).all()
    likes_users_ids = [a.user_id for a in likes_users]
    likes_users_data = user_schema.dump(User.query.filter(User.user_id.in_(likes_users_ids)))

    return jsonify({'likedByYou':liked_users_data,'likesYou':likes_users_data})




@app.route('/likeno',methods=["POST"])
def likeno():
    data = request.get_json()
    match = Swipe.query.filter((Swipe.user_id == data['target_user_id']) & (Swipe.target_user_id == data['user_id'])).first()
    if match:
        db.session.delete(match)
        db.session.commit()
    else:
        print("User Not found")

    likes_users = Swipe.query.filter((Swipe.target_user_id == data['user_id']) & (Swipe.swipe_action=="right")).all()
    likes_users_ids = [a.user_id for a in likes_users]
    likes_users_data = user_schema.dump(User.query.filter(User.user_id.in_(likes_users_ids)))
    
    return jsonify({'likesYou':likes_users_data})





@app.route('/match', methods=['POST'])
def match():
    data = request.get_json()
    user_ids = sorted([data['user_id'], data['target_user_id']])
    
    unique_string = f"{user_ids[0]}_{user_ids[1]}"
    match_id = hashlib.md5(unique_string.encode()).hexdigest() 
    
    match = Match(
        user_1_id=user_ids[0],
        user_2_id=user_ids[1],
        match_id=match_id
    )
    
    db.session.add(match)
    db.session.commit()

    match = Swipe.query.filter((Swipe.user_id == data['target_user_id']) & (Swipe.target_user_id == data['user_id'])).first()
    if match:
        db.session.delete(match)
        db.session.commit()

    likes_users = Swipe.query.filter((Swipe.target_user_id == data['user_id']) & (Swipe.swipe_action=="right")).all()
    likes_users_ids = [a.user_id for a in likes_users]
    likes_users_data = user_schema.dump(User.query.filter(User.user_id.in_(likes_users_ids)))

    notification = Notifications(
        sender_user_id = data['user_id'],
        receiver_user_id = data['target_user_id'],
        type = 'match',
        is_seen = 'unseen'
    )
    db.session.add(notification)
    db.session.commit()

    return jsonify({'likesYou':likes_users_data})





@app.route('/matchdel',methods=['POST'])
def matchdel():
    data = request.get_json()

    match = Match.query.filter(((Match.user_1_id == data['user_1_id']) & (Match.user_2_id == data['user_2_id'])) |
                               ((Match.user_1_id == data['user_2_id']) & (Match.user_2_id == data['user_1_id']))).first()
    if match:
        db.session.delete(match)
        db.session.commit()
    
    messages = Message.query.filter(((Message.sender_user_id == data['user_1_id']) & (Message.receiver_user_id == data['user_2_id'])) |
                               ((Message.sender_user_id == data['user_2_id']) & (Message.receiver_user_id == data['user_1_id'])) ).all()

    if messages:
        for a in messages:
            db.session.delete(a)
            db.session.commit()
        
    matches = Match.query.filter((Match.user_1_id == data['user_1_id']) | (Match.user_2_id == data['user_1_id'])).all()
    match_users_ids = []

    for a in matches:
        if a.user_1_id == data['user_1_id']:  
            match_users_ids.append(a.user_2_id) 
        elif a.user_2_id == data['user_1_id']:  
            match_users_ids.append(a.user_1_id)

    match_users_data = user_schema.dump(User.query.filter(User.user_id.in_(match_users_ids)))


    noti = Notifications.query.filter((Notifications.receiver_user_id == data['user_1_id'])&(Notifications.sender_user_id == data['user_2_id'])&(Notifications.type == 'match')).first()
    if noti:
        db.session.delete(noti)
        db.session.commit()

    MatchesNoti = Notifications.query.filter((Notifications.receiver_user_id == data['user_1_id'])&(Notifications.type == 'like')).all()

    return jsonify({'matches':match_users_data, 'MatchesNoti':notifications_schema.dump(MatchesNoti)})
    






@app.route('/matches',methods=["POST"])
def matches():
    data = request.get_json()
    matches = Match.query.filter((Match.user_1_id == data['user_id']) | (Match.user_2_id == data['user_id'])).all()
    match_users_ids = []

    for a in matches:
        if a.user_1_id == data['user_id']:  
            match_users_ids.append(a.user_2_id) 
        elif a.user_2_id == data['user_id']:  
            match_users_ids.append(a.user_1_id)

    match_users_data = user_schema.dump(User.query.filter(User.user_id.in_(match_users_ids)))


    notifications = Notifications.query.filter((Notifications.receiver_user_id == data['user_id'])&(Notifications.type == 'message')).all()   
    notifications = notifications_schema.dump(notifications)

    return jsonify({'matches':match_users_data, 'notifications':notifications})



@app.route('/seen',methods=["POST"])
def seen():
    data = request.get_json()
    notifications = Notifications.query.filter((Notifications.sender_user_id == data['sender_id']) & (Notifications.receiver_user_id == data['user_id'])).all()
    for a in notifications:
        db.session.delete(a)
    db.session.commit()
    return jsonify({'message':'Notifications deleted successfully'})
   



@socketio.on("join_room")
def join_room_event(data):
    match = Match.query.filter(
        (Match.match_id == data['room']) &
        ((Match.user_1_id == data['user_id']) | (Match.user_2_id == data['user_id']))
        ).first()
    if match:
        join_room(data['room'])
    print(f"User joined room {data['room']}")



@socketio.on("bharat")
def handle_message(data):

    if 'message' in data:
        text = Message(
            sender_user_id=data['sender_id'],
            receiver_user_id=data['receiver_id'],
            content=data['message']
        )
        db.session.add(text)
        db.session.commit()

        if 'type' in data:
            notification = Notifications(
                sender_user_id = data['sender_id'],
                receiver_user_id = data['receiver_id'],
                type = data['type'],
                is_seen = data['is_seen'],
            )
            db.session.add(notification)
            db.session.commit()

    messages = Message.query.filter(
        ((Message.sender_user_id == data['sender_id']) & (Message.receiver_user_id == data['receiver_id'])) |
        ((Message.sender_user_id == data['receiver_id']) & (Message.receiver_user_id == data['sender_id']))
    ).order_by(Message.timestamp).all()
    messages = message_schema.dump(messages)

    socketio.emit("bharat", messages, room=data['room'])




if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
