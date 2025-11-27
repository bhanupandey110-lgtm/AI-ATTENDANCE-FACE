import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.db.models import Sum, Q
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.http import JsonResponse, HttpResponseRedirect
from datetime import timedelta, datetime
from .models import Student, Attendance, Fee, FeePayment, CameraConfiguration, LateCheckInPolicy
from .forms import LateCheckInPolicyForm, StudentEditForm
from django.contrib.auth.models import User


##############################################
# HOME PAGE VIEW
##############################################
def home(request):
    if not request.user.is_authenticated:
        return render(request, 'home.html')

    if request.user.is_staff:
        return redirect('admin_dashboard')

    try:
        Student.objects.get(user=request.user)
        return redirect('student_dashboard')
    except Student.DoesNotExist:
        return render(request, 'home.html')


##############################################
# ADMIN CHECK
##############################################
def is_admin(user):
    return user.is_superuser


##############################################
# ADMIN DASHBOARD VIEW
##############################################
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    today = timezone.now().date()
    context = {
        'total_students': Student.objects.count(),
        'total_attendance': Attendance.objects.filter(date=today).count(),
        'total_present': Attendance.objects.filter(date=today, status='Present').count(),
        'total_absent': Attendance.objects.filter(date=today, status='Absent').count(),
        'total_late_checkins': Attendance.objects.filter(date=today, is_late=True).count(),
        'total_checkins': Attendance.objects.filter(date=today, check_in_time__isnull=False).count(),
        'total_checkouts': Attendance.objects.filter(date=today, check_out_time__isnull=False).count(),
        'total_cameras': CameraConfiguration.objects.count(),
    }
    return render(request, 'admin/admin-dashboard.html', context)


##############################################
# MARK ATTENDANCE UI PAGE (NO CAMERA)
##############################################
def mark_attendance(request):
    messages.info(request, "Face recognition app will be used for attendance.")
    return render(request, 'Mark_attendance.html')


##############################################
# REGISTER STUDENT
##############################################
def register_student(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            email = request.POST.get('email')
            phone_number = request.POST.get('phone_number')
            student_class = request.POST.get('student_class')
            username = request.POST.get('username')
            password = request.POST.get('password')

            if not username or not password:
                messages.error(request, "Username & Password required")
                return render(request, 'register_student.html')

            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already used")
                return render(request, 'register_student.html')

            user = User.objects.create_user(username=username, password=password, email=email)

            Student.objects.create(
                user=user, name=name, email=email,
                phone_number=phone_number, student_class=student_class,
                authorized=False
            )

            login(request, user)
            messages.success(request, "Registration Successful!")
            return redirect('register_success')

        except Exception as e:
            print(e)
            messages.error(request, "Registration failed")
            return render(request, 'register_student.html')

    return render(request, 'register_student.html')


def register_success(request):
    return render(request, 'register_success.html')


##############################################
# ADMIN - STUDENT ATTENDANCE LIST
##############################################
@login_required
@user_passes_test(is_admin)
def student_attendance_list(request):
    search_query = request.GET.get('search', '')
    date_filter = request.GET.get('attendance_date', '')

    students = Student.objects.all()

    if search_query:
        students = students.filter(name__icontains=search_query)

    student_attendance_data = []

    for student in students:
        records = Attendance.objects.filter(student=student)
        if date_filter:
            records = records.filter(date=date_filter)

        student_attendance_data.append({
            'student': student,
            'attendance_records': records.order_by('date')
        })

    return render(request, 'student_attendance_list.html', {
        'student_attendance_data': student_attendance_data,
        'search_query': search_query,
        'date_filter': date_filter,
    })


##############################################
# ADMIN - STUDENT LIST
##############################################
@staff_member_required
def student_list(request):
    return render(request, 'student_list.html', {'students': Student.objects.all()})


@staff_member_required
def student_detail(request, pk):
    return render(request, 'student_detail.html', {'student': get_object_or_404(Student, pk=pk)})


@staff_member_required
def student_authorize(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        student.authorized = True
        student.save()
        return redirect('student-detail', pk=pk)
    return render(request, 'student_authorize.html', {'student': student})


def student_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)
    form = StudentEditForm(request.POST or None, request.FILES or None, instance=student)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Student updated successfully")
        return redirect('student-detail', pk=pk)
    return render(request, 'student_edit.html', {'form': form, 'student': student})


@staff_member_required
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        student.delete()
        return redirect('student-list')
    return render(request, 'student_delete_confirm.html', {'student': student})


##############################################
# LOGIN / LOGOUT
##############################################
def user_login(request):
    if request.method == 'POST':
        user = authenticate(request,
                            username=request.POST.get('username'),
                            password=request.POST.get('password'))
        if user:
            login(request, user)
            try:
                Student.objects.get(user=user)
                return redirect('student_dashboard')
            except:
                return redirect('admin_dashboard')
        messages.error(request, 'Invalid Credentials')
    return render(request, 'login.html')


def user_logout(request):
    logout(request)
    return redirect('login')


##############################################
# STUDENT DASHBOARD
##############################################
@login_required
def student_dashboard(request):
    try:
        student = Student.objects.get(user=request.user)
    except:
        messages.error(request, "Student profile missing")
        return redirect('admin_dashboard')

    total_present = Attendance.objects.filter(student=student, status='Present').count()
    total_absent = Attendance.objects.filter(student=student, status='Absent').count()

    return render(request, 'student/student-dashboard.html', {
        'student': student,
        'total_present': total_present,
        'total_absent': total_absent,
        'attendance_records': student.attendance_set.all().order_by('-date')[:5],
    })


##############################################
# STUDENT INDIVIDUAL ATTENDANCE
##############################################
@login_required
def student_attendance(request):
    student = Student.objects.get(user=request.user)
    attendance_records = Attendance.objects.filter(student=student)
    return render(request, 'student/student_attendance.html',
                  {'student_attendance_data': attendance_records})


##############################################
# STUDENT FEES SECTION
##############################################
@login_required
def student_fee_detail(request):
    student = get_object_or_404(Student, user=request.user)
    fee_details = Fee.objects.filter(student=student)
    return render(request, 'student/student_fee_detail.html', {
        'student': student,
        'fee_details': fee_details,
    })
