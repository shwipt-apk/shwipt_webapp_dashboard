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
textStory_ref = db.collection('textStories')
photoStory_ref = db.collection('photoStories')
feeds_ref = db.collection('feeds')
club_ref = db.collection('clubs')

@csrf_exempt
def get_text_story(request):
    if request.method == 'GET':
      try:
        data = json.loads(request.body)
        inputID = data.get('inputID')
        query = textStory_ref.order_by('postTime', direction=firestore.Query.DESCENDING)
        results = query.stream()

        if not inputID:
          return JsonResponse({'message': 'inputID attribute is required'}, status=400)
        
        else:
          user_ids = [user.id for user in db.collection('users').document(inputID).collection('connections').stream()]
          all_text_stories = [{"id": stories.id, "data": stories.to_dict()} for stories in results if stories.id in user_ids or stories.id == inputID]
          return JsonResponse({'message': 'Success', 'story_data': all_text_stories, 'textStories_count': len(all_text_stories)})
      except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)
    
    elif request.method == 'POST':
      try:
        data = json.loads(request.body)
        inputID = data.get('inputID')
        description = data.get('description')
        username = data.get('username')
        displayPic = data.get('displayPic')

        if not inputID:
          return JsonResponse({'message': 'inputID attribute is required'}, status=400)
        
        elif not description:
          return JsonResponse({'message': 'description attribute is required'}, status=400)
        
        elif not username:
          return JsonResponse({'message': 'username attribute is required'}, status=400)
        
        elif not displayPic:
          return JsonResponse({'message': 'displayPic attribute is required'}, status=400)
        
        else:
          textStory_ref.document(inputID).set({
            "description": description,
            "postTime": firestore.SERVER_TIMESTAMP,
            "uid": inputID,
            "username": username,
            "displayPic": displayPic,
            "likes": 0,
          })
          return JsonResponse({'status': 'Success', 'message': 'Text Story Created'})
      except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)
      
@csrf_exempt
def get_photo_story(request):
    if request.method == 'GET':
      try:
        data = json.loads(request.body)
        inputID = data.get('inputID')
        query = photoStory_ref.order_by('postTime', direction=firestore.Query.DESCENDING)
        results = query.stream()

        if not inputID:
          return JsonResponse({'message': 'inputID attribute is required'}, status=400)
        
        else:
          user_ids = [user.id for user in db.collection('users').document(inputID).collection('connections').stream()]
          all_photo_stories = [{"id": stories.id, "data": stories.to_dict()} for stories in results if stories.id in user_ids or stories.id == inputID]
          return JsonResponse({'message': 'Success', 'story_data': all_photo_stories, 'photoStories_count': len(all_photo_stories)})
      except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)
    
    elif request.method == 'POST':
      try:
        data = json.loads(request.body)
        inputID = data.get('inputID')
        description = data.get('description')
        username = data.get('username')
        displayPic = data.get('displayPic')
        imageUrl = data.get('imageUrl')

        if not inputID:
          return JsonResponse({'message': 'inputID attribute is required'}, status=400)
        
        elif not username:
          return JsonResponse({'message': 'username attribute is required'}, status=400)
        
        elif not displayPic:
          return JsonResponse({'message': 'displayPic attribute is required'}, status=400)
        
        elif not imageUrl:
          return JsonResponse({'message': 'imageUrl attribute is required'}, status=400)
        
        else:
          photoStory_ref.document(inputID).set({
            "description": description,
            "postTime": firestore.SERVER_TIMESTAMP,
            "uid": inputID,
            "username": username,
            "displayPic": displayPic,
            "likes": 0,
            "imageUrl": imageUrl
          })
          return JsonResponse({'status': 'Success', 'message': 'Photo Story Created'})
      except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)
      
@csrf_exempt
def get_worldwide_post(request):
    if request.method == 'GET':
      try:
        results = feeds_ref.order_by('postTime', direction=firestore.Query.DESCENDING).where("private", "==", False).stream()
        all_posts = [{"id": feed.id, "data": feed.to_dict()} for feed in results]
        return JsonResponse({'message': 'Success', 'feed_data': all_posts, 'feed_count': len(all_posts)})
      except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)
    
    elif request.method == 'POST':
      try:
        data = json.loads(request.body)
        inputID = data.get('inputID')
        description = data.get('description')
        username = data.get('username')
        displayPic = data.get('displayPic')
        imageUrl = data.get('imageUrl')
        postID = data.get('postID')

        if not inputID:
          return JsonResponse({'message': 'inputID attribute is required'}, status=400)
        
        elif not username:
          return JsonResponse({'message': 'username attribute is required'}, status=400)
        
        elif not displayPic:
          return JsonResponse({'message': 'displayPic attribute is required'}, status=400)
        
        elif not postID:
          return JsonResponse({'message': 'postID attribute is required'}, status=400)
        
        else:
          feeds_ref.document(inputID).set({
            "description": description,
            "postTime": firestore.SERVER_TIMESTAMP,
            "uid": inputID,
            "username": username,
            "displayPic": displayPic,
            "likes": 0,
            "comments": 0,
            "imageUrl": imageUrl,
            "private": False,
            "postID": postID
          })
          return JsonResponse({'status': 'Success', 'message': 'Worldwide Post Created'}, status=200)
      except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)
      
@csrf_exempt
def get_private_post(request):
    if request.method == 'GET':
      try:
        data = json.loads(request.body)
        inputID = data.get('inputID')
        results = feeds_ref.order_by('postTime', direction=firestore.Query.DESCENDING).where("private", "==", True).stream()

        if not inputID:
          return JsonResponse({'message': 'inputID attribute is required'}, status=400)
        
        else:
          user_ids = [user.id for user in db.collection('users').document(inputID).collection('connections').stream()]
          all_posts = [{"id": feed.id, "data": feed.to_dict()} for feed in results if feed.to_dict().get('uid') in user_ids]
          return JsonResponse({'message': 'Success', 'feed_data': all_posts, 'feed_count': len(all_posts)})
      except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)
    
    elif request.method == 'POST':
      try:
        data = json.loads(request.body)
        inputID = data.get('inputID')
        description = data.get('description')
        username = data.get('username')
        displayPic = data.get('displayPic')
        imageUrl = data.get('imageUrl')
        postID = data.get('postID')

        if not inputID:
          return JsonResponse({'message': 'inputID attribute is required'}, status=400)
        
        elif not username:
          return JsonResponse({'message': 'username attribute is required'}, status=400)
        
        elif not displayPic:
          return JsonResponse({'message': 'displayPic attribute is required'}, status=400)
        
        elif not postID:
          return JsonResponse({'message': 'postID attribute is required'}, status=400)
        
        else:
          feeds_ref.document(inputID).set({
            "description": description,
            "postTime": firestore.SERVER_TIMESTAMP,
            "uid": inputID,
            "username": username,
            "displayPic": displayPic,
            "likes": 0,
            "comments": 0,
            "imageUrl": imageUrl,
            "private": True,
            "postID": postID
          })
          return JsonResponse({'status': 'Success', 'message': 'Private Post Created'}, status=200)
      except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)
      
@csrf_exempt
def get_post_likes(request):
    if request.method == 'GET':
      try:
        data = json.loads(request.body)
        postID = data.get('postID')
        query = feeds_ref.document(postID).collection('likes').order_by('postTime', direction=firestore.Query.DESCENDING)
        results = query.stream()

        if not postID:
          return JsonResponse({'message': 'postID attribute is required'}, status=400)
        
        else:
          all_likes = [{"id": likes.id, "data": likes.to_dict()} for likes in results]
          return JsonResponse({'message': 'Success', 'likes_data': all_likes, 'likes_count': len(all_likes)})
      except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)
      
@csrf_exempt
def get_post_comments(request):
    if request.method == 'GET':
      try:
        data = json.loads(request.body)
        postID = data.get('postID')
        query = feeds_ref.document(postID).collection('comments').order_by('postTime', direction=firestore.Query.DESCENDING)
        results = query.stream()

        if not postID:
          return JsonResponse({'message': 'postID attribute is required'}, status=400)
        
        else:
          all_comments = [{"id": comments.id, "data": comments.to_dict()} for comments in results]
          return JsonResponse({'message': 'Success', 'comments_data': all_comments, 'comments_count': len(all_comments)})
      except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)
      
@csrf_exempt
def post_feed_likes(request):
    if request.method == 'POST':
      try:
        data = json.loads(request.body)
        postID = data.get('postID')
        uid = data.get('uid')
        displayPic = data.get('displayPic')
        username = data.get('username')

        if not postID:
          return JsonResponse({'message': 'postID attribute is required'}, status=400)
        
        elif not uid:
          return JsonResponse({'message': 'uid attribute is required'}, status=400)
        
        elif not displayPic:
          return JsonResponse({'message': 'displayPic attribute is required'}, status=400)
        
        elif not username:
          return JsonResponse({'message': 'username attribute is required'}, status=400)
        
        else:
          feeds_ref.document(postID).collection('likes').set({
            "postTime": firestore.SERVER_TIMESTAMP,
            "uid": uid,
            "username": username,
            "displayPic": displayPic,
          })
          return JsonResponse({'status': 'Success', 'message': 'Post Liked'})
      except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)
      
@csrf_exempt
def post_feed_comments(request):
    if request.method == 'POST':
      try:
        data = json.loads(request.body)
        postID = data.get('postID')
        uid = data.get('uid')
        displayPic = data.get('displayPic')
        username = data.get('username')
        comment = data.get('comment')

        if not postID:
          return JsonResponse({'message': 'postID attribute is required'}, status=400)
        
        elif not uid:
          return JsonResponse({'message': 'uid attribute is required'}, status=400)
        
        elif not displayPic:
          return JsonResponse({'message': 'displayPic attribute is required'}, status=400)
        
        elif not username:
          return JsonResponse({'message': 'username attribute is required'}, status=400)
        
        elif not comment:
          return JsonResponse({'message': 'comment attribute is required'}, status=400)
        
        else:
          feeds_ref.document(postID).collection('comments').set({
            "postTime": firestore.SERVER_TIMESTAMP,
            "uid": uid,
            "username": username,
            "displayPic": displayPic,
            "comment": comment,
            "likes": 0
          })
          return JsonResponse({'status': 'Success', 'message': 'Post Commented'})
      except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)

@csrf_exempt      
def get_user_club_post(request):
    if request.method == 'GET':
      try:
        data = json.loads(request.body)
        inputID = data.get('inputID')
      
        if not inputID:
          return JsonResponse({'message': 'inputID attribute is required'}, status=400)
    
        req_doc = user_ref.document(f"{inputID}")

        if req_doc.collection('joinedClubs'):
          joined_clubs_list = [doc.to_dict()["clubID"] for doc in req_doc.collection('joinedClubs').get()]

        if req_doc.collection('myClubs'):
          myclubs_list = [doc.to_dict()["clubID"] for doc in req_doc.collection('myClubs').get()]
    
        check_lst = set(joined_clubs_list + myclubs_list)
        final_lst = []
        
        for _ in check_lst:
          new_doc = club_ref.document(f"{_}")
          post_lst = [doc.to_dict() for doc in new_doc.collection('posts').get()]
        
        for _ in post_lst:
            final_lst.append({"id": _["postID"], "data": _})

        return JsonResponse({'status': 'Success', 'clubPost_data': final_lst, 'clubPost_count': len(final_lst)}, status=200)
      
      except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)