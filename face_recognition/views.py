from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Class, Student, Attendance
from datetime import datetime

def landing_page(request):
    return render(request, 'face_recognition/landing_page.html')

def signup(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # Create username from email (before @ symbol)
        username = email.split('@')[0]
        
        if password == confirm_password:
            if User.objects.filter(username=username).exists():
                # If username exists, add a number to make it unique
                counter = 1
                original_username = username
                while User.objects.filter(username=username).exists():
                    username = f"{original_username}{counter}"
                    counter += 1
            
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists')
            else:
                user = User.objects.create_user(
                    username=username, 
                    email=email, 
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                user.save()
                auth_login(request, user)
                messages.success(request, 'Account created successfully!')
                return redirect('dashboard')
        else:
            messages.error(request, 'Passwords do not match')
    
    return render(request, 'face_recognition/signup.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Get username from email
        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username
        except User.DoesNotExist:
            messages.error(request, 'Invalid email or password')
            return render(request, 'face_recognition/login.html')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            messages.success(request, 'Logged in successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email or password')
    
    return render(request, 'face_recognition/login.html')

@login_required(login_url='login')
def dashboard(request):
    from django.utils import timezone
    from django.db.models import Count, Q
    
    classes = Class.objects.filter(created_by=request.user).order_by('-created_at')
    total_classes = classes.count()
    
    # Calculate total students across all classes
    total_students = sum(cls.get_student_count() for cls in classes)
    
    # Get today's date
    today = timezone.now().date()
    
    # Calculate today's attendance statistics
    today_attendance = Attendance.objects.filter(
        class_session__created_by=request.user,
        date=today
    )
    
    total_present_today = today_attendance.filter(status='present').count()
    total_absent_today = today_attendance.filter(status='absent').count()
    total_late_today = today_attendance.filter(status='late').count()
    
    # Calculate attendance rate for today
    total_marked_today = today_attendance.count()
    attendance_rate = round((total_present_today / total_marked_today * 100), 1) if total_marked_today > 0 else 0
    
    # Get classes that haven't taken attendance today
    classes_with_attendance_today = today_attendance.values_list('class_session_id', flat=True).distinct()
    pending_classes = classes.exclude(id__in=classes_with_attendance_today)
    
    # Get today's absences with student details
    todays_absences = Attendance.objects.filter(
        class_session__created_by=request.user,
        date=today,
        status='absent'
    ).select_related('student', 'class_session')[:10]  # Limit to 10 recent
    
    context = {
        'classes': classes,
        'total_classes': total_classes,
        'total_students': total_students,
        'attendance_rate': attendance_rate,
        'total_absent_today': total_absent_today,
        'pending_classes_count': pending_classes.count(),
        'pending_classes': pending_classes,
        'todays_absences': todays_absences,
        'total_present_today': total_present_today,
        'total_late_today': total_late_today,
    }
    return render(request, 'face_recognition/dashboard.html', context)

@login_required(login_url='login')
def create_class(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        time = request.POST.get('time')
        
        if title and time:
            new_class = Class.objects.create(
                title=title,
                time=time,
                created_by=request.user
            )
            messages.success(request, f'Class "{title}" created successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please fill in all fields')
    
    return render(request, 'face_recognition/create_class.html')

@login_required(login_url='login')
def mark_attendance(request, class_id):
    """
    Mark attendance page - offers two options:
    1. Facial Recognition (upload 3 photos)
    2. Manual Entry (checkbox list)
    """
    class_obj = get_object_or_404(Class, id=class_id, created_by=request.user)
    students = class_obj.students.all()
    
    # Get today's date
    from django.utils import timezone
    today = timezone.now().date()
    
    # Check if attendance already taken today
    attendance_taken = Attendance.objects.filter(
        class_session=class_obj,
        date=today
    ).exists()
    
    context = {
        'class': class_obj,
        'students': students,
        'attendance_taken': attendance_taken,
        'enrollment_link': class_obj.get_enrollment_link(request),
    }
    return render(request, 'face_recognition/mark_attendance.html', context)


@login_required(login_url='login')
def mark_attendance_facial(request, class_id):
    """Handle facial recognition attendance via photo upload"""
    from .models import AttendanceSession
    from .face_api_client import FaceAPIClient
    from django.utils import timezone
    import json
    
    class_obj = get_object_or_404(Class, id=class_id, created_by=request.user)
    
    if request.method == 'POST':
        photo1 = request.FILES.get('photo1')
        photo2 = request.FILES.get('photo2')
        photo3 = request.FILES.get('photo3')
        
        if not all([photo1, photo2, photo3]):
            messages.error(request, 'Please upload all 3 photos')
            return redirect('mark_attendance', class_id=class_id)
        
        # Create attendance session
        session = AttendanceSession.objects.create(
            class_session=class_obj,
            created_by=request.user,
            method='facial',
            photo1=photo1,
            photo2=photo2,
            photo3=photo3,
            processing_status='processing'
        )
        
        # Call FastAPI to process photos
        api_client = FaceAPIClient()
        result = api_client.mark_attendance(
            class_code=class_obj.enrollment_code,
            image_files=[photo1, photo2, photo3]
        )
        
        if result['success']:
            # Mark students as present based on FastAPI response
            present_student_ids = result.get('present_students', [])
            
            for student in class_obj.students.all():
                if student.student_id in present_student_ids:
                    Attendance.objects.update_or_create(
                        student=student,
                        class_session=class_obj,
                        date=timezone.now().date(),
                        defaults={
                            'status': 'present',
                            'marked_by': 'facial',
                            'attendance_session': session
                        }
                    )
                else:
                    # Mark as absent if not detected
                    Attendance.objects.update_or_create(
                        student=student,
                        class_session=class_obj,
                        date=timezone.now().date(),
                        defaults={
                            'status': 'absent',
                            'marked_by': 'facial',
                            'attendance_session': session
                        }
                    )
            
            session.processed = True
            session.processing_status = 'completed'
            session.save()
            
            messages.success(request, f'Attendance marked! {len(present_student_ids)} students detected as present.')
        else:
            session.processing_status = 'failed'
            session.save()
            messages.error(request, f'Face recognition failed: {result.get("error", "Unknown error")}. Please try manual attendance.')
        
        return redirect('dashboard')
    
    return redirect('mark_attendance', class_id=class_id)


@login_required(login_url='login')
def mark_attendance_manual(request, class_id):
    """Handle manual attendance marking"""
    from django.utils import timezone
    
    class_obj = get_object_or_404(Class, id=class_id, created_by=request.user)
    
    if request.method == 'POST':
        # Get list of present student IDs from checkboxes
        present_ids = request.POST.getlist('present_students')
        
        # Create manual attendance session
        from .models import AttendanceSession
        session = AttendanceSession.objects.create(
            class_session=class_obj,
            created_by=request.user,
            method='manual',
            processed=True,
            processing_status='completed'
        )
        
        # Mark all students
        for student in class_obj.students.all():
            status = 'present' if str(student.id) in present_ids else 'absent'
            Attendance.objects.update_or_create(
                student=student,
                class_session=class_obj,
                date=timezone.now().date(),
                defaults={
                    'status': status,
                    'marked_by': 'manual',
                    'attendance_session': session
                }
            )
        
        messages.success(request, 'Attendance marked manually!')
        return redirect('dashboard')
    
    return redirect('mark_attendance', class_id=class_id)


def enroll_student(request, enrollment_code):
    """Student self-enrollment page with live webcam - accessed via unique link"""
    from django.http import JsonResponse
    from django.conf import settings
    import json
    
    # Get the class by enrollment code
    class_obj = get_object_or_404(Class, enrollment_code=enrollment_code)
    
    # Handle AJAX save request
    if request.method == 'POST' and request.headers.get('Content-Type') == 'application/json':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            student_id = data.get('student_id')
            email = data.get('email', '')
            
            # Check if student already enrolled
            if Student.objects.filter(student_id=student_id, class_enrolled=class_obj).exists():
                return JsonResponse({'success': False, 'error': 'You are already enrolled in this class'}, status=400)
            
            # Create student record
            Student.objects.create(
                name=name,
                student_id=student_id,
                email=email,
                class_enrolled=class_obj,
                face_encoding=''  # Stored in FastAPI database
            )
            
            return JsonResponse({'success': True, 'message': 'Successfully enrolled!'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    context = {
        'class': class_obj,
        'FACE_API_URL': getattr(settings, 'FACE_API_URL', 'http://localhost:8001'),
    }
    return render(request, 'face_recognition/enroll_student.html', context)


@login_required(login_url='login')
def enroll_student_manual(request, class_id):
    """
    Manual student enrollment by lecturer using live camera
    """
    from django.conf import settings
    
    class_obj = get_object_or_404(Class, id=class_id, created_by=request.user)
    
    context = {
        'class': class_obj,
        'FACE_API_URL': getattr(settings, 'FACE_API_URL', 'http://localhost:8001'),
    }
    return render(request, 'face_recognition/enroll_manual.html', context)


@login_required(login_url='login')
def save_enrollment(request):
    """
    Save enrollment data to Django database after FastAPI processing
    """
    from django.http import JsonResponse
    import json
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            student_id = data.get('student_id')
            email = data.get('email', '')
            class_id = data.get('class_id')
            enrollment_code = data.get('enrollment_code')
            
            # Get class
            class_obj = Class.objects.get(id=class_id, created_by=request.user)
            
            # Check if student already exists
            if Student.objects.filter(student_id=student_id, class_enrolled=class_obj).exists():
                return JsonResponse({'success': False, 'error': 'Student already enrolled'}, status=400)
            
            # Create student record
            Student.objects.create(
                name=name,
                student_id=student_id,
                email=email,
                class_enrolled=class_obj,
                face_encoding=''  # Stored in FastAPI database
            )
            
            return JsonResponse({'success': True, 'message': 'Student enrolled successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)


@login_required(login_url='login')
def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('landing_page')
    
