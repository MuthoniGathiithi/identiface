from django.contrib import admin
from .models import Class, Student, Attendance, AttendanceSession

# Register your models here.

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ['title', 'time', 'enrollment_code', 'created_by', 'created_at']
    list_filter = ['created_at', 'created_by']
    search_fields = ['title', 'enrollment_code']
    readonly_fields = ['enrollment_code']

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['name', 'student_id', 'email', 'class_enrolled', 'registered_at']
    list_filter = ['class_enrolled', 'registered_at']
    search_fields = ['name', 'student_id', 'email']

@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ['class_session', 'date', 'time', 'method', 'processing_status', 'created_by']
    list_filter = ['method', 'processing_status', 'date']
    search_fields = ['class_session__title']

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'class_session', 'date', 'time', 'status', 'marked_by']
    list_filter = ['status', 'marked_by', 'date', 'class_session']
    search_fields = ['student__name', 'student__student_id']
