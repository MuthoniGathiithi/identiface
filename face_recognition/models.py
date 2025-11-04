from django.db import models
from django.contrib.auth.models import User
import uuid

# Create your models here.

class Class(models.Model):
    title = models.CharField(max_length=200)
    time = models.TimeField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='classes')
    created_at = models.DateTimeField(auto_now_add=True)
    enrollment_code = models.CharField(max_length=12, unique=True, blank=True)  # Unique enrollment link code
    
    class Meta:
        verbose_name_plural = "Classes"
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Generate unique enrollment code if not exists
        if not self.enrollment_code:
            self.enrollment_code = str(uuid.uuid4())[:12].upper()
        super().save(*args, **kwargs)
    
    def get_student_count(self):
        return self.students.count()
    
    def get_enrollment_link(self, request):
        """Generate full enrollment URL"""
        from django.urls import reverse
        return request.build_absolute_uri(
            reverse('enroll_student', kwargs={'enrollment_code': self.enrollment_code})
        )


class Student(models.Model):
    name = models.CharField(max_length=200)
    student_id = models.CharField(max_length=50, unique=True)
    email = models.EmailField(blank=True, null=True)
    class_enrolled = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='students')
    face_encoding = models.TextField(blank=True, null=True)  # Store face encoding data
    registered_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.student_id})"


class AttendanceSession(models.Model):
    """Represents a single attendance-taking session for a class"""
    class_session = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='attendance_sessions')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)
    method = models.CharField(max_length=20, choices=[
        ('facial', 'Facial Recognition'),
        ('manual', 'Manual Entry')
    ], default='facial')
    photo1 = models.ImageField(upload_to='attendance_photos/', blank=True, null=True)
    photo2 = models.ImageField(upload_to='attendance_photos/', blank=True, null=True)
    photo3 = models.ImageField(upload_to='attendance_photos/', blank=True, null=True)
    processed = models.BooleanField(default=False)  # Has FastAPI processed the photos?
    processing_status = models.CharField(max_length=50, default='pending')  # pending, processing, completed, failed
    
    def __str__(self):
        return f"{self.class_session.title} - {self.date} - {self.method}"


class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    class_session = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='attendances')
    attendance_session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='records', null=True, blank=True)
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late')
    ], default='present')
    marked_by = models.CharField(max_length=20, choices=[
        ('facial', 'Facial Recognition'),
        ('manual', 'Manual Entry')
    ], default='facial')
    
    class Meta:
        unique_together = ['student', 'class_session', 'date']
    
    def __str__(self):
        return f"{self.student.name} - {self.class_session.title} - {self.date}"
