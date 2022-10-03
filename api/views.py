from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Q
from .models import *

# Create your views here.
@api_view(['POST'])
def user_view(request):
    if request.method == 'POST':
        return Response()


@api_view(['POST'])
def login_view(request):
    if request.method == 'POST':
        username = request.data['username']
        password = request.data['password']
        username_exists = User.objects.filter(Q(username=username) | Q(email=username)).last()
        data = {
            'message': 'Invalid Username',
            'username': None,
            'user_id': None
        }
        if username_exists:
            user = authenticate(request, username=username_exists.username, password=password)
            data['message'] = 'Successful' if user else 'Unsuccessful'
            data['username'] = user.username if user else None
            data['user_id'] = user.id if user else None
        return Response(data)