from django.urls import path
from . import views

urlpatterns = [
    path(
        "student-upgrade/",
        views.student_upgrade,
        name="student-upgrade"
    ),
    path(
        "classroom/create/",
        views.create_classroom,
        name="create-classroom"
    ),
    path(
        "add-student/",
        views.add_student,
        name="add-student"
    ),
]