from django.shortcuts import render

def landing_page(request):
    return render(request, 'face_recognition/landing_page.html')

def signup(request):
    return render(request, 'face_recognition/signup.html')

def login(request):
    return render(request, 'face_recognition/login.html')

    
