from django.shortcuts import render

def landing_page(request):
    return render(request, 'face_recognition/landing_page.html')
