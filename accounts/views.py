from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from students.models import ClassRoom,Student
from django.contrib import messages
from academics.models import Subject
from .models import User,ContactMessage


def login_selection(request):
    return render(request, "accounts/login_page.html")

def home(request):
    return render(request,"accounts/home.html")


def contact(request):
    if request.method == "POST":
        ContactMessage.objects.create(
            name=request.POST.get("name"),
            email=request.POST.get("email"),
            phone=request.POST.get("phone"),
            subject=request.POST.get("subject"),
            message=request.POST.get("message"),
        )

        return redirect("contact")
    
    return render(request, "accounts/contact.html")
    
def about(request):
    return render(request,"accounts/about.html")

def teacher_login(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(username=username, password=password)

        if user and user.role == "TEACHER":
            login(request, user)
            messages.success(request, "Login successful")
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid credentials")
            return redirect("login")

    return render(request, "accounts/login.html")





def teacher_logout(request):
    logout(request)
    messages.success(
                request,
                "Logout successful."
            )
    return redirect("home")


@login_required
def dashboard(request):
    classroom = ClassRoom.objects.filter(teacher=request.user).first()

    student_count = 0
    subject_count = 0

    if classroom:
        student_count = classroom.students.count()
        subject_count = Subject.objects.filter(classroom=classroom).count()

    context = {
        "classroom": classroom,
        "student_count": student_count,
        "subject_count": subject_count,
    }
    return render(request, "accounts/dashboard.html", context)



def admin_logout(request):
    logout(request)
    messages.success(
            request,
            "Logout  successful."
            )
    return redirect("home")


@login_required
def admin_login(request):
    # If already logged in
    if request.user.is_authenticated:

        if request.user.role == "ADMIN" or request.user.is_superuser:
            return redirect("admin-dashboard")

        return redirect("dashboard")

    # Handle login form
    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        # Invalid credentials
        if user is None:

            messages.error(
                request,
                "Invalid username or password."
            )

            return redirect("admin-login")

        # Check Admin role
        if user.role != "ADMIN" and not user.is_superuser:

            messages.error(
                request,
                "You do not have Admin access."
            )

            return redirect("admin-login")

        login(request, user)

        messages.success(
            request,
            "Admin login successful."
        )

        return redirect("admin-dashboard")

    return render(
        request,
        "accounts/admin_login.html"
    )
    
    
@login_required
def admin_dashboard(request):

    # Only Admin / Superuser
    if request.user.role != "ADMIN" and not request.user.is_superuser:

        messages.error(
            request,
            "You are not authorized to access the Admin Dashboard."
        )

        return redirect("dashboard")

    # Count complete system data
    total_students = Student.objects.count()

    total_teachers = User.objects.filter(
        role="TEACHER"
    ).count()

    total_classrooms = ClassRoom.objects.count()

    total_subjects = Subject.objects.count()

    context = {
        "total_students": total_students,
        "total_teachers": total_teachers,
        "total_classrooms": total_classrooms,
        "total_subjects": total_subjects,
    }

    return render(
        request,
        "accounts/admin_dashboard.html",
        context
    )
    
    
    
@login_required
def admin_contact_messages(request):
    messages_contact = ContactMessage.objects.all().order_by("-created_at")
    
    return render(
        request,
        "accounts/contact_messages.html",
        {
            "messages_contact": messages_contact,
        },
    )