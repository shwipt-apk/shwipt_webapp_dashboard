from flask import Flask
from firebase_admin import firestore
from django.http import JsonResponse
import json
import datetime
from django.views.decorators.csrf import csrf_exempt

# Setting up the flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = '123456789qwert'

# Setting up theFirebase Database
db = firestore.client()
admin_ref = db.collection('admin')
user_ref = db.collection('users')
club_ref = db.collection('clubs')
feed_ref = db.collection('feeds')
audio_room_ref = db.collection('audioRooms')
chat_room_ref = db.collection('chatRooms')
photo_stories_ref = db.collection('photoStories')
text_stories_ref = db.collection('textStories')

@csrf_exempt
def get_admin_details(request):
    if request.method == 'GET':
      try:
        admin_data = [doc.to_dict() for doc in admin_ref.stream()]
        return JsonResponse({'message': 'Success', 'data': admin_data})
      except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)

@csrf_exempt  
def put_admin_count(request):
    if request.method == 'PUT':
        new_chatRoomsCount = len([doc.to_dict() for doc in chat_room_ref.get()])
        new_clubCount = len([doc.to_dict() for doc in club_ref.get()])
        new_feedCount = len([doc.to_dict() for doc in feed_ref.get()])
        new_photoStoriesCount = len([doc.to_dict() for doc in photo_stories_ref.get()])
        new_audioRoomsCount = len([doc.to_dict() for doc in audio_room_ref.get()])
        new_textStoriesCount = len([doc.to_dict() for doc in text_stories_ref.get()])
        new_userCount = len([doc.to_dict() for doc in user_ref.get()])
        try:
            admin_ref.document("superAdmin").update({
                "chatRoomsCount": new_chatRoomsCount,
                "clubCount": new_clubCount,
                "feedCount": new_feedCount,
                "photoStoriesCount": new_photoStoriesCount,
                "audioRoomsCount": new_audioRoomsCount,
                "textStoriesCount": new_textStoriesCount,
                "userCount": new_userCount
            })
            return JsonResponse({'message': 'Success'}, status=200)
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)