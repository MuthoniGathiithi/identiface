from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create-class/', views.create_class, name='create_class'),
    path('mark-attendance/<int:class_id>/', views.mark_attendance, name='mark_attendance'),
    path('mark-attendance-facial/<int:class_id>/', views.mark_attendance_facial, name='mark_attendance_facial'),
    path('mark-attendance-manual/<int:class_id>/', views.mark_attendance_manual, name='mark_attendance_manual'),
    path('enroll-manual/<int:class_id>/', views.enroll_student_manual, name='enroll_student_manual'),
    path('save-enrollment/', views.save_enrollment, name='save_enrollment'),
    path('enroll/<str:enrollment_code>/', views.enroll_student, name='enroll_student'),
]