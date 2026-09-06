
from django.urls import path
from . import views
urlpatterns = [
    path("assignments/list/", views.assignment_list, name="assignment-list"),
    path("assignments/add/", views.add_assignment, name="add-assignment"),
    path("marks/add/", views.add_marks, name="add-marks"),
    path("marks/view/", views.view_marks, name="view-marks"),
    
     path(
        "marks/edit/<int:mark_id>/",
        views.edit_marks,
        name="marks-edit"
    ),

     path(
        "marks/delete/<int:mark_id>/",
        views.marks_delete,
        name="marks-delete",
    ),
    
    path("results/", views.student_results, name="student-results"),
    path('assignment/delete/<int:id>/',views.delete_assignment,name="delete_assignment"),
    
    path(
        "das/assignments/edit/<int:id>/",
        views.edit_assignment,
        name="assignment-edit"
    ),
    path("report-card/<int:student_id>/<str:exam_name>/", views.report_card, name="report-card"),
    
    path("notices/", views.notice_list, name="notice-list"),
    
    path("das/notices/", views.notice, name="notice-dash"),
    
    
    path(
        "admin/notices/",
        views.admin_notice_list,
        name="admin-notice-list"
    ),
     
    path(
        "admin/notices/add/",
        views.admin_add_notice,
        name="admin-add-notice"
    ),
]