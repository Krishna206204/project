from django.urls import path

from . import views

urlpatterns = [
    path("list/", views.student, name="student"),
    path("portal/", views.student_lookup, name="student-lookup"),
    
    path(
        "profile/",
        views.student_profile,
        name="student-profile"
    ),
    path("portal/<int:student_id>/", views.student_dashboard, name="student-dashboard"),
    path("portal/<int:student_id>/marks/", views.student_marks, name="student-marks"),
    path(
        "portal/<int:student_id>/attendance/",
        views.student_attendance,
        name="student-attendance",
    ),
    path(
        "portal/<int:student_id>/report-card/<str:exam_name>/",
        views.student_report_card,
        name="student-report-card",
    ),
    path(
        "portal/<int:student_id>/report-card/",
        views.student_report_card,
        name="student-report-card",
    ),
    
# Added manually
    path("accounts/logout/", views.student_logout, name="student-logout"), 
    path("portal/<int:student_id>/assignment/",views.student_assignment,name="student-assignment"),
    
# notice
    path(
        "student/<int:student_id>/notice/",
        views.student_notice,
        name="student-notice"
    ),
    
    path(
        "leave/",
        views.student_leave_applications,
        name="student-leave-applications"
    ),

    path(
        "leave/apply/",
        views.student_apply_leave,
        name="student-apply-leave"
    ),
    
    
    path(
        "teacher/leave/",
        views.teacher_leave_applications,
        name="teacher-leave-applications"
    ),

    path(
        "teacher/leave/<int:leave_id>/update/",
        views.teacher_update_leave,
        name="teacher-update-leave"
    ),  
    
     path(
        "admin/students/",
        views.admin_students,
        name="admin-students"
    ),
    
    
    path(
        "admin/report-cards/",
        views.admin_report_cards,
        name="admin-report-cards"
    ),
    path(
        "portal/<int:student_id>/report-card/",
        views.student_report_card,
        name="student-report-card"
    ),
    path(
        "admin/report-cards/<int:student_id>/",
        views.admin_student_report_card,
        name="admin-student-report-card"
        ),
    
]
