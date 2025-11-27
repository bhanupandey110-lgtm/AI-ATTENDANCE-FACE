from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # Admin
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('students/', views.student_list, name='student-list'),
    path('students/<int:pk>/', views.student_detail, name='student-detail'),
    path('students/<int:pk>/authorize/', views.student_authorize, name='student-authorize'),
    path('students/<int:pk>/edit/', views.student_edit, name='student-edit'),
    path('students/<int:pk>/delete/', views.student_delete, name='student-delete'),
    path('attendance-list/', views.student_attendance_list, name='student_attendance_list'),

    # Student
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student-attendance/', views.student_attendance, name='student_attendance'),
    path('student-fees/', views.student_fee_detail, name='student_fee_detail'),
]
