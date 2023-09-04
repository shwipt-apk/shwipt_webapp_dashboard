from flask import Flask
from firebase_admin import firestore
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt

# Setting up the flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = '123456789qwert'

# Setting up theFirebase Database
db = firestore.client()
user_ref = db.collection('users')
club_ref = db.collection('clubs')

@csrf_exempt
def get_user_club(request):
    if request.method == 'GET':
      try:
        data = json.loads(request.body)
        inputID = data.get('inputID')
        if not inputID:
          return JsonResponse({'message': 'inputID attribute is required'}, status=400)
        
        else:
          clubs = [doc.to_dict() for doc in club_ref.where("ownerID", "==", f"{inputID}").stream()]
          return JsonResponse({'status': 'Success', 'data': clubs, 'clubs_count': len(clubs)}, status=200)
      except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)
        
@csrf_exempt
def get_joined_club(request):
    if request.method == 'GET':
      try:
        data = json.loads(request.body)
        inputID = data.get('inputID')
        if not inputID:
          return JsonResponse({'status': 'Failed', 'message': 'inputID attribute is required'}, status=400)
        
        else:
          req_doc = user_ref.document(f"{inputID}")
          joined_clubs_list = [doc.to_dict() for doc in req_doc.collection('joinedClubs').stream()]
          return JsonResponse({'status': 'Success', 'data': joined_clubs_list, 'clubs_count': len(joined_clubs_list)}, status=200)
      except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)
        
@csrf_exempt
def get_explore_club(request):
    if request.method == 'GET':
      try:
        data = json.loads(request.body)
        inputID = data.get('inputID')
        if not inputID:
          return JsonResponse({'status': 'Failed', 'message': 'inputID attribute is required'}, status=400)
        
        else:
          club_list = [doc.to_dict()["clubID"] for doc in club_ref.stream()]
          req_doc = user_ref.document(f"{inputID}")
          
          if req_doc.collection('joinedClubs'):
            joined_clubs_list = [doc.to_dict()["clubID"] for doc in req_doc.collection('joinedClubs').get()]
          
          # To Get myClub uid list
          if req_doc.collection('myClubs'):
            myclubs_list = [doc.to_dict()["clubID"] for doc in req_doc.collection('myClubs').get()]

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
          
          joined_clubs_list = [doc.to_dict() for doc in req_doc.collection('joinedClubs').stream()]
          return JsonResponse({'status': 'Success', 'data': club_list, 'clubs_count': len(club_list)}, status=200)
      except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)

@csrf_exempt
def post_join_club(request):
    if request.method == 'POST':
      try:
        data = json.loads(request.body)
        inputID = data.get('inputID')
        role = data.get('role')
        memberTime = data.get('memberTime')
        clubID = data.get('clubID')

        if not inputID:
          return JsonResponse({'status': 'Failed', 'message': 'inputID attribute is required'}, status=400)
        
        if not role:
          return JsonResponse({'status': 'Failed', 'message': 'role attribute is required'}, status=400)
        
        if not memberTime:
          return JsonResponse({'status': 'Failed', 'message': 'memberTime attribute is required'}, status=400)
        
        if not clubID:
          return JsonResponse({'status': 'Failed', 'message': 'clubID attribute is required'}, status=400)
        
        else:
          post_club_data = {"uid": inputID, "role": role, "memberTime": memberTime}
          post_user_data = {"clubID": clubID, "joinedTime": memberTime}
          club_ref.document(clubID).collection('members').document(inputID).set(post_club_data)
          user_ref.document(inputID).collection('joinedClubs').document(clubID).set(post_user_data)
          return JsonResponse({'status': 'Success', 'message': 'Joined Club Successfully'}, status=200)
      except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)
        
# @csrf_exempt
# def post_create_club(request):
#     if request.method == 'POST':
#         data = json.loads(request.body)
#         inputID = data.get('inputID')
#         role = data.get('role')
#         memberTime = data.get('memberTime')
#         clubName = data.get('clubName')

#         if not inputID:
#           return JsonResponse({'status': 'Failed', 'message': 'inputID attribute is required'}, status=400)
        
#         if not role:
#           return JsonResponse({'status': 'Failed', 'message': 'role attribute is required'}, status=400)
        
#         if not memberTime:
#           return JsonResponse({'status': 'Failed', 'message': 'memberTime attribute is required'}, status=400)
        
#         if not clubID:
#           return JsonResponse({'status': 'Failed', 'message': 'clubID attribute is required'}, status=400)
        
#         else:
#           post_club_data = {"uid": inputID, "role": role, "memberTime": memberTime}
#           post_user_data = {"clubID": clubID, "joinedTime": memberTime}
#           club_ref.document(clubID).collection('members').document(inputID).set(post_club_data)
#           user_ref.document(inputID).collection('joinedClubs').document(clubID).set(post_user_data)
#           return JsonResponse({'status': 'Success', 'message': 'Joined Club Successfully'}, status=200)