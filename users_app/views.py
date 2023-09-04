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
user_ref = db.collection('users')

@csrf_exempt
def get_user(request):
    if request.method == 'GET':
      try:
        data = json.loads(request.body)
        inputID = data.get('inputID')
        if not inputID:
          return JsonResponse({'message': 'inputID attribute is required'}, status=400)
        else:
          req_user = [doc.to_dict() for doc in user_ref.where("uid", "==", f"{inputID}").stream()]
          return JsonResponse({'message': 'Success', 'data': req_user})
      except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)

@csrf_exempt  
def get_alltime_popular(request):
    if request.method == 'GET':
      try:
        data = json.loads(request.body)
        inputID = data.get('inputID')
        gender = data.get('gender')
        country = data.get('country')
        query = user_ref.order_by('popularity', direction=firestore.Query.DESCENDING)
        results = query.stream()

        if not inputID:
          return JsonResponse({'message': 'inputID attribute is required'}, status=400)

        if not gender:
          return JsonResponse({'message': 'gender attribute is required'}, status=400)
        
        if not country:
          return JsonResponse({'message': 'country attribute is required'}, status=400)
        
        if gender == "Both":
          if country == "Worldwide":
            all_users = [{"id": user.id, "data": user.to_dict()} for user in results]
          else:
            all_users = [{"id": user.id, "data": user.to_dict()} for user in results if country == user.to_dict().get('country')]
        elif gender == "Male":
          if country == "Worldwide":
            all_users = [{"id": user.id, "data": user.to_dict()} for user in results if gender == user.to_dict().get('gender')]
          else:
            all_users = [{"id": user.id, "data": user.to_dict()} for user in results if country == user.to_dict().get('country') and gender == user.to_dict().get('gender')]
        else:
          if country == "Worldwide":
            all_users = [{"id": user.id, "data": user.to_dict()} for user in results if gender == user.to_dict().get('gender')]
          else:
            all_users = [{"id": user.id, "data": user.to_dict()} for user in results if  country == user.to_dict().get('country') and gender == user.to_dict().get('gender')]
        return JsonResponse({'message': 'Success', 'data': all_users, 'all_users': len(all_users)})
      except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)

@csrf_exempt
def get_weekly_popular(request):
    if request.method == 'GET':
      try:
        data = json.loads(request.body)
        inputID = data.get('inputID')
        gender = data.get('gender')
        country = data.get('country')
        query = user_ref.order_by('weekly_popularity', direction=firestore.Query.DESCENDING)
        results = query.stream()

        if not inputID:
          return JsonResponse({'message': 'inputID attribute is required'}, status=400)

        if not gender:
          return JsonResponse({'message': 'gender attribute is required'}, status=400)
        
        if not country:
          return JsonResponse({'message': 'country attribute is required'}, status=400)
        
        if gender == "Both":
          if country == "Worldwide":
            all_users = [{"id": user.id, "data": user.to_dict()} for user in results]
          else:
            all_users = [{"id": user.id, "data": user.to_dict()} for user in results if country == user.to_dict().get('country')]
        elif gender == "Male":
          if country == "Worldwide":
            all_users = [{"id": user.id, "data": user.to_dict()} for user in results if gender == user.to_dict().get('gender')]
          else:
            all_users = [{"id": user.id, "data": user.to_dict()} for user in results if country == user.to_dict().get('country') and gender == user.to_dict().get('gender')]
        else:
          if country == "Worldwide":
            all_users = [{"id": user.id, "data": user.to_dict()} for user in results if gender == user.to_dict().get('gender')]
          else:
            all_users = [{"id": user.id, "data": user.to_dict()} for user in results if  country == user.to_dict().get('country') and gender == user.to_dict().get('gender')]
        return JsonResponse({'message': 'Success', 'data': all_users, 'all_users': len(all_users)})
      except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)

@csrf_exempt
def get_active_user(request):
    if request.method == 'GET':
      try:
        data = json.loads(request.body)
        inputID = data.get('inputID')
        gender = data.get('gender')
        country = data.get('country')
        query = user_ref.order_by('last_active', direction=firestore.Query.DESCENDING)
        results = query.stream()

        if not inputID:
          return JsonResponse({'message': 'inputID attribute is required'}, status=400)

        if not gender:
          return JsonResponse({'message': 'gender attribute is required'}, status=400)
        
        if not country:
          return JsonResponse({'message': 'country attribute is required'}, status=400)
        
        if gender == "Both":
          if country == "Worldwide":
            all_users = [{"id": user.id, "data": user.to_dict()} for user in results if user.id != inputID and user.id != 'qrRjVYfpuWRjprkAfdINh7IZbAY2' and user.to_dict().get('active', True)]
          else:
            all_users = [{"id": user.id, "data": user.to_dict()} for user in results if user.id != inputID and user.id != 'qrRjVYfpuWRjprkAfdINh7IZbAY2' and country == user.to_dict().get('country') and user.to_dict().get('active', True)]
        elif gender == "Male":
          if country == "Worldwide":
            all_users = [{"id": user.id, "data": user.to_dict()} for user in results if user.id != inputID and user.id != 'qrRjVYfpuWRjprkAfdINh7IZbAY2' and gender == user.to_dict().get('gender') and user.to_dict().get('active', True)]
          else:
            all_users = [{"id": user.id, "data": user.to_dict()} for user in results if user.id != inputID and user.id != 'qrRjVYfpuWRjprkAfdINh7IZbAY2' and country == user.to_dict().get('country') and gender == user.to_dict().get('gender') and user.to_dict().get('active', True)]
        else:
          if country == "Worldwide":
            all_users = [{"id": user.id, "data": user.to_dict()} for user in results if user.id != inputID and user.id != 'qrRjVYfpuWRjprkAfdINh7IZbAY2' and gender == user.to_dict().get('gender') and user.to_dict().get('active', True)]
          else:
            all_users = [{"id": user.id, "data": user.to_dict()} for user in results if user.id != inputID and user.id != 'qrRjVYfpuWRjprkAfdINh7IZbAY2' and country == user.to_dict().get('country') and gender == user.to_dict().get('gender') and user.to_dict().get('active', True)]
        return JsonResponse({'message': 'Success', 'data': all_users, 'active_users': len(all_users)})
      except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)

@csrf_exempt
def get_active_friends(request):
    if request.method == 'GET':
      try:
        data = json.loads(request.body)
        inputID = data.get('inputID')
        gender = data.get('gender')
        country = data.get('country')

        if not inputID:
          return JsonResponse({'message': 'inputID attribute is required'}, status=400)
        
        if not gender:
          return JsonResponse({'message': 'gender attribute is required'}, status=400)
        
        if not country:
          return JsonResponse({'message': 'country attribute is required'}, status=400)
        
        req_doc = user_ref.document(f"{inputID}")
        active_connections = []
        if req_doc.collection('connections'):
          user_connections = [doc.to_dict() for doc in req_doc.collection('connections').get()]
          connection_uids = [connection['uid'] for connection in user_connections]

          if country == "Worldwide":
            if gender == "Both":
              active_users = (
                    user_ref
                    .where("uid", "in", connection_uids)
                    .where("active", "==", True)
                    .where("uid", "!=", 'qrRjVYfpuWRjprkAfdINh7IZbAY2')
                    .get()
              )
            
            elif gender == "Male":
              active_users = (
                    user_ref
                    .where("uid", "in", connection_uids)
                    .where("active", "==", True)
                    .where("uid", "!=", 'qrRjVYfpuWRjprkAfdINh7IZbAY2')
                    .where("gender", "==", "Male")
                    .get()
              )

            else:
              active_users = (
                    user_ref
                    .where("uid", "in", connection_uids)
                    .where("active", "==", True)
                    .where("uid", "!=", 'qrRjVYfpuWRjprkAfdINh7IZbAY2')
                    .where("gender", "==", "Female")
                    .get()
              )
            
          else:
            if gender == "Both":
              active_users = (
                    user_ref
                    .where("uid", "in", connection_uids)
                    .where("active", "==", True)
                    .where("uid", "!=", 'qrRjVYfpuWRjprkAfdINh7IZbAY2')
                    .get()
              )
            
            elif gender == "Male":
              active_users = (
                    user_ref
                    .where("uid", "in", connection_uids)
                    .where("active", "==", True)
                    .where("uid", "!=", 'qrRjVYfpuWRjprkAfdINh7IZbAY2')
                    .where("gender", "==", "Male")
                    .get()
              )

            else:
              active_users = (
                    user_ref
                    .where("uid", "in", connection_uids)
                    .where("active", "==", True)
                    .where("uid", "!=", 'qrRjVYfpuWRjprkAfdINh7IZbAY2')
                    .where("gender", "==", "Female")
                    .get()
              )

          active_connections = [
                    {"id": doc.id, "data": doc.to_dict()}
                    for doc in active_users
          ]
        
        else:
          return JsonResponse({'message': 'Failed', 'data': active_connections})
        
        return JsonResponse({'message': 'Success', 'data': active_connections, 'active_users': len(active_connections)})
      
      except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)
      
@csrf_exempt
def post_create_user(request):
    if request.method == 'POST':
      try:
        data = json.loads(request.body)
        uid = data.get('uid')
        user_ref.document(uid).set(data)
        return JsonResponse({'status': 'Success', 'message': 'User Created Successfully'})
      except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)
      
@csrf_exempt
def get_user_existence(request):
    if request.method == 'GET':
      try:
        data = json.loads(request.body)
        phone = data.get('phone')
        req_user = [doc.to_dict() for doc in user_ref.where("phone", "==", f"{phone}").stream()]
        if len(req_user) > 0:
          return JsonResponse({'status': 'Success', 'message': 'User Exists', 'exists': True})
        else:
          return JsonResponse({'status': 'Success', 'message': 'User Doesn\'t Exists', 'exists': False})
      except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)
      
@csrf_exempt
def put_edit_userProfile(request):
    if request.method == 'PUT':
      try:
        data = json.loads(request.body)
        inputID = data.get('inputID')
        user_ref.document(inputID).update(data)
        return JsonResponse({'status': 'Success', 'message': 'Profile Updated'})
      except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)