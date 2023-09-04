from flask import Flask, jsonify, request
from firebase_admin import credentials, initialize_app, firestore, auth
import phonenumbers
import pytz
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend
import datetime
from flask_mail import Mail, Message
from tzlocal import get_localzone
import base64
import os

# # creds = credentials.Certificate('serviceAccount.json')
creds = credentials.Certificate({
    "type": os.environ.get("type"),
    "project_id": os.environ.get("project_id"),
    "private_key_id": os.environ.get("private_key_id"),
    "private_key": os.environ.get("private_key").replace('\n', '\n'),
    "client_email": os.environ.get("client_email"),
    "client_id": os.environ.get("client_id"),
    "auth_uri": os.environ.get("auth_uri"),
    "token_uri": os.environ.get("token_uri"),
    "auth_provider_x509_cert_url": os.environ.get("auth_provider_x509_cert_url"),
    "client_x509_cert_url": os.environ.get("client_x509_cert_url")
})

# # account_sid = os.environ['TWILIO_ACCOUNT_SID']
# # auth_token = os.environ['TWILIO_AUTH_TOKEN']
# # client = Client(account_sid, auth_token)

# # Set up Twilio client
# account_sid = 
# auth_token = 
# client = Client(account_sid, auth_token)

default_app = initialize_app(creds)

# Setting up the flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = '123456789qwert'
sec_key = ""

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'mayurshinde0346@gmail.com'
app.config['MAIL_PASSWORD'] = 'drea hwxn dmjq fpic'  # Replace with your app password
app.config['MAIL_DEFAULT_SENDER'] = 'mayurshinde0346@gmail.com'

mail = Mail(app)

# Setting up theFirebase Database
db = firestore.client()
user_ref = db.collection('users')
club_ref = db.collection('clubs')
feed_ref = db.collection('feeds')
admin_ref = db.collection('admin')
rooms_ref = db.collection('rooms')
chat_room_ref = db.collection('chatRooms')
audio_room_ref = db.collection('audioRooms')
photo_stories_ref = db.collection('photoStories')
text_stories_ref = db.collection('textStories')
key_ref = db.collection('keys')
bug_ref = db.collection('bugs')
feedback_ref = db.collection('feedbacks')

#keys
private_key = None
public_key = None

# Index Route
@app.route('/')
def index():
    """index Route"""
    return jsonify({"Hello User": "Welcome to your Shwipt Api"})

################################### Auth Routes #########################################

@app.route('/auth/phone', methods=['POST'])
def authenticate_phone_number():
    """Create a new Firebase user with the provided phone number and return a verification ID.
    This function creates a new Firebase user with the phone number provided in the request body. The user is authenticated using Firebase Authentication service. Once the user is created, this function returns a verification ID that can be used to verify the user's phone number.
    Args:
    None
    Returns:
    A JSON object with the following key-value pair:
    - "verification_id": A string containing the verification ID for the newly created user.
    """
    phone_number = request.json["phone_number"]
    user = auth.create_user(phone_number=phone_number)
    verification_id = user.uid
    return {'verification_id': verification_id}

################################### Chat Encryption Routes #########################################

@app.route("/getKeys")
def get_keys():
    """Get a list of Base64 encoded public keys from Firebase."""
    # Retrieve documents from Firebase
    docs = key_ref.get()

    # Convert each pubKey from blob to Base64 encoded string
    pubkeys_b64 = [doc.to_dict()['pubKey'] for doc in docs]

    # Return the list of Base64 encoded strings as a JSON response
    return jsonify({"data": pubkeys_b64})

@app.route('/generate_keys', methods=['POST'])
def generate_keys():
    """Generate an RSA key pair, store the public key in Firebase, and return the private and public keys."""
    inputId = request.json['inputId']
    # generate new RSA keys
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()

    # serialize and return public key for storage
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    public_key_str = public_key_pem.decode('utf-8')

    private_key_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
    )
    private_key_bytes = private_key_pem
    
    # base64 encode private key for storage
    private_key_b64 = base64.b64encode(private_key_bytes).decode('utf-8')
    
    try:
        key_ref.document(f"{inputId}").set({
            "pubKey": public_key_str,
            "privKey": private_key_b64
        })
    except Exception as exp:
        return jsonify({"success": False, "error": exp})
    return {'private_key': private_key_b64, 'public_key': public_key_str}

@app.route('/send_message', methods=['POST'])
def send_message():
    """
    Endpoint for sending an encrypted message to a recipient.

    Expects a POST request with the following JSON payload:
    {
        "uid": "<sender user ID>",
        "message": "<message to send>",
        "rid": "<recipient user ID>"
    }

    Returns a JSON response with the following fields:
    {
        "success": <true if message was sent successfully>,
        "message": "<Base64-encoded encrypted message>"
    }
    """
    # retrieve message from request
    user_id = request.json["uid"]
    message = request.json['message']
    recipient_id = request.json['rid']
    #query the public key
    req_doc = key_ref.document(f"{recipient_id}").get()
    recipient_public_key_str = req_doc.to_dict()['pubKey']

    # load recipient public key
    recipient_public_key = serialization.load_pem_public_key(
        recipient_public_key_str.encode(),
        backend=default_backend()
    )

    # encrypt message using recipient's public key
    encrypted_message = recipient_public_key.encrypt(
        message.encode(),
        padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
        )
    )

    # send encrypted message to recipient
    # get the number of existing documents in the collection
    num_docs = len(user_ref.document(f"{user_id}").collection("sent_message").get())
    try:
        user_ref.document(f"{user_id}").collection("sent_message").document(f"message{num_docs+1}").set({
            "recipentUid": recipient_id,
            "message": base64.b64encode(encrypted_message).decode('utf-8')
        })
        return jsonify({"success": True, "message": base64.b64encode(encrypted_message).decode('utf-8')})
    except Exception as exp:
        return jsonify({"success": False, "error": exp})

@app.route('/receive_message', methods=['POST'])
def receive_message():
    """
    Endpoint for receiving and decrypting a message.

    Expects a POST request with the following JSON payload:
    {
        "uid": "<recipient user ID>",
        "rid": "<sender user ID>",
        "encrypted_message": "<Base64-encoded encrypted message>"
    }

    Returns a JSON response with the following fields:
    {
        "message": "<decrypted message>"
    }
    """
    # retrieve private key from Firestore
    uid = request.json["uid"]
    rid = request.json["rid"]
    encrypted_message_b64 = request.json["encrypted_message"]
    doc_ref = db.collection('keys').document(rid)
    doc = doc_ref.get()
    if not doc.exists:
        return jsonify({"error": "User not found."}), 404
    
    private_key_b64 = doc.to_dict().get('privKey')
    if not private_key_b64:
        return jsonify({"error": "Private key not found."}), 404
    
    private_key_bytes = base64.b64decode(private_key_b64.encode('utf-8'))
    private_key = serialization.load_pem_private_key(
        private_key_bytes,
        password=None,
        backend=default_backend()
    )
    
    # # retrieve encrypted message from Firestore
    # message_ref = db.collection('users').document(uid).collection('sent_message').document('test')
    # message = message_ref.get()
    # if not message:
    #     return jsonify({"error": "Message not found."}), 404
       
    # encrypted_message_b64 = message.to_dict().get('message')
    # if not encrypted_message_b64:
    #     return jsonify({"error": "Encrypted message not found."}), 404

    # decode Base64-encoded string into bytes
    encrypted_message_bytes = base64.b64decode(encrypted_message_b64)

    # print(encrypted_message_bytes)
    # print(private_key)
    # decrypt message using private RSA key
    decrypted_message = private_key.decrypt(
        encrypted_message_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    ).decode()

    return jsonify({"message": decrypted_message})

# ################################### WhatsApp Routes #######################################
# @app.route('/whatsapp/sendMessage', methods=["POST"])
# def send_whatsapp_msg():
#     phone = request.args.get('phone', type=int)
#     countryCode = request.args.get('countryCode', type=int)
#     message = client.messages.create(
#         from_='whatsapp:+14155238886',
#         body=request.json["message"],
#         to=f'whatsapp:+{countryCode}{phone}'
#         )
#     print(f"whatsapp:+{countryCode}{phone}")
#     return jsonify(message.sid)

################################### Send Email Routes #####################################
@app.route('/sendEmail', methods=['POST'])
def send_email():
    """doc"""
    sender = request.json.get('sender')
    recipient = request.json.get('recipient')
    subject = request.json.get('subject')
    body = request.json.get('body')

    msg = Message(subject=subject, sender=sender, recipients=[recipient])
    with app.open_resource('static/pdfs/test.pdf') as pdf:
        msg.attach(filename='test.pdf', data=pdf.read(), content_type='application/pdf')

    msg.body = body

    mail.send(msg)
    return jsonify({'message': 'Email sent successfully.'})

################################### Feeds Routes ##########################################

@app.route('/feeds/publicPosts')
def get_public_posts():
    """
    Returns a list of public posts that match the specified interests, sorted by post time and paginated. The user's timezone is used to convert the post time to the local time zone.
    """
    user_timezone = request.args.get('timeZone')
    page = request.args.get('page', default=1, type=int)
    page_size = request.args.get('page_size', default=10, type=int)
    interest = request.args.getlist('interest')
    
    local_tz = pytz.timezone(user_timezone)
    
    # Modify the query to filter by interest
    if interest:
        public_posts = [
            {
                **doc.to_dict(),
                "postTime": datetime.datetime.strptime(str(doc.to_dict().get("postTime")), '%Y-%m-%d %H:%M:%S.%f%z').replace(tzinfo=pytz.UTC).astimezone(local_tz).strftime('%A, %d %B %Y %I:%M:%S %p %Z')
            } for doc in feed_ref.where("private", "==", False).where("interest", "array_contains_any", interest).get()
        ]
    else:
        public_posts = [
            {
                **doc.to_dict(),
                "postTime": datetime.datetime.strptime(str(doc.to_dict().get("postTime")), '%Y-%m-%d %H:%M:%S.%f%z').replace(tzinfo=pytz.UTC).astimezone(local_tz).strftime('%A, %d %B %Y %I:%M:%S %p %Z')
            } for doc in feed_ref.where("private", "==", False).get()
        ]
    
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    
    paginated_posts = []
    for post in public_posts[start_index:end_index]:
        paginated_posts.append({
            "id": post["postID"],
            "data": post,
        })
    paginated_posts.reverse()

    final_lst = [{"total": len(paginated_posts), "data": paginated_posts}]
    return jsonify(final_lst)


@app.route('/feeds/connectionPosts')
def get_connection_posts():
    """
    Returns a list of private posts that are visible to the user's connections and match the specified interests, sorted by post time. The user's timezone is used to convert the post time to the local time zone.
    """
    inputId = request.args.get('inputId')
    user_timezone = request.args.get('timeZone')
    interest = request.args.getlist('interest')
    
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    
    final_lst = []
    
    req_doc = user_ref.document(f"{inputId}")
    if req_doc.collection('connections'):
        user_connections = [doc.to_dict()["uid"] for doc in req_doc.collection('connections').get()]
        user_connections.append(f"{inputId}") 

    query = feed_ref.where("private", "==", True)
    
    # Filter the posts by interest
    if interest:
        query = query.where("interest", "array_contains_any", interest)
        
    query = query.order_by('postTime', direction=firestore.Query.DESCENDING)
    results = query.stream()
    total_posts = [doc.to_dict()["postID"] for doc in results]

    for post in total_posts:
        for doc in feed_ref.where("postID", "==", f"{post}").where("private", "==", True).get():
            req_id = doc.to_dict()["uid"]
            if req_id in user_connections:
                local_tz = pytz.timezone(user_timezone)
                final_lst.append({
                    "id": req_id,
                    "data": {
                        **doc.to_dict(),
                        "postTime": datetime.datetime.strptime(str(doc.to_dict().get("postTime")), '%Y-%m-%d %H:%M:%S.%f%z').replace(tzinfo=pytz.UTC).astimezone(local_tz).strftime('%A, %d %B %Y %I:%M:%S %p %Z')
                    }
                })

    return jsonify(final_lst), 200

@app.route('/feeds/postComments')
def get_post_comments():
    """Returns a list of comments for the specified post, sorted by comment time. The user's timezone is used to convert the comment time to the local time zone. If there are no comments on the post, it returns a message indicating so."""
    postId = request.args.get('postId')
    user_timezone = request.args.get('timeZone')
    if not postId:
        return jsonify({"success": False, "Provide query" : "postId"}), 500
    req_doc = feed_ref.document(f"{postId}")
    if req_doc.collection("comments"):
        post_comments = [doc.to_dict() for doc in req_doc.collection('comments').get()]
        final_lst = []
        for comment in post_comments:
            local_tz = pytz.timezone(user_timezone)
            final_lst.append({
                "id": comment["uid"],
                "data": {
                    **comment,
                    "commentTime": datetime.datetime.strptime(str(comment.get("commentTime")), '%Y-%m-%d %H:%M:%S.%f%z').replace(tzinfo=pytz.UTC).astimezone(local_tz).strftime('%A, %d %B %Y %I:%M:%S %p %Z')
                }
            })
        return jsonify(final_lst), 200
    else:
        return jsonify("No Comments on the post"), 200
    
@app.route('/feeds/postLikes')
def get_post_likes():
    """retrieves likes for a post and converts likeTime to the user's timezone"""
    postId = request.args.get('postId')
    user_timezone = request.args.get('timeZone')
    if not postId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    req_doc = feed_ref.document(f"{postId}")
    if req_doc.collection("likes"):
        post_likes = [doc.to_dict() for doc in req_doc.collection('likes').get()]
        local_tz = pytz.timezone(user_timezone)
        final_lst = []
        for like in post_likes:
            final_lst.append({
                "id": like["uid"],
                "data": {
                    **like,
                    "likeTime": datetime.datetime.strptime(str(like["likeTime"]), '%Y-%m-%d %H:%M:%S.%f%z').replace(tzinfo=pytz.UTC).astimezone(local_tz).strftime('%A, %d %B %Y %I:%M:%S %p %Z')
                }
            })
        return jsonify(final_lst), 200
    else:
        return jsonify("No Likes on the post"), 200

@app.route("/feeds/likeExists")
def get_like_exists():
    """checks if a user has liked a post"""
    # To get postId
    postId = request.args.get('postId')
    if not postId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    # To get inputId
    inputId = request.args.get('inputId')
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    # Get post likes
    req_doc = feed_ref.document(f"{postId}")
    if req_doc.collection("likes"):
        post_likes = [doc.to_dict()["uid"] for doc in req_doc.collection('likes').get()]
    like_exists = False
    for _ in post_likes:
        if _ == inputId:
            like_exists = True
    return jsonify({"like-exists":like_exists}), 200    

@app.route('/feeds/photoStories')
def get_photo_stories():
    """retrieves and formats photo stories for a user in descending order by post time."""
    inputId = request.args.get('inputId')
    user_timezone = request.args.get('timeZone')
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    # Get the local time zone
    local_tz = pytz.timezone(user_timezone)

    query = photo_stories_ref.order_by(
            'postTime', direction=firestore.Query.DESCENDING
            )
    results = query.stream()
    
    photo_stories = [doc.to_dict() for doc in results]

    final_lst = []
    for _ in photo_stories:
        _["postTime"] = datetime.datetime.strptime(str(_["postTime"]), '%Y-%m-%d %H:%M:%S.%f%z').replace(tzinfo=pytz.UTC).astimezone(local_tz).strftime('%A, %d %B %Y %I:%M:%S %p %Z')
        if _["uid"] == inputId:
            req_data = {"id": inputId, "data": _}
            final_lst.insert(0, req_data)
        else:
            final_lst.append({"id": _["uid"], "data": _})
    return jsonify(final_lst), 200

# @app.route('/feeds/textStories')
# def get_text_stories():
#     """doc6"""
#     inputId = request.args.get('inputId')
#     if not inputId:
#         return jsonify({"success": False, "Provide query" : "inputId"}), 500
#     # Get the local time zone
#     local_tz = get_localzone()

#     query = text_stories_ref.order_by(
#             'postTime', direction=firestore.Query.DESCENDING
#             )
#     results = query.stream()

#     text_stories = [doc.to_dict() for doc in results]
#     final_lst = []

#     for story in text_stories:
#         story["postTime"] = datetime.datetime.strptime(str(story["postTime"]), '%Y-%m-%d %H:%M:%S.%f%z').replace(tzinfo=pytz.UTC).astimezone(local_tz).strftime('%A, %d %B %Y %I:%M:%S %p %Z')
#         # final_lst.append({
#         #     "id": story["uid"],
#         #     "data": {
#         #         **story,
#         #         "postTime": story_time_local
#         #     }
#         # })
#     final_lst = []
#     for _ in text_stories:
#         _["postTime"] = datetime.datetime.strptime(str(_["postTime"]), '%Y-%m-%d %H:%M:%S.%f%z').replace(tzinfo=pytz.UTC).astimezone(local_tz).strftime('%A, %d %B %Y %I:%M:%S %p %Z')
#         if _["uid"] == inputId:
#             req_data = {"id": inputId, "data": _}
#             final_lst.insert(0, req_data)
#         else:
#             final_lst.append({"id": _["uid"], "data": _})
#     return jsonify(final_lst), 200
@app.route('/feeds/textStories')
def get_text_stories():
    """etrieves all text stories sorted by post time, with optional query parameters for inputId (the ID of the user whose stories should be prioritized) and timeZone (the user's local time zone)"""
    inputId = request.args.get('inputId')
    user_timezone = request.args.get('timeZone')
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    # Get the local time zone
    local_tz = pytz.timezone(user_timezone)

    query = text_stories_ref.order_by(
            'postTime', direction=firestore.Query.DESCENDING
            )
    results = query.stream()
    
    text_stories = [doc.to_dict() for doc in results]

    final_lst = []
    for _ in text_stories:
        _["postTime"] = datetime.datetime.strptime(str(_["postTime"]), '%Y-%m-%d %H:%M:%S.%f%z').replace(tzinfo=pytz.UTC).astimezone(local_tz).strftime('%A, %d %B %Y %I:%M:%S %p %Z')
        if _["uid"] == inputId:
            req_data = {"id": inputId, "data": _}
            final_lst.insert(0, req_data)
        else:
            final_lst.append({"id": _["uid"], "data": _})
    return jsonify(final_lst), 200
@app.route("/feeds/photoStories/likeExists")
def photo_story_like_exists():
    """checks if a user has liked a photo story, with query parameters for storyId (the ID of the story to check) and checkId (the ID of the user to check)"""
    storyId = request.args.get('storyId')
    if not storyId:
        return jsonify({"success": False, "Provide query" : "storyId"}), 500
    checkId = request.args.get('checkId')
    if not checkId:
        return jsonify({"success": False, "Provide query" : "checkId"}), 500
    req_doc = photo_stories_ref.document(f"{storyId}")
    if req_doc.collection("likes"):
        photo_story_likes = [doc.to_dict()["uid"] for doc in req_doc.collection('likes').get()]
    like_exists = False
    for _ in photo_story_likes:
        if _ == checkId:
            like_exists = True
    return jsonify({"like-exists":like_exists}), 200

@app.route("/feeds/textStories/likeExists")
def text_story_like_exists():
    """checks if a user has liked a text story, with query parameters for storyId (the ID of the story to check) and checkId (the ID of the user to check)"""
    storyId = request.args.get('storyId')
    if not storyId:
        return jsonify({"success": False, "Provide query" : "storyId"}), 500
    checkId = request.args.get('checkId')
    if not checkId:
        return jsonify({"success": False, "Provide query" : "checkId"}), 500
    req_doc = text_stories_ref.document(f"{storyId}")
    if req_doc.collection("likes"):
        text_story_likes = [doc.to_dict()["uid"] for doc in req_doc.collection('likes').get()]
    like_exists = False
    for _ in text_story_likes:
        if _ == checkId:
            like_exists = True
    return jsonify({"like-exists":like_exists}), 200

################################### User Routes ##########################################
@app.route('/users')
def get_user():
    """ retrieves user data for a specific user, with query parameter inputId (the ID of the user to retrieve data for)"""
    inputId = request.args.get('inputId')
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    req_user = [doc.to_dict() for doc in user_ref.where("uid", "==", f"{inputId}").stream()]
    return jsonify(req_user), 200

@app.route('/users/list')
def get_users():
    """retrieves a list of users sorted by popularity, with optional query parameters for inputId (the ID of the user making the request), country (a filter for users in a specific country), timeZone (the user's local time zone), page (the current page number), and page_size (the number of users to include per page)"""
    inputId = request.args.get('inputId')
    country = request.args.get('country')
    user_timezone = request.args.get('timeZone')
    page = request.args.get('page', default=1, type=int)
    page_size = request.args.get('page_size', default=10, type=int)
    if not country:
        query = user_ref.order_by(
            'popularity', direction=firestore.Query.DESCENDING
            )
        results = query.stream()
        all_users = [doc.to_dict() for doc in results]    
    else:
        query = user_ref.order_by(
            'popularity', direction=firestore.Query.DESCENDING
            )
        results = query.stream()
        all_users = []
        for doc in results:
            if doc.to_dict()["country"] == country:
                all_users.append(doc.to_dict())
            else:
                continue
    
    # Add timestamp formatting logic here
    final_lst = []
    local_tz = pytz.timezone(user_timezone)
    for user in all_users:
        user["last_active"] = datetime.datetime.strptime(str(user.get("last_active")), '%Y-%m-%d %H:%M:%S.%f%z').replace(tzinfo=pytz.UTC).astimezone(local_tz).strftime('%A, %d %B %Y %I:%M:%S %p %Z')
        if user["uid"] != inputId:
            final_lst.append({"id": user["uid"], "data": user})
        else:
            continue
        
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    paginated_users = []
    for user in final_lst[start_index:end_index]:
        paginated_users.append(user)
    last_lst = [{"total": len(paginated_users), "data": paginated_users}]
    return jsonify(last_lst), 200

@app.route('/users/list/weekly')
def get_weekly():
    """returns a list of all users sorted by their weekly popularity in descending order. The list is paginated, and the page size can be specified. The route takes three query parameters, inputId, timeZone, and page_size. The inputId parameter is the user id of the person requesting the list, the timeZone parameter is the time zone of the user, and the page_size parameter is the number of users to be returned per page. The route returns a JSON response with a list of users and their data."""
    inputId = request.args.get('inputId')
    user_timezone = request.args.get('timeZone')
    page = request.args.get('page', default=1, type=int)
    page_size = request.args.get('page_size', default=10, type=int)
    query = user_ref.order_by(
            'weekly_popularity', direction=firestore.Query.DESCENDING
            )
    results = query.get()
    all_users = [doc.to_dict() for doc in results]
    final_lst = []
    local_tz = pytz.timezone(user_timezone)
    for user in all_users:
        user["last_active"] = datetime.datetime.strptime(str(user.get("last_active")), '%Y-%m-%d %H:%M:%S.%f%z').replace(tzinfo=pytz.UTC).astimezone(local_tz).strftime('%A, %d %B %Y %I:%M:%S %p %Z')
        if user["uid"] != inputId:
            final_lst.append({"id": user["uid"], "data": user})
        else:
            continue
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    paginated_users = []
    for user in final_lst[start_index:end_index]:
        paginated_users.append(user)
    last_lst = [{"total": len(paginated_users), "data": paginated_users}]
    return jsonify(last_lst), 200

@app.route('/users/isActive')
def get_active_users():
    """returns a list of active users based on some filters. The route takes several query parameters, including inputId, timeZone, interest, gender, age_min, age_max, and countries. The inputId parameter is the user id of the person requesting the list, the timeZone parameter is the time zone of the user, and the other parameters are filters that can be applied to the list. The route returns a JSON response with a list of active users and their data."""
    # To get inputId
    inputId = request.args.get('inputId')
    user_timezone = request.args.get('timeZone')
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    page = request.args.get('page', default=1, type=int)
    page_size = request.args.get('page_size', default=10, type=int)
    # To get country
    interest = request.args.list('interest')
    gender = request.args.get('gender')
    age_min = request.args.get('age_min', type=int)
    age_max = request.args.get('age_max', type=int)
    countries = request.args.getlist('countries')

    query = user_ref.where("active", "==", True)

    if interest:
        query = query.where("interest", "array_contains_any", interest)
    if gender:
        query = query.where("gender", "==", f"{gender}")
    if age_min:
        query = query.where("age", ">=", age_min)
    if age_max:
        query = query.where("age", "<=", age_max)
    if countries:
        query = query.where("country", "in", countries)

    active_users = [doc.to_dict() for doc in query.get()]
    final_lst = []

    for _ in active_users:
        local_tz = pytz.timezone(user_timezone)
        final_lst.append({"id": _["uid"], "data": {
            **_,
            "last_active": datetime.datetime.strptime(str(_.get("last_active")), '%Y-%m-%d %H:%M:%S.%f%z').replace(tzinfo=pytz.UTC).astimezone(local_tz).strftime('%A, %d %B %Y %I:%M:%S %p %Z')
        }})
    for user in final_lst:
        if user["id"] == inputId:
            final_lst.remove(user)
        else:
            continue

    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    paginated_users = []
    for user in final_lst[start_index:end_index]:
        paginated_users.append(user)
    last_lst = [{"total": len(paginated_users), "data": paginated_users}]
    return jsonify(last_lst)

@app.route('/users/clubs')
def get_clubs():
    """returns a list of all clubs owned by a particular user. The route takes two query parameters, inputId and timeZone. The inputId parameter is the user id of the person requesting the list, and the timeZone parameter is the time zone of the user. The route returns a JSON response with a list of clubs and their data."""
    inputId = request.args.get('inputId')
    user_timezone = request.args.get('timeZone')
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    clubs = [doc.to_dict() for doc in club_ref.where("ownerID", "==", f"{inputId}").get()]
    final_lst = []
    for club in clubs:
        local_tz = pytz.timezone(user_timezone)
        final_lst.append({
            "id": club["clubID"],
            "data": {
                **club,
                "createTime": datetime.datetime.strptime(str(club.get("createTime")), '%Y-%m-%d %H:%M:%S.%f%z').replace(tzinfo=pytz.UTC).astimezone(local_tz).strftime('%A, %d %B %Y %I:%M:%S %p %Z')
            }
        })
    return jsonify(final_lst), 200


@app.route('/users/refer')
def get_refer_id():
    """returns the user ID of the person who referred a particular user. The route takes one query parameter, referCode. The referCode parameter is the referral code of the user whose referrer ID is being requested. The route returns a JSON response with the referrer ID and a success flag."""
    referCode = request.args.get('referCode')
    if not referCode:
        return jsonify({"success": False, "Provide query" : "referCode"}), 500
    req_id = 0
    for doc in user_ref.where("referCode", "==", f"{referCode}").get():
        req_id = doc.to_dict()["uid"]
    if req_id == 0:
        return jsonify({"referID": "Not Found", "Success": False})
    else:
        return jsonify({"referID":req_id, "Success": True})

@app.route('/users/block')
def get_block():
    """This route takes an inputId parameter and returns a list of all the users that are blocked by the user with the given inputId. The route queries the Firestore database to get the document of the user with the given inputId and then looks for any documents in the block subcollection of that user's document. For each document found, the route queries the Firestore database to get the document of the blocked user and adds it to a list of blocked users."""
    inputId = request.args.get('inputId')
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    block_lst = []
    req_doc = user_ref.document(f"{inputId}")
    if req_doc.collection('block'):
        user_block = [doc.to_dict() for doc in req_doc.collection('block').get()]
        for _ in user_block:
            req_id = _["uid"]
            for doc in user_ref.where("uid", "==", f"{req_id}").get():
                block_lst.append({"id": doc.to_dict()["uid"], "data": doc.to_dict()})
        return jsonify(block_lst), 200
    else:
        return jsonify("User has no Connections")

@app.route('/users/reports')
def get_reports():
    """This route takes an inputId parameter and returns a list of all the users that are reported by the user with the given inputId. The route works in a similar way to the /users/block route, except that it looks for documents in the reports subcollection of the user's document instead of the block subcollection."""
    inputId = request.args.get('inputId')
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    report_lst = []
    req_doc = user_ref.document(f"{inputId}")
    if req_doc.collection('block'):
        user_block = [doc.to_dict() for doc in req_doc.collection('reports').get()]
        for _ in user_block:
            req_id = _["uid"]
            for doc in user_ref.where("uid", "==", f"{req_id}").get():
                report_lst.append({"id": doc.to_dict()["uid"], "data": doc.to_dict()})
        return jsonify(report_lst), 200
    else:
        return jsonify("User has no Connections")

@app.route('/users/activeConnections')
def get_active_connections():
    """This route takes an inputId parameter and several optional parameters for filtering the results. The route returns a paginated list of all the users that are active connections of the user with the given inputId. The route first queries the Firestore database to get the document of the user with the given inputId and then looks for any documents in the connections subcollection of that user's document. For each document found, the route queries the Firestore database to get the document of the connected user and applies the requested filters to the query. The route also converts the last_active field of each connected user to the timezone specified by the timeZone parameter."""
    inputId = request.args.get('inputId')
    user_timezone = request.args.get('timeZone')
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    page = request.args.get('page', default=1, type=int)
    page_size = request.args.get('page_size', default=10, type=int)
    # To get array of countries
    countries = request.args.getlist('countries')
    # To get gender
    gender = request.args.get('gender')
    # To get array of interests
    interests = request.args.getlist('interest')
    # To get age range
    min_age = request.args.get('min_age')
    max_age = request.args.get('max_age')
    active_connections = []
    req_doc = user_ref.document(f"{inputId}")
    if req_doc.collection('connections'):
        user_connections = [doc.to_dict() for doc in req_doc.collection('connections').get()]
        for _ in user_connections:
            req_id = _["uid"]
            query = user_ref.where("uid", "==", f"{req_id}").where("active", "==", True)
            # Filter by countries
            if countries:
                query = query.where("country", "in", countries)
            # Filter by gender
            if gender:
                query = query.where("gender", "==", gender)
            # Filter by interests
            if interests:
                query = query.where("interests", "array_contains_any", interests)
            # Filter by age
            if min_age:
                query = query.where("age", ">=", int(min_age))
            if max_age:
                query = query.where("age", "<=", int(max_age))
            docs = query.get()
            for doc in docs:
                local_tz = pytz.timezone(user_timezone)
                active_connections.append({"id": doc.to_dict()["uid"], "data": {
                    **doc.to_dict(),
                    "last_active": datetime.datetime.strptime(str(doc.to_dict().get("last_active")), '%Y-%m-%d %H:%M:%S.%f%z').replace(tzinfo=pytz.UTC).astimezone(local_tz).strftime('%A, %d %B %Y %I:%M:%S %p %Z')
                }})
        #pagination
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_users = []
        for user in active_connections[start_index:end_index]:
            paginated_users.append(user)
        final_lst = [{"total": len(paginated_users), "data": paginated_users}]
        return jsonify(final_lst)
    else:
        return jsonify("User has no active Connections")


@app.route('/users/connections')
def get_connections():
    """This route takes an inputId parameter and returns a list of all the users that are connections of the user with the given inputId. The route works in a similar way to the /users/block and /users/reports routes, except that it looks for documents in the connections subcollection of the user's document instead of the block or reports subcollections."""
    inputId = request.args.get('inputId')
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    user_connections = []
    req_doc = user_ref.document(f"{inputId}")
    if req_doc.collection('connections'):
        user_conn = [doc.to_dict() for doc in req_doc.collection('connections').get()]
        for _ in user_conn:
            req_id = _["uid"]
            for doc in user_ref.where("uid", "==", f"{req_id}").get():
                user_connections.append({"id": doc.to_dict()["uid"], "data": doc.to_dict()})
        return jsonify(user_connections), 200
    else:
        return jsonify("User has no Connections")

@app.route('/users/joinedClubs')
def get_joined_clubs():
    """This route takes an inputId parameter and returns a list of all the clubs that the user with the given inputId has joined. The route queries the Firestore database to get the document of the user with the given inputId and then looks for any documents in the clubs subcollection of that user's document. For each document found, the route adds it to a list of joined clubs."""
    inputId = request.args.get('inputId')
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
     # To get users document
    req_doc = user_ref.document(f"{inputId}")
    
    # To Get joinedClubs uid list
    if req_doc.collection('joinedClubs'):
        joined_clubs_list = [doc.to_dict() for doc in req_doc.collection('joinedClubs').get()]
        final_lst = []
        for _ in joined_clubs_list:
            final_lst.append({"id": _["clubID"], "data": _})
        return jsonify(final_lst), 200
    else:
        return jsonify({"Sucsess": False})

@app.route('/users/inClub')
def get_in_club():
    """ It retrieves the club document with the given clubId and checks whether the inputId exists in the ownerID or members field of the document. It returns a JSON object with id, check, and role fields. The role field is set to "owner" if the inputId matches the ownerID, "member" if the inputId matches any member in the members field, and "explorer" if the inputId is not found."""
    inputId = request.args.get('inputId')
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    clubId = request.args.get('clubId')
    if not clubId:
        return jsonify({"success": False, "Provide query" : "clubId"}), 500
    req_doc = club_ref.document(f"{clubId}")

    if req_doc.collection('memebers'):
        member_lst = [doc.to_dict()["uid"] for doc in req_doc.collection('members').get()]
        owner_lst = [doc.to_dict()["ownerID"] for doc in club_ref.get()]
        if inputId in owner_lst:
            return jsonify({"id": inputId, "check": clubId, "role": "owner"})
        elif inputId in member_lst:
            return jsonify({"id": inputId, "check": clubId, "role": "memeber"})
        else:
            return jsonify({"id": inputId, "check": clubId, "role": "explorer"})
    else:
        return jsonify("Club has no memebers")

@app.route('/users/clubRooms')
def get_club_rooms():
    """It retrieves the club document with the given clubId and returns a list of room objects, where each object contains an id field and a data field that contains the room document's data."""
    clubId = request.args.get('clubId')
    if not clubId:
        return jsonify({"success": False, "Provide query" : "clubId"}), 500
     # To get users document
    req_doc = club_ref.document(f"{clubId}")
    
    # To Get joinedClubs uid list
    if req_doc.collection('rooms'):
        joined_clubs_list = [doc.to_dict() for doc in req_doc.collection('rooms').get()]
        final_lst = []
        for _ in joined_clubs_list:
            final_lst.append({"id": _["clubID"], "data": _})
        return jsonify(final_lst), 200
    else:
        return jsonify({"Sucsess": False})
    
@app.route('/users/notification')
def get_user_notification():
    """It retrieves the user document with the given inputId and returns a list of notification objects, where each object contains an id field and a data field that contains the notification document's data."""
    inputId = request.args.get('inputId')
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    req_doc = user_ref.document(f"{inputId}")

    if req_doc.collection('notifications'):
        notification_list = [doc.to_dict() for doc in req_doc.collection('notifications').get()]
        final_lst = []
        for _ in notification_list:
            final_lst.append({"id": _["uid"], "data": _})
        return jsonify(final_lst), 200
    else:
        return jsonify({"Sucsess": False})


@app.route('/users/clubs/posts')
def get_user_club_post():
    """It retrieves the user document with the given inputId and gets a list of club documents that the user has joined or created. For each club, it retrieves the posts collection and returns a list of post objects, where each object contains an id field and a data field that contains the post document's data."""
    inputId = request.args.get('inputId')
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    
    # To get users document
    req_doc = user_ref.document(f"{inputId}")

    # To Get joinedClubs uid list
    if req_doc.collection('joinedClubs'):
        joined_clubs_list = [doc.to_dict()["clubID"] for doc in req_doc.collection('joinedClubs').get()]

    # To Get myClub uid list
    if req_doc.collection('myClubs'):
        myclubs_list = [doc.to_dict()["clubID"] for doc in req_doc.collection('myClubs').get()]
    
    check_lst = set(joined_clubs_list + myclubs_list)
    final_lst = []
    for _ in check_lst:
        new_doc = club_ref.document(f"{_}")
        post_lst = [doc.to_dict() for doc in new_doc.collection('posts').get()]
        for _ in post_lst:
            final_lst.append({"id": _["postID"], "data": _})
    return jsonify(final_lst), 200

@app.route('/users/callHistory')
def get_call_history():
    """It retrieves the user document with the given inputId and returns a list of call history objects, where each object contains a caller_uid field and a data field that contains the call history document's data. Additionally, the function retrieves the recipient's profile data, including display picture, display name, device token, last active status, and active status, and adds them to the data field."""
    inputId = request.args.get('inputId')
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    req_doc = user_ref.document(f"{inputId}")

    if req_doc.collection('callHistory'):
        call_log = [doc.to_dict() for doc in req_doc.collection('callHistory').get()]
        final_lst = []
        for _ in call_log:
            req_id = _["caller_uid"]
            reciver_data = [doc.to_dict() for doc in user_ref.where("uid", "==", f"{req_id}").get()]
            _["dispalyPic"] = reciver_data[0]["displayPic"]
            _["dispalyName"] = reciver_data[0]["displayName"]
            _["device_token"] = reciver_data[0]["device_token"]
            _["last_active"] = reciver_data[0]["last_active"]
            _["active"] = reciver_data[0]["active"]
            final_lst.append({"caller_uid":req_id, "data": _})
        final_lst.reverse()
        return jsonify(final_lst), 200
    else:
        return jsonify({"Sucsess": False})
    
@app.route('/users/storyExixts')
def get_user_story_status():
    """It retrieves all photo and text story documents and checks whether the inputId exists in the uid field of any of the documents. It sets the ps variable to True if the user has a photo story and ts variable to True if the user has a text story. Finally, it returns a JSON object with ps and ts fields."""
    inputId = request.args.get('inputId')
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    photo_stories = [doc.to_dict() for doc in photo_stories_ref.get()]
    text_stories = [doc.to_dict() for doc in text_stories_ref.get()]
    ps = False
    ts = False
    for _ in photo_stories:
        if _["uid"] == inputId:
            ps = True
    for _ in text_stories:
        if _["uid"] == inputId:
            ps = True
    return jsonify({"Success": True, "photoStory-Exixts": ps, "textStory-Exixts": ts})

@app.route("/admin/count", methods=["GET"])
def get_admin_count():
    """Returns the count of documents in a Firestore collection named "admin"."""
    admin_data = [doc.to_dict() for doc in admin_ref.stream()]
    return jsonify(admin_data), 200

@app.route('/users/validate-phone', methods=['GET'])
def validate_phone():
    """Validates a phone number provided by the user and returns a JSON response indicating if the phone number is valid or not."""
    # Get the input from the user
    phone_number = request.args.get('number')
    country = request.args.get('country')

    # Convert the country code to a country name
    try:
        country_name = phonenumbers.region_code_for_country_code(int(country))
    except ValueError:
        country_name = country

    # Parse the phone number
    try:
        parsed_number = phonenumbers.parse(phone_number, country_name)
    except phonenumbers.NumberParseException:
        return ({'status':False,'valid': False})

    # Check if the phone number is valid
    is_valid = phonenumbers.is_valid_number(parsed_number)

    return jsonify({'status':True,'valid': is_valid})

@app.route('/connections/birthday')
def get_birthday_connections():
    """ Given an "inputId" and a "timeZone", this route retrieves documents from a Firestore collection named "connections" for a specific user, checks if the user's connections have a birthday today in their timezone, and returns a JSON response with the user's connections whose birthday is today."""
    inputId = request.args.get('inputId')
    user_timezone = request.args.get('timeZone')
    if not inputId:
        return jsonify({"success": False, "Provide query": "inputId"}), 500
    user_connections = []
    req_doc = user_ref.document(f"{inputId}")
    if req_doc.collection('connections'):
        user_conn = [doc.to_dict() for doc in req_doc.collection('connections').get()]
        today = datetime.now(pytz.timezone(user_timezone)).date()
        for _ in user_conn:
            req_id = _["uid"]
            for doc in user_ref.where("uid", "==", f"{req_id}").get():
                conn_data = doc.to_dict()
                dob = conn_data.get("dob")
                if dob:
                    dob = datetime.strptime(dob, '%Y-%m-%d').date()
                    if dob.month == today.month and dob.day == today.day:
                        user_connections.append({"id": doc.to_dict()["uid"], "data": doc.to_dict()})
    return jsonify(user_connections), 200
    


################################### Club Routes ##########################################
@app.route('/clubs/chatRooms')
def get_chat_rooms():
    """ retrieve all chat rooms associated with a club. Requires clubId query parameter. Returns a list of chat rooms in JSON format."""
    clubId = request.args.get('clubId')
    if not clubId:
        return jsonify({"success": False, "Provide query" : "clubId"}), 500
    req_doc = club_ref.document(f"{clubId}")
    if req_doc.collection('chatRooms'):
        chat_rooms_list = [doc.to_dict() for doc in req_doc.collection('chatRooms').get()]
        final_lst = []
        for _ in chat_rooms_list:
            final_lst.append({"id": _["roomID"], "data": _})
        return jsonify(final_lst), 200
@app.route('/clubs/getClub')
def get_club():
    """retrieve data of a club. Requires clubId query parameter. Returns club data in JSON format."""
    clubId = request.args.get('clubId')
    if not clubId:
        return jsonify({"success": False, "Provide query" : "clubId"}), 500
    club_data = [doc.to_dict() for doc in club_ref.where("clubID", "==", f"{clubId}").get()]
    final_lst = []
    for _ in club_data:
        final_lst.append({"id": _["clubID"], "data": _})
        return jsonify(final_lst), 200

@app.route('/clubs/getChatRoom')
def get_chat_room():
    """retrieve data of a specific chat room. Requires roomId query parameter. Returns chat room data in JSON format."""
    try:
        roomId = request.args.get('roomId')
        if not roomId:
            return jsonify({"success": False, "Provide query" : "roomId"}), 500
        req_room = chat_room_ref.document(f"{roomId}").get()
        if req_room.exists:
            req_data = req_room.to_dict()
            return jsonify({"id": req_data['ownerID'], "data": req_data, "success": True})
        else:
            return jsonify({"success": False, "Response": "Room does not exist"}), 404
    except Exception as exp:
        return jsonify({"success": False, "Response": f"An error occurred: {str(exp)}"}), 500

@app.route('/clubs/getAudioRoom')
def get_audio_room():
    """retrieve data of a specific audio room. Requires roomId query parameter. Returns audio room data in JSON format."""
    try:
        roomId = request.args.get('roomId')
        if not roomId:
            return jsonify({"success": False, "Provide query" : "roomId"}), 500
        req_room = audio_room_ref.document(f"{roomId}").get()
        if req_room.exists:
            req_data = req_room.to_dict()
            return jsonify({"id": req_data['ownerID'], "data": req_data, "success": True})
        else:
            return jsonify({"success": False, "Response": "Room does not exist"}), 404
    except Exception as exp:
        return jsonify({"success": False, "Response": f"An error occurred: {str(exp)}"}), 500

# @app.route('/clubs/members')
# def get_members():
#     clubId = request.args.get('clubId')
#     if not clubId:
#         return jsonify({"success": False, "Provide query" : "clubId"}), 500
#     req_doc = club_ref.document(f"{clubId}")
#     if req_doc.collection('members'):
#         members_list = [doc.to_dict() for doc in req_doc.collection('members').get()]
#         final_lst = []
#         club_data = club_ref.document(f"{clubId}").get()
#         for _ in members_list:
#             if _["uid"] == club_data.to_dict()['ownerID']:
#                 owner_data = _
#             else:
#                 final_lst.append({"id": _["uid"], "data": _})
#         final_lst.insert(0, {"id": club_data.to_dict()['ownerID'], "data": owner_data})
        
#         return jsonify(final_lst), 200
@app.route('/clubs/members')
def get_members():
    """It returns a JSON object with a list of dictionaries containing each member's information, including their unique ID uid and other data. The data also includes information about the club owner with the same format. If no members are found for the given clubId, it returns a 404 error. If an error occurs during the process, it returns a 500 error with an error message."""
    try:
        clubId = request.args.get('clubId')
        if not clubId:
            return jsonify({"success": False, "Provide query" : "clubId"}), 500
        req_doc = club_ref.document(f"{clubId}")
        if req_doc.collection('members').get():
            members_list = [doc.to_dict() for doc in req_doc.collection('members').get()]
            final_lst = []
            club_data = club_ref.document(f"{clubId}").get()
            for _ in members_list:
                if _["uid"] == club_data.to_dict()['ownerID']:
                    owner_data = _
                else:
                    final_lst.append({"id": _["uid"], "data": _})
            final_lst.insert(0, {"id": club_data.to_dict()['ownerID'], "data": owner_data})
            return jsonify(final_lst), 200
        else:
            return jsonify({"success": False, "Response": "No members found"}), 404
    except Exception as exp:
        return jsonify({"success": False, "Response": f"An error occurred: {str(exp)}"}), 500

################################### Swipe Routes ##########################################
@app.route('/swipe')
def get_swipe():
    """Retrieves a list of user IDs for swiping based on the input ID provided as a query parameter. Paginates the results based on page and page_size query parameters. Returns a JSON object with a "total" count and a "data" array containing user data."""
    inputId = request.args.get('inputId')
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    
    page = request.args.get('page', default=1, type=int)
    page_size = request.args.get('page_size', default=10, type=int)
    
    # To Get Request uid list
    user_list = [doc.to_dict()["uid"] for doc in user_ref.stream()]
    user_list.remove(inputId)

    # Get uid documnet
    req_doc = user_ref.document(f"{inputId}")
    
    # To Get Connections uid list
    connection_list = []
    if req_doc.collection('connections'):
        user_conn = [doc.to_dict()["uid"] for doc in req_doc.collection('connections').get()]
        for con in user_conn:
            for doc_conn in user_ref.where("uid", "==", f"{con}").get():
                connection_list.append(doc_conn.to_dict()["uid"])

    # To Get sentRequest uid list
    sent_request_list = []
    if req_doc.collection('sentRequests'):
        user_sreq = [doc.to_dict()["uid"] for doc in req_doc.collection('sentRequests').get()]
        for sreq in user_sreq:
            for doc_sreq in user_ref.where("uid", "==", f"{sreq}").get():
                sent_request_list.append(doc_sreq.to_dict()["uid"])

    # To Get Request uid list
    request_list = []
    if req_doc.collection('requests'):
        user_req = [doc.to_dict()["uid"] for doc in req_doc.collection('requests').get()]
        for req in user_req:
            for doc_req in user_ref.where("uid", "==", f"{req}").get():
                request_list.append(doc_req.to_dict()["uid"])
    
    # To Get Rejects uid list
    rejects_list = []
    if req_doc.collection('rejects'):
        user_req = [doc.to_dict()["uid"] for doc in req_doc.collection('rejects').get()]
        for req in user_req:
            for doc_req in user_ref.where("uid", "==", f"{req}").get():
                rejects_list.append(doc_req.to_dict()["uid"])

    # To get the swipe Result
    
    # for Request
    for user_id in connection_list:
        try:
            user_list.remove(user_id)
        except ValueError:
            pass
    
    # for sentRequests
    for user_id in request_list:
        try:
            user_list.remove(user_id)
        except ValueError:
            pass
    
    # for connections
    for user_id in sent_request_list:
        try:
            user_list.remove(user_id)
        except ValueError:
            pass
    
    # for rejects
    for user_id in rejects_list:
        try:
            user_list.remove(user_id)
        except ValueError:
            pass

    # Pagination
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    paginated_users = []
    for user in user_list[start_index:end_index]:
        for doc in user_ref.where("uid", "==", f"{user}").get():
            paginated_users.append({
                "id": user,
                "data": doc.to_dict()
        })
    final_lst = [{"total": len(paginated_users), "data": paginated_users}]
    return jsonify(final_lst)

@app.route('/swipe/choice', methods=["POST"])
def post_swipe_choice():
    """Accepts a swipe choice ("like" or "reject") and saves the swipe to the appropriate collection for the swipe ID and target ID provided as query parameters. Returns a JSON object indicating success or failure."""
    swipeId = request.args.get('swipeId')
    if not swipeId:
        return jsonify({"success": False, "Provide query" : "swipeId"}), 500
    targetId = request.args.get('targetId')
    if not targetId:
        return jsonify({"success": False, "Provide query" : "targetId"}), 500
    choice = request.args.get('choice')
    if not choice:
        return jsonify({"success": False, "Provide query" : "choice"}), 500
    
    if choice == "like":
        try:
            req_coll_s = user_ref.document(f'{swipeId}').collection('sentRequests')
            req_coll_t = user_ref.document(f'{targetId}').collection('requests')
            req_coll_s.document(f"{targetId}").set({
                "uid": targetId,
            })
            req_coll_t.document(f"{swipeId}").set({
                "uid": swipeId,
            })
            return jsonify({"Success": True})
        except Exception as exp:
            return jsonify({"Error": f"{exp}"})
    elif choice == "reject":
        try:
            req_coll_s = user_ref.document(f'{swipeId}').collection('rejects')
            req_coll_s.document(f"{targetId}").set({
                "uid": targetId,
            })
            return jsonify({"Success": True})
        except Exception as exp:
            return jsonify({"Error": f"{exp}"})
    else:
        return jsonify({"Success": False})

################################### Stories Routes ##########################################
@app.route('/views/photoStories', methods=["GET", "POST"])
def views_photoStories():
    """retrieves a list of views for a photo story, while a POST request adds a new view to the views collection for a photo story."""
    inputId = request.args.get('inputId')
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    storyId = request.args.get('storyId')
    if not storyId:
        return jsonify({"success": False, "Provide query" : "storyId"}), 500
    view_ref = photo_stories_ref.document(f"{storyId}").collection("views")
    if request.method == "GET":
        views = [doc.to_dict() for doc in view_ref.stream()]
        final_lst =[]
        for view in views:
            final_lst.append({"id": view["uid"], "data": view})
        return jsonify(final_lst), 200
    else:
        local_tz = get_localzone()
        timestamp = datetime.datetime.now().astimezone(local_tz)
        try:
            view_ref.document(f"{inputId}").set({
                "viewTime": timestamp,
                "like": False,
                "uid": inputId
            })
            return jsonify({"Sucess": True})
        except Exception as exp:
            return jsonify({"Error Occured": f"{exp}"})

@app.route('/views/textStories', methods=["GET", "POST"])
def views_textStories():
    """retrieves a list of views for a text story, while a POST request adds a new view to the views collection for a text story."""
    inputId = request.args.get('inputId')
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    storyId = request.args.get('storyId')
    if not storyId:
        return jsonify({"success": False, "Provide query" : "storyId"}), 500
    view_ref = text_stories_ref.document(f"{storyId}").collection("views")
    if request.method == "GET":
        views = [doc.to_dict() for doc in view_ref.stream()]
        final_lst =[]
        for view in views:
            final_lst.append({"id": view["uid"], "data": view})
        return jsonify(final_lst), 200
    else:
        local_tz = get_localzone()
        timestamp = datetime.datetime.now().astimezone(local_tz)
        try:
            view_ref.document(f"{inputId}").set({
                "viewTime": timestamp,
                "like": False,
                "uid": inputId
            })
            return jsonify({"Sucess": True})
        except Exception as exp:
            return jsonify({"Error Occured": f"{exp}"})

@app.route('/photoStory/likes')
def get_photo_story_likes():
    """retrieves a list of likes for a photo story."""
    storyId = request.args.get('storyId')
    if not storyId:
        return jsonify({"success": False, "Provide query" : "storyId"}), 500
    like_ref = photo_stories_ref.document(f"{storyId}").collection("likes")
    likes = [doc.to_dict() for doc in like_ref.stream()]
    final_lst =[]
    for like in likes:
        final_lst.append({"id": like["uid"], "data": like})
    return jsonify(final_lst), 200

@app.route('/textStory/likes')
def get_text_story_likes():
    """retrieves a list of likes for a text story."""
    storyId = request.args.get('storyId')
    if not storyId:
        return jsonify({"success": False, "Provide query" : "storyId"}), 500
    like_ref = text_stories_ref.document(f"{storyId}").collection("likes")
    likes = [doc.to_dict() for doc in like_ref.stream()]
    final_lst =[]
    for like in likes:
        final_lst.append({"id": like["uid"], "data": like})
    return jsonify(final_lst), 200


################################### Explore Clubs Routes ##########################################
@app.route("/exploreClubs")
def get_req_clubs():
    """
    Description: This endpoint returns a paginated list of clubs that the user has not joined or created.
    Method: GET
    Query Parameters:
    inputId: Required. User ID of the user who is making the request.
    page: Optional. Page number for pagination. Default is 1.
    age_size: Optional. Number of items per page for pagination. Default is 10.
    Returns: A JSON object containing the paginated list of clubs that the user has not joined or created.
    """

    #To get inputId query
    inputId = request.args.get('inputId')
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    
    page = request.args.get('page', default=1, type=int)
    page_size = request.args.get('page_size', default=10, type=int)

    club_list = [doc.to_dict()["clubID"] for doc in club_ref.stream()]
    
    # To get users document
    req_doc = user_ref.document(f"{inputId}")
    
    # To Get joinedClubs uid list
    if req_doc.collection('joinedClubs'):
        joined_clubs_list = [doc.to_dict()["clubID"] for doc in req_doc.collection('joinedClubs').get()]

    # To Get myClub uid list
    if req_doc.collection('myClubs'):
        myclubs_list = [doc.to_dict()["clubID"] for doc in req_doc.collection('myClubs').get()]
        
    # To get the exploreClubs Result
    # To remove joinedClubs
    for user_id in joined_clubs_list:
        try:
            club_list.remove(user_id)
        except ValueError:
            pass
    # To remove myClubs
    for user_id in myclubs_list:
        try:
            club_list.remove(user_id)
        except ValueError:
            pass
    # Pagination
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    paginated_clubs = []
    for club in club_list[start_index:end_index]:
        for doc in club_ref.where("clubID", "==", f"{club}").get():
            paginated_clubs.append({
                "id": club,
                "data": doc.to_dict()
        })
    final_lst = [{"total": len(paginated_clubs), "data": paginated_clubs}]
    return jsonify(final_lst)

################################### User Relation ##########################################
@app.route("/user/areConnected")
def get_are_connected():
    """
    Description: This endpoint checks whether two users are connected on the platform.
    Method: GET
    Query Parameters:
    firstId: Required. User ID of the first user to check.
    secondId: Required. User ID of the second user to check.
    Returns: A JSON object containing whether the two users are connected, and if so, how they are connected.
    """
    #To get firstId query
    firstId = request.args.get('firstId')
    if not firstId:
        return jsonify({"success": False, "Provide query" : "firstId"}), 500
    
    #To get secondId query
    secondId = request.args.get('secondId')
    if not secondId:
        return jsonify({"success": False, "Provide query" : "secondId"}), 500

    # Get uid documnet
    req_doc = user_ref.document(f"{firstId}")
    
    # To Get Request uid list
    connection_list = []
    if req_doc.collection('connections'):
        user_conn = [doc.to_dict()["uid"] for doc in req_doc.collection('connections').get()]
        for con in user_conn:
            for doc_conn in user_ref.where("uid", "==", f"{con}").get():
                connection_list.append(doc_conn.to_dict()["uid"])

    # To Get Request uid list
    sent_request_list = []
    if req_doc.collection('sentRequests'):
        user_sreq = [doc.to_dict()["uid"] for doc in req_doc.collection('sentRequests').get()]
        for sreq in user_sreq:
            for doc_sreq in user_ref.where("uid", "==", f"{sreq}").get():
                sent_request_list.append(doc_sreq.to_dict()["uid"])

    # To Get Request uid list
    request_list = []
    if req_doc.collection('requests'):
        user_req = [doc.to_dict()["uid"] for doc in req_doc.collection('requests').get()]
        for req in user_req:
            for doc_req in user_ref.where("uid", "==", f"{req}").get():
                request_list.append(doc_req.to_dict()["uid"])
    
    to_check = f'{secondId}'
    iscon = False
    issenq = False
    isreq = False

    if to_check in connection_list:
        iscon = True
        succ = True
    elif to_check in sent_request_list:
        issenq = True
        succ = True
    elif to_check in request_list:
        isreq = True
        succ = True
    else:
        succ = False
    
    return jsonify({"id": firstId , "check": secondId, "data": {"Connection" : iscon, "Sent-Request" : issenq, "Request" : isreq, "Success" : succ}})
################################### Latest APIs ############################################


################################### POST REQUESTS ##########################################
@app.route('/users/update', methods=["PUT"])
def update_data():
    """Updates user data."""

    #To get inputId query
    inputId = request.args.get('inputId')
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    gender = request.args.get('gender')
    age = request.args.get('age')
    phone = request.args.get('phone')
    email = request.args.get('email')
    displayPic = request.args.get('displayPic')
    username = request.args.get('username')
    data = []
    if gender:
        user_ref.document(f"{inputId}").update({
            "gender": gender,
        })
        data.append("gender")
    if age:
        user_ref.document(f"{inputId}").update({
            "age": int(age),
        })
        data.append("age")
    if phone:
        user_ref.document(f"{inputId}").update({
            "phone": phone,
        })
        data.append("phone")
    if email:
        user_ref.document(f"{inputId}").update({
            "email": email,
        })
        data.append("email")
    if displayPic:
        user_ref.document(f"{inputId}").update({
            "email": displayPic,
        })
        data.append("display")
    if username:
        username_list = [doc.to_dict()["username"] for doc in user_ref.stream()]
        if username not in username_list:
            user_ref.document(f"{inputId}").update({
                "username": username,
            })
            data.append("username")
        else:
            return jsonify({"Success": False, "Response": "Username already exists"})
    return jsonify({"Success": True, "field-updated": data})

@app.route('/users/updateSocials', methods=["PUT"])
def update_socials():
    """Updates user social media information."""

    #To get inputId query
    inputId = request.args.get('inputId')
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    snapchat = request.args.get('snapchat')
    twitter = request.args.get('twitter')
    whatsapp = request.args.get('whatsapp')
    instagram = request.args.get('instagram')
    data = []
    if snapchat:
        user_ref.document(f"{inputId}").update({
            "gender": snapchat,
        })
        data.append("snapchat")
    if twitter:
        user_ref.document(f"{inputId}").update({
            "age": twitter,
        })
        data.append("twitter")
    if whatsapp:
        user_ref.document(f"{inputId}").update({
            "phone": whatsapp,
        })
        data.append("whatsapp")
    if instagram:
        user_ref.document(f"{inputId}").update({
            "phone": whatsapp,
        })
        data.append("instagram")
    return jsonify({"Success": True, "field-updated": data})

@app.route('/users/textStories/add', methods=["POST"])
def add_text_story():
    """Adds a text story for a specific user."""
    #To get inputId query
    inputId = request.args.get('inputId')
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    req_user = [doc.to_dict() for doc in user_ref.where("uid", "==", f"{inputId}").stream()]
    dispalyPic = req_user[0]["displayPic"]
    username = req_user[0]["username"]
    local_tz = get_localzone()
    timestamp = datetime.datetime.now().astimezone(local_tz)
    # print(dispalyPic)
    try:
        text_stories_ref.document(f"{inputId}").set({
            "displayPic": dispalyPic,
            "description": request.json['description'],
            "likes": 0,
            "uid": inputId,
            "postTime": timestamp,
            "username": username,
        })
        return jsonify({"Sucsess": True})
    except Exception as exp:
        return jsonify({"Error Occured": f"{exp}"})

@app.route('/users/photoStories/add', methods=["POST"])
def add_photo_story():
    """adds a photo story for a user and stores it in the database"""
    #To get inputId query
    inputId = request.args.get('inputId')
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    req_user = [doc.to_dict() for doc in user_ref.where("uid", "==", f"{inputId}").stream()]
    dispalyPic = req_user[0]["displayPic"]
    username = req_user[0]["username"]
    local_tz = get_localzone()
    timestamp = datetime.datetime.now().astimezone(local_tz)
    # print(dispalyPic)
    try:
        photo_stories_ref.document(f"{inputId}").set({
            "displayPic": dispalyPic,
            "imageUrl": request.json['imageUrl'],
            "likes": 0,
            "uid": inputId,
            "postTime": timestamp,
            "username": username,
        })
        return jsonify({"Sucsess": True})
    except Exception as exp:
        return jsonify({"Error Occured": f"{exp}"})
    
@app.route('/modify/popularity', methods=["POST"])
def modify_pop():
    """modifies the popularity count of a user in the database"""
    inputId = request.args.get('inputId')
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    mod = request.args.get('mod')
    if not mod:
        return jsonify({"success": False, "Provide query" : "mod"}), 500
    value = int(request.args.get('value'))
    if not value:
        return jsonify({"success": False, "Provide query": "value"}), 500
    req_user = [doc.to_dict() for doc in user_ref.where("uid", "==", f"{inputId}").get()]

    if mod == "add":
        new_value = req_user[0]['popularity'] + value
        new_value_w = req_user[0]['popularity'] + value
    elif mod == "subtract":
        new_value = req_user[0]['popularity'] - value
        new_value_w = req_user[0]['popularity'] - value
    
    try:
        user_ref.document(f"{inputId}").update({
            "popularity": new_value,
            "weekly_popularity": new_value_w
        })
        return jsonify({"Sucsess": True})
    except Exception as exp:
        return jsonify({"Error Occured": f"{exp}"})
    
@app.route('/modify/diamonds', methods=["POST"])
def modify_diamonds():
    """modifies the number of diamonds of a user in the database"""
    inputId = request.args.get('inputId')
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    mod = request.args.get('mod')
    if not mod:
        return jsonify({"success": False, "Provide query" : "mod"}), 500
    value = int(request.args.get('value'))
    if not value:
        return jsonify({"success": False, "Provide query": "value"}), 500
    req_user = [doc.to_dict() for doc in user_ref.where("uid", "==", f"{inputId}").get()]

    if mod == "add":
        new_value = req_user[0]['diamonds'] + value
    elif mod == "subtract":
        new_value = req_user[0]['diamonds'] - value
    try:
        user_ref.document(f"{inputId}").update({
            "diamonds": new_value,
        })
        return jsonify({"Sucsess": True})
    except Exception as exp:
        return jsonify({"Error Occured": f"{exp}"})

@app.route('/modify/reset/weekly', methods=["POST"])
def modify_reset_weekly():
    """resets the weekly popularity count for all users in the database"""
    users = [doc.to_dict() for doc in user_ref.get()]
    for user in users:
        req_uid = user["uid"]
        user_ref.document(f"{req_uid}").update({
            "weekly_popularity": 0
            })
    return jsonify({"Sucsess": True})

@app.route('/create/user', methods=["POST"])
def create_user():
    """creates a new user and stores their information in the database"""
    inputId = request.args.get('inputId')
    tos = request.args.get('tos', type=bool)
    if not tos:
        return jsonify({"success": False, "Provide query" : "tos"}), 500
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    local_tz = get_localzone()
    timestamp = datetime.datetime.now().astimezone(local_tz)
    if tos is True:
        try:
            user_ref.document(f"{inputId}").set({
                "displayName": request.json['displayName'],
                "username": request.json['username'],
                "uid": inputId,
                "email": request.json['email'],
                "phone": request.json['phone'],
                "gender": request.json['gender'],
                "age": int(request.json['age']),
                "dob": request.json['dob'],
                "country": request.json['country'],
                "countryCode": request.json['countryCode'],
                "language": request.json['language'],
                "description": request.json['description'],
                "displayPic": request.json['displayPic'],
                "active": bool(request.json['active']),
                "popularity": int(request.json['popularity']),
                "weekly_popularity": int(request.json['weekly_popularity']),
                "posts": int(request.json['posts']),
                "connections": int(request.json['connections']),
                "swipePosts": int(request.json['swipePosts']),
                "diamonds": int(request.json['diamonds']),
                "referrals": int(request.json['referrals']),
                "referCode": request.json['referCode'],
                "isoCode": request.json['isoCode'],
                "interests": list(request.json['interests']),
                "last_active": timestamp,
                "flag": request.json['flag'],
                "snapchat": request.json['snapchat'],
                "instagram": request.json['instagram'],
                "twitter": request.json['twitter'],
                "whatsapp": request.json['whatsapp'],
                "searchName": list(request.json['searchName']),
                "device_token":request.json['device_token']
            })
            return jsonify({"Sucsess": True})
        except Exception as exp:
            return jsonify({"Error Occured": f"{exp}"})
    else:
        return jsonify({"Sucsess": False})
    
@app.route("/admin/count/update", methods=["PUT"])
def update_admin_count():
    """Update the count of different types of documents in the database and store it in the admin document."""
    new_chatRoomsCount = len([doc.to_dict() for doc in chat_room_ref.get()])
    new_clubCount = len([doc.to_dict() for doc in club_ref.get()])
    new_feedCount = len([doc.to_dict() for doc in feed_ref.get()])
    new_photoStoriesCount = len([doc.to_dict() for doc in photo_stories_ref.get()])
    new_roomsCount = len([doc.to_dict() for doc in rooms_ref.get()])
    new_textStoriesCount = len([doc.to_dict() for doc in text_stories_ref.get()])
    new_userCount = len([doc.to_dict() for doc in user_ref.get()])
    try:
        admin_ref.document("superAdmin").update({
            "chatRoomsCount": new_chatRoomsCount,
            "clubCount": new_clubCount,
            "feedCount": new_feedCount,
            "photoStoriesCount": new_photoStoriesCount,
            "roomsCount": new_roomsCount,
            "textStoriesCount": new_textStoriesCount,
            "userCount": new_userCount
        })
        return jsonify({"Sucsess": True})
    except Exception as exp:
        return jsonify({"Error Occured": f"{exp}"})

@app.route("/modify/clubs", methods=["PUT"])
def modify_club():
    """Modify the details of a club with the given club ID."""
    clubId = request.args.get('clubId')
    if not clubId:
        return jsonify({"success": False, "Provide query" : "clubId"}), 500
    clubName = request.args.get('clubName')
    try:
        club_ref.document(f"{clubId}").update({
            "clubName": request.json["clubName"],
            "description": request.json["description"],
            "imageUrl": request.json["imageUrl"]
        })
        return jsonify({"Sucsess": True})
    except Exception as exp:
        return jsonify({"Error Occured": f"{exp}"})

@app.route("/modify/refer", methods=["POST"])   
def increase_referral_count():
    """Increase the referral count of the user with the given referral code by 1, but only if it's less than 5."""
    referCode = request.args.get('referCode')
    if not referCode:
        return jsonify({"success": False, "Provide query" : "referCode"}), 500
    req_id = 0
    for doc in user_ref.where("referCode", "==", f"{referCode}").get():
        req_id = doc.to_dict()["uid"]
    if req_id == 0:
        return jsonify({"referID": "Not Found", "Success": False})
    else:
        user_data = user_ref.document(f"{req_id}").get()
        refer_count = int(user_data.to_dict()['referrals'])
        if refer_count >= 5:
            return jsonify({"success": False, "Response": "Refer Limit Reached"})
        else:
            user_ref.document(f"{req_id}").update({
                "referrals": (refer_count + 1)
            })
        return jsonify({"success": True})

@app.route("/modify/connection", methods=["POST"])
def modify_connection():
    """Add or remove a friend connection between two users with the given input and target IDs."""
    inputId = request.args.get('inputId')
    targetId = request.args.get('targetId')
    req_col = user_ref.document(f"{inputId}").collection('connections').document(f"{targetId}")
    if req_col.get().exists:
        req_col.delete()
        return jsonify({"success": True, "Response": "Friend Removed"})
    else:
        new_doc = user_ref.document(f"{inputId}").collection('connections').document(f"{targetId}")
        new_doc.set({
            "uid": targetId
        })
        return jsonify({"success": True, "Response": "Friend Added"})

@app.route("/create/post", methods=["POST"])
def create_post():
    """Create a new post with the given input ID, description, image URL, and privacy setting."""
    inputId = request.args.get('inputId')
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    req_user = [doc.to_dict() for doc in user_ref.where("uid", "==", f"{inputId}").stream()]
    dispalyPic = req_user[0]["displayPic"]
    username = req_user[0]["username"]
    displayName = req_user[0]["displayName"]
    local_tz = get_localzone()
    timestamp = datetime.datetime.now().astimezone(local_tz)
    posts = [doc.to_dict()["postID"] for doc in feed_ref.get()]
    post_id = f"Post-{len(posts)+1}"
    try:
        feed_ref.document(post_id).set({
            "comments":0,
            "description":request.json["description"],
            "displayName":displayName,
            "displayPic":dispalyPic,
            "imageUrl":request.json["imageUrl"],
            "likes":0,
            "postID":post_id,
            "postTime":timestamp,
            "private":request.json["private"],
            "uid": inputId,
            "username":username       
        })
        return jsonify({"Sucsess": True})
    except Exception as exp:
        return jsonify({"Error Occured": f"{exp}"})

# @app.route('/create/post', methods=["POST"])
# def create_post():
#     inputId = request.args.get('inputId')
#     if not inputId:
#         return jsonify({"success": False, "Provide query" : "inputId"}), 500
#     postId = request.args.get('postId')
#     if not postId:
#         return jsonify({"success": False, "Provide query" : "postId"}), 500
#     req_user = [doc.to_dict() for doc in user_ref.where("uid", "==", f"{inputId}").stream()]
#     dispalyPic = req_user[0]["displayPic"]
#     username = req_user[0]["username"]
#     local_tz = get_localzone()
#     timestamp = datetime.datetime.now().astimezone(local_tz)
#     try:
#         feed_ref.document(f"{postId}").set({
#             "comments": 0,
#             "description": request.json['description'],
#             "displayPic": dispalyPic,
#             "imageUrl": request.json['imageUrl'],
#             "likes": 0,
#             "uid": inputId,
#             "postTime": timestamp,
#             "username": username,
#         })
#         return jsonify({"Sucess": True})
#     except Exception as exp:
#         return jsonify({"Error Occured": f"{exp}"})

@app.route("/create/club", methods=["POST"])
def create_club():
    """This endpoint creates a new club with the provided name, description, image URL, owner ID, and privacy status. Returns a success response with the created club's details or an error message if an error occurs."""
    local_tz = get_localzone()
    timestamp = datetime.datetime.now().astimezone(local_tz)
    clubs = [doc.to_dict()["clubName"] for doc in club_ref.get()]
    club_id = f"Club-{len(clubs)+1}"
    if request.json["clubName"] not in clubs:
        try:
            club_ref.document(club_id).set({
                "clubID":club_id,
                "clubName":request.json["clubName"],
                "createTime":timestamp,
                "description":request.json["description"],
                "imageUrl":request.json["imageUrl"],
                "members":0,
                "ownerID":request.json["ownerID"],
                "private":request.json["private"]
            })
        except Exception as exp:
            return jsonify({"Error Occured": f"{exp}"})
    else:
        return jsonify({"success": False,"Response":"Club Name Already exists"})

@app.route("/create/audioRoom", methods=["POST"])
def create_audio_room():
    """This endpoint creates a new audio room with the provided name, description, image URL, owner ID, and associated club ID. Returns a success response with the created room's details or an error message if an error occurs."""
    local_tz = get_localzone()
    timestamp = datetime.datetime.now().astimezone(local_tz)
    rooms = [doc.to_dict()["roomName"] for doc in audio_room_ref.get()]
    room_id = f"AudioRoom-{len(rooms)+1}"
    if request.json["roomName"] not in rooms:
        try:
            audio_room_ref.document(room_id).set({
                "clubID":request.json["clubID"],
                "createTime":timestamp,
                "description":request.json["description"],
                "imageUrl":request.json["imageUrl"],
                "ownerID":request.json["ownerID"],
                "roomID": room_id,
                "roomName":request.json["roomName"],
            })
            return jsonify({"success": True, "Response": "Room Created"})
        except Exception as exp:
            return jsonify({"Error Occured": f"{exp}"})
    else:
        return jsonify({"success": False,"Response":"Room Name Already exists"})

@app.route("/create/chatRoom", methods=["POST"])
def create_chat_room():
    """This endpoint creates a new chat room with the provided name, description, image URL, owner ID, and associated club ID. Returns a success response with the created room's details or an error message if an error occurs."""
    local_tz = get_localzone()
    timestamp = datetime.datetime.now().astimezone(local_tz)
    rooms = [doc.to_dict()["roomName"] for doc in chat_room_ref.get()]
    room_id = f"ChatRoom-{len(rooms)+1}"
    if request.json["roomName"] not in rooms:
        try:
            chat_room_ref.document(room_id).set({
                "clubID":request.json["clubID"],
                "createTime":timestamp,
                "description":request.json["description"],
                "imageUrl":request.json["imageUrl"],
                "ownerID":request.json["ownerID"],
                "roomID": room_id,
                "roomName":request.json["roomName"],
            })
            return jsonify({"success": True, "Response": "Room Created"})
        except Exception as exp:
            return jsonify({"Error Occured": f"{exp}"})
    else:
        return jsonify({"success": False,"Response":"Room Name Already exists"})

@app.route("/clubs/report", methods=["POST"])
def report_club():
    """Report a club with a specific ID."""
    inputId = request.args.get('inputId')
    clubId = request.args.get('clubId')
    try:
        club_ref.document(f"{clubId}").collection("reports").document(f"{inputId}").set({
            "uid": inputId
        })
        return jsonify({"success": True, "Response": "Report Added"})
    except Exception as exp:
        return jsonify({"Error Occured": f"{exp}"})
    
@app.route("/chatRoom/report", methods=["POST"])
def report_chat_room():
    """Report a chat room with a specific ID."""
    inputId = request.args.get('inputId')
    roomId = request.args.get('roomId')
    try:
        chat_room_ref.document(f"{roomId}").collection("reports").document(f"{inputId}").set({
            "uid": inputId
        })
        return jsonify({"success": True, "Response": "Report Added"})
    except Exception as exp:
        return jsonify({"Error Occured": f"{exp}"})

@app.route("/audioRoom/report", methods=["POST"])
def report_audio_room():
    """Report an audio room with a specific ID."""
    inputId = request.args.get('inputId')
    roomId = request.args.get('roomId')
    try:
        audio_room_ref.document(f"{roomId}").collection("reports").document(f"{inputId}").set({
            "uid": inputId
        })
        return jsonify({"success": True, "Response": "Report Added"})
    except Exception as exp:
        return jsonify({"Error Occured": f"{exp}"})
    
@app.route("/post/report", methods=["POST"])
def report_post():
    """Report a post with a specific ID."""
    inputId = request.args.get('inputId')
    postId = request.args.get('postId')
    try:
        feed_ref.document(f"{postId}").collection("reports").document(f"{inputId}").set({
            "uid": inputId
        })
        return jsonify({"success": True, "Response": "Report Added"})
    except Exception as exp:
        return jsonify({"Error Occured": f"{exp}"})

@app.route("/photoStory/like", methods=["POST"])
def like_photoStory():
    """Adds a like to a photo story."""
    inputId = request.args.get('inputId')
    storyId = request.args.get('storyId')
    local_tz = get_localzone()
    timestamp = datetime.datetime.now().astimezone(local_tz)
    user_lst = [doc.to_dict() for doc in user_ref.where("uid", "==", f"{inputId}").get()]
    displayPic = user_lst[0]["displayPic"]
    username = user_lst[0]["username"]
    try:
        photo_stories_ref.document(f"{storyId}").collection("likes").document(f"{inputId}").set({
            "displayPic": displayPic,
            "postTime": timestamp,
            "uid": inputId,
            "username": username
        })
        return jsonify({"success": True, "Response": "Like Added"})
    except Exception as exp:
        return jsonify({"Error Occured": f"{exp}"})
    
@app.route("/photoStory/report", methods=["POST"])
def report_photo_story():
    """Reports a photo story."""
    inputId = request.args.get('inputId')
    storyId = request.args.get('storyId')
    try:
        photo_stories_ref.document(f"{storyId}").collection("reports").document(f"{inputId}").set({
            "uid": inputId
        })
        return jsonify({"success": True, "Response": "Report Added"})
    except Exception as exp:
        return jsonify({"Error Occured": f"{exp}"})

@app.route("/textStory/like", methods=["POST"])
def like_textStory():
    """ Adds a like to a text story."""
    inputId = request.args.get('inputId')
    storyId = request.args.get('storyId')
    local_tz = get_localzone()
    timestamp = datetime.datetime.now().astimezone(local_tz)
    user_lst = [doc.to_dict() for doc in user_ref.where("uid", "==", f"{inputId}").get()]
    displayPic = user_lst[0]["displayPic"]
    username = user_lst[0]["username"]
    try:
        text_stories_ref.document(f"{storyId}").collection("likes").document(f"{inputId}").set({
            "displayPic": displayPic,
            "postTime": timestamp,
            "uid": inputId,
            "username": username
        })
        return jsonify({"success": True, "Response": "Like Added"})
    except Exception as exp:
        return jsonify({"Error Occured": f"{exp}"})
    
@app.route("/textStory/report", methods=["POST"])
def report_text_story():
    """ Reports a text story."""
    inputId = request.args.get('inputId')
    storyId = request.args.get('storyId')
    try:
        text_stories_ref.document(f"{storyId}").collection("reports").document(f"{inputId}").set({
            "uid": inputId
        })
        return jsonify({"success": True, "Response": "Report Added"})
    except Exception as exp:
        return jsonify({"Error Occured": f"{exp}"})
    
@app.route("/post/like", methods=["POST"])
def like_post():
    """Adds a like to a post."""
    inputId = request.args.get('inputId')
    postId = request.args.get('postId')
    local_tz = get_localzone()
    timestamp = datetime.datetime.now().astimezone(local_tz)
    user_lst = [doc.to_dict() for doc in user_ref.where("uid", "==", f"{inputId}").get()]
    displayPic = user_lst[0]["displayPic"]
    username = user_lst[0]["username"]
    try:
        feed_ref.document(f"{postId}").collection("likes").document(f"{inputId}").set({
            "displayPic": displayPic,
            "postTime": timestamp,
            "uid": inputId,
            "username": username
        })
        return jsonify({"success": True, "Response": "Like Added"})
    except Exception as exp:
        return jsonify({"Error Occured": f"{exp}"})

@app.route("/post/comment", methods=["POST"])
def comment_post():
    """adds a comment to a post and stores it in a Firestore collection."""
    inputId = request.args.get('inputId')
    postId = request.args.get('postId')
    local_tz = get_localzone()
    timestamp = datetime.datetime.now().astimezone(local_tz)
    user_lst = [doc.to_dict() for doc in user_ref.where("uid", "==", f"{inputId}").get()]
    displayPic = user_lst[0]["displayPic"]
    username = user_lst[0]["username"]
    try:
        feed_ref.document(f"{postId}").collection("comments").document(f"{inputId}").set({
            "displayPic": displayPic,
            "postTime": timestamp,
            "description": request.json["description"],
            "uid": inputId,
            "username": username
        })
        return jsonify({"success": True, "Response": "Comment Added"})
    except Exception as exp:
        return jsonify({"Error Occured": f"{exp}"})
    
@app.route('/bugReport', methods=["POST"])
def send_bug_report():
    """adds a bug report and stores it in a Firestore document."""
    inputId = request.args.get('inputId')
    local_tz = get_localzone()
    timestamp = datetime.datetime.now().astimezone(local_tz)
    try:
        bug_ref.document(f"{inputId}").set({
            "uid": inputId,
            "reportTime": timestamp,
            "description": request.json["description"],
            "imageUrl": request.json["imageUrl"]
        })
        return jsonify({"success": True, "Response": "Bug Report Added"})
    except Exception as exp:
        return jsonify({"Error Occured": f"{exp}"})

@app.route('/feedback', methods=["POST"])
def send_feedback():
    """adds feedback and stores it in a Firestore document."""
    inputId = request.args.get('inputId')
    local_tz = get_localzone()
    timestamp = datetime.datetime.now().astimezone(local_tz)
    try:
        feedback_ref.document(f"{inputId}").set({
            "uid": inputId,
            "reportTime": timestamp,
            "description": request.json["description"],
            "stars": request.json["stars"]
        })
        return jsonify({"success": True, "Response": "feedback Added"})
    except Exception as exp:
        return jsonify({"Error Occured": f"{exp}"})
    
@app.route("/create/clubPost", methods=["POST"])
def create__club_post():
    """creates a post in a club and stores it in a Firestore collection."""
    inputId = request.args.get('inputId')
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    clubId = request.args.get('clubId')
    if not inputId:
        return jsonify({"success": False, "Provide query" : "clubId"}), 500
    req_user = [doc.to_dict() for doc in user_ref.where("uid", "==", f"{inputId}").stream()]
    dispalyPic = req_user[0]["displayPic"]
    username = req_user[0]["username"]
    displayName = req_user[0]["displayName"]
    local_tz = get_localzone()
    timestamp = datetime.datetime.now().astimezone(local_tz)
    posts = [doc.to_dict()["clubID"] for doc in club_ref.document(clubId).collection("posts").get()]
    post_id = f"Post-{len(posts)+1}"
    try:
        club_ref.document(clubId).collection("posts").document(f"{post_id}").set({
            "comments":0,
            "description":request.json["description"],
            "displayName":displayName,
            "displayPic":dispalyPic,
            "imageUrl":request.json["imageUrl"],
            "likes":0,
            "postID":post_id,
            "postTime":timestamp,
            "private":request.json["private"],
            "uid": inputId,
            "username":username       
        })
        return jsonify({"Sucsess": True})
    except Exception as exp:
        return jsonify({"Error Occured": f"{exp}"})

@app.route("/notification/send", methods=["POST"])
def send_notification():
    """Adds new notification in the notification subcollection of the given inputId"""
    inputId = request.args.get('inputId')
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    local_tz = get_localzone()
    timestamp = datetime.datetime.now().astimezone(local_tz)
    message = request.json["message"]
    try:
        user_ref.document(f"{inputId}").collection("notification").document(f"{inputId}").set({
            "uid":inputId,
            "time":timestamp,
            "description":message
        })
        return jsonify({"success": True, "Response": "Notification Added"})
    except Exception as exp:
        return jsonify({"Error Occured": f"{exp}"})

@app.route("/create/recentChat", methods=["POST"])
def create_recent_chat():
    """Code Remanning Template"""
    inputId = request.args.get('inputId')
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    targetId = request.args.get('targetId')
    if not targetId:
        return jsonify({"success": False, "Provide query" : "targetId"}), 500
    local_tz = get_localzone()
    local_tz = get_localzone()
    timestamp = datetime.datetime.now().astimezone(local_tz)
    message = request.json["message"]
    req_ref = user_ref.document(f"{inputId}").collection("messages").document(f"{targetId}")
    req_doc = req_ref.get()
    req_data = req_doc.to_dict()
    if req_doc.exists:
        totalMessage = req_data["totalMessage"]
        try:
            user_ref.document(f"{inputId}").collection("messages").document(f"{targetId}").set({
                "uid":targetId,
                "time":timestamp,
                "message":message,
                "read":False,
                "totalMessage":(int(totalMessage) + 1)
            })
            return jsonify({"success": True, "Response": "Message Added"})
        except Exception as exp:
            return jsonify({"Error Occured": f"{exp}"})
    else:
        try:
            user_ref.document(f"{inputId}").collection("messages").document(f"{targetId}").set({
                "uid":targetId,
                "time":timestamp,
                "message":message,
                "read":False,
                "totalMessage":0
            })
            return jsonify({"success": True, "Response": "Message Added"})
        except Exception as exp:
            return jsonify({"Error Occured": f"{exp}"})

@app.route("/recentChats/readStatus", methods=["PUT"])
def update_read_status():
    inputId = request.args.get('inputId')
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    targetId = request.args.get('targetId')
    if not targetId:
        return jsonify({"success": False, "Provide query" : "targetId"}), 500
    try:
        user_ref.document(f"{inputId}").collection("messages").document(f"{targetId}").update({
            "read":True,
            "totalMessage":0
        })
        return jsonify({"success": True, "Response": "Read Status Updated"})
    except Exception as exp:
        return jsonify({"Error Occured": f"{exp}"})

@app.route("/recentChats")
def get_recent_chat():
    """Code Remanning Template"""
    inputId = request.args.get('inputId')
    if not inputId:
        return jsonify({"success": False, "Provide query" : "inputId"}), 500
    req_doc = user_ref.document(f"{inputId}")

    if req_doc.collection('messages'):
        messages_list = [doc.to_dict() for doc in req_doc.collection('messages').get()]
        final_lst = []
        for _ in messages_list:
            final_lst.append({"id": _["uid"], "data": _})
        return jsonify(final_lst), 200
    else:
        return jsonify({"Sucsess": False})

    
if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
