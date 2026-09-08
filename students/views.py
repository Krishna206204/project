from functools import wraps

from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from academics.models import Assignment, Marks, Subject,Notice
from attendance.models import Attendance
from students.models import ClassRoom, Student
from accounts.models import User
from django.contrib import messages
from django.core.paginator import Paginator


# recommend by chatgpt
def student_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        logged_student_id = request.session.get("student_id")
        requested_student_id = kwargs.get("student_id")

        # Student is not logged in
        if not logged_student_id:
            return redirect("student-lookup")

        # Prevent one student from accessing another student's data
        if requested_student_id is not None:
            if int(logged_student_id) != int(requested_student_id):
                return redirect(
                    "student-dashboard",
                    student_id=logged_student_id
                )

        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
def student(request):
    classroom = ClassRoom.objects.filter(
        teacher=request.user
    ).first()

    # Start with students from this classroom only
    students = Student.objects.none()

    if classroom:
        students = Student.objects.filter(
            classroom=classroom
        )

    # Get search text from URL
    search = request.GET.get("search", "").strip()

    # Filter ONLY by student name
    if search:
        students = students.filter(
            name__icontains=search
        )

    # Get total student count for the class
    if classroom:
        student_count = Student.objects.filter(
            classroom=classroom
        ).count()

        subject_count = Subject.objects.filter(
            classroom=classroom
        ).count()
    else:
        student_count = 0
        subject_count = 0

    context = {
        "classroom": classroom,
        "students": students,
        "student_count": student_count,
        "subject_count": subject_count,
        "search": search,
    }

    return render(request, "students/student_list.html", context)


def student_lookup(request):
    if request.method == "POST":

        student_id = request.POST.get("student_id")
        # phone = request.POST.get("phone")
        date_of_birth=request.POST.get("date_of_birth")

        try:
            student = Student.objects.get(
                id=student_id,
                date_of_birth=date_of_birth,
            )
            request.session["student_id"] = student.id
            messages.success(request, "Login successful")

            return redirect(
                "student-dashboard",
                student_id=student.id
            )

        except Student.DoesNotExist:

            return render(
                request,
                "students/student_lookup.html",
                {
                    "error_message": "Invalid Student ID or Date of birth."
                }
            )

    return render(request, "students/student_lookup.html")




@student_login_required
def student_dashboard(request, student_id):

    student = get_object_or_404(
        Student.objects.select_related("classroom"),
        pk=student_id,
    )

    # Get all marks for this student
    marks_qs = Marks.objects.filter(
        student=student
    ).select_related("subject")

    attendance_qs = Attendance.objects.filter(student=student)

    # GET THE LATEST EXAM
    latest_exam = (
        Marks.objects.filter(student=student)
        .order_by("-id")
        .values_list("exam_name", flat=True)
        .first()
    )

    # CALCULATE PERCENTAGE FOR LATEST EXAM ONLY


    if latest_exam:

        latest_marks_qs = Marks.objects.filter(
            student=student,
            exam_name=latest_exam
        ).select_related("subject")

        total_full_marks = sum(
            mark.full_marks or 0
            for mark in latest_marks_qs
        )

        total_obtained_marks = sum(
            mark.marks_obtained or 0
            for mark in latest_marks_qs
        )

        overall_percentage = (
            round(
                (total_obtained_marks / total_full_marks) * 100,
                2
            )
            if total_full_marks
            else 0
        )

    else:
        overall_percentage = 0


    present_days = attendance_qs.filter(status="PRESENT").count()

    total_days = attendance_qs.count()

    attendance_percentage = (
        round((present_days / total_days) * 100, 2)
        if total_days
        else 0
    )

    subject_count = Subject.objects.filter(
        classroom=student.classroom
    ).count()

    assignment_count = Assignment.objects.filter(
        classroom=student.classroom
    ).count()

    # Latest exam for report card
    report_exam = latest_exam or "Mid-Term"


    context = {
        "student": student,
        "student_id": student.id,
        "classroom": student.classroom,
        "overall_percentage": overall_percentage,
        "attendance_percentage": attendance_percentage,
        "subject_count": subject_count,
        "assignment_count": assignment_count,
        "report_exam": report_exam,
    }

    return render(
        request,
        "students/student_dashboard.html",
        context
    )



@student_login_required
def student_marks(request, student_id):

    student = get_object_or_404(
        Student,
        id=student_id
    )

    # Search query
    search_query = request.GET.get("search", "").strip()

    # Selected exam
    selected_exam = request.GET.get("exam", "").strip()


    available_exams = list(
        Marks.objects.filter(
            student=student
        )
        .values_list(
            "exam_name",
            flat=True
        )
        .distinct()
    )


    available_exams.sort(reverse=True)


    if not selected_exam and available_exams:

        selected_exam = available_exams[0]


    marks = Marks.objects.filter(
        student=student
    )


    if selected_exam:

        marks = marks.filter(
            exam_name=selected_exam
        )



    if search_query:

        marks = marks.filter(
            subject__name__icontains=search_query
        )

    mark_rows = []

    for mark in marks:

        if mark.full_marks:

            percentage = (
                mark.marks_obtained /
                mark.full_marks
            ) * 100

        else:

            percentage = 0


        mark_rows.append({

            "subject": mark.subject.name,

            "exam_name": mark.exam_name,

            "marks_obtained": mark.marks_obtained,

            "full_marks": mark.full_marks,

            "percentage": round(
                percentage,
                2
            ),

        })



    context = {

        "student": student,

        "mark_rows": mark_rows,

        "available_exams": available_exams,

        "selected_exam": selected_exam,

        "search_query": search_query,

    }


    return render(
        request,
        "students/student_marks.html",
        context
    )
    
    

# login requird

@student_login_required
def student_attendance(request, student_id):
    student = get_object_or_404(Student.objects.select_related("classroom"), pk=student_id)
    attendance_records = (
        Attendance.objects.filter(student=student)
        .order_by("-date")
    )

    present_days = attendance_records.filter(status="PRESENT").count()
    absent_days = attendance_records.filter(status="ABSENT").count()
    total_days = attendance_records.count()
    attendance_percentage = (
        round((present_days / total_days) * 100, 2) if total_days else 0
    )

    context = {
        "student": student,
        "attendance_records": attendance_records,
        "present_days": present_days,
        "absent_days": absent_days,
        "total_days": total_days,
        "attendance_percentage": attendance_percentage,
    }
    return render(request, "students/student_attendance.html", context)


# login required
@student_login_required
def student_report_card(request, student_id):

    student = get_object_or_404(
        Student.objects.select_related("classroom"),
        pk=student_id
    )

    available_exams = list(
        Marks.objects.filter(student=student)
        .values_list("exam_name", flat=True)
        .distinct()
        .order_by("exam_name")
    )

    selected_exam = request.GET.get("exam", "").strip()

    if not selected_exam and available_exams:
        selected_exam = available_exams[0]

    marks = (
        Marks.objects.filter(
            student=student,
            exam_name=selected_exam
        )
        .select_related("subject", "student__classroom")
        .order_by("subject__name")
    )

    subject_rows = []
    total_full_marks = 0
    total_obtained_marks = 0

    has_failed_subject = False

    for mark in marks:

        full_marks = mark.full_marks or 0
        obtained_marks = mark.marks_obtained or 0

        percentage = (
            round((obtained_marks / full_marks) * 100, 2)
            if full_marks > 0
            else 0
        )

        if percentage < 40:
            has_failed_subject = True

        total_full_marks += full_marks
        total_obtained_marks += obtained_marks

        subject_rows.append({
            "subject": mark.subject.name,
            "full_marks": full_marks,
            "obtained_marks": obtained_marks,
            "percentage": percentage,
        })

    overall_percentage = (
        round(
            (total_obtained_marks / total_full_marks) * 100,
            2
        )
        if total_full_marks > 0
        else 0
    )

    #  FINAL RESULT
    
    if overall_percentage >= 40 and not has_failed_subject:
        result = "PASS"
    else:
        result = "FAIL"

    # GRADE
    
    if result == "FAIL":
        grade = "NG"

    elif overall_percentage >= 90:
        grade = "A+"

    elif overall_percentage >= 80:
        grade = "A"

    elif overall_percentage >= 70:
        grade = "B+"

    elif overall_percentage >= 60:
        grade = "B"

    else:
        grade = "C"

    # REMARKS
   
    if result == "FAIL":

        if has_failed_subject:
            remarks = "Failed in one or more subjects. Improvement is required."

        else:
            remarks = "Overall percentage is below the passing percentage."

    elif overall_percentage >= 90:
        remarks = "Outstanding Performance"

    elif overall_percentage >= 80:
        remarks = "Excellent Work"

    elif overall_percentage >= 70:
        remarks = "Very Good Performance"

    elif overall_percentage >= 60:
        remarks = "Good Effort"

    elif overall_percentage >= 50:
        remarks = "Satisfactory"

    else:
        remarks = "Passed. Continue working to improve your performance."

    # CONTEXT

    context = {
        "student": student,

        # Exam data
        "available_exams": available_exams,
        "selected_exam": selected_exam,
        "exam_name": selected_exam,

        # Subject marks
        "subject_rows": subject_rows,
        "total_full_marks": total_full_marks,
        "total_obtained_marks": total_obtained_marks,

        # Result information
        "overall_percentage": overall_percentage,
        "grade": grade,
        "result": result,
        "remarks": remarks,
        "has_failed_subject": has_failed_subject,

        # School information
        "school_name": "Jhime Malika Secondary School",
        "school_address": "K.I. Singh-04, Doti",
        "report_title": "Report Card",
        "academic_session": "2026",
    }

    return render(
        request,
        "students/student_report_card.html",
        context
    )




@student_login_required
def student_assignment(request, student_id):
    student = get_object_or_404(Student.objects.select_related("classroom"), pk=student_id)
    assignment_list = (
        Assignment.objects.filter(classroom=student.classroom)
        .order_by("-created_at")
    )
    
    
    context={
        "assignment_list":assignment_list,
        "student":student,
    }
    
    return render(request,"students/student_assignment.html",context)


@student_login_required
def student_notice(request, student_id):

    # Get the logged-in/current student
    student = get_object_or_404(
        Student.objects.select_related("classroom"),
        pk=student_id
    )
    notice_list = Notice.objects.all().order_by("-created_at")

    context = {
        "notice_list": notice_list,
        "student": student,
    }

    return render(
        request,
        "students/student_notice.html",
        context
    )
    
    
# added Logout
def student_logout(request):
    request.session.flush()   
    messages.success(
                request,
                "Logout successful."
            )  
    return redirect("home")



# admin
@login_required
def admin_students(request):

    # Only Admin / Superuser
    if request.user.role != "ADMIN" and not request.user.is_superuser:
        return redirect("dashboard")

    students = (
        Student.objects
        .select_related("classroom")
        .order_by("id")
    )

    # Statistics
    student_count = students.count()
    classroom_count = ClassRoom.objects.count()
    subject_count = Subject.objects.count()
    teacher_count = User.objects.filter(
        role="TEACHER"
    ).count()

    # Pagination (10 students per page)
    paginator = Paginator(students, 11)

    page_number = request.GET.get("page")

    students = paginator.get_page(
        page_number
    )

    context = {
        "students": students,
        "student_count": student_count,
        "classroom_count": classroom_count,
        "subject_count": subject_count,
        "teacher_count": teacher_count,
    }

    return render(
        request,
        "students/admin_student.html",
        context
    )


@login_required
def admin_report_cards(request):

    # Only Admin / Superuser
    if request.user.role != "ADMIN" and not request.user.is_superuser:
        return redirect("dashboard")

    search = request.GET.get("search", "").strip()
    classroom_id = request.GET.get("classroom", "").strip()
    exam_name = request.GET.get("exam_name", "").strip()

    exam_names = list(
        Marks.objects
        .values_list("exam_name", flat=True)
        .distinct()
        .order_by("-id")
    )

    # Remove duplicate exam names while preserving order
    exam_names = list(dict.fromkeys(exam_names))

    if not exam_name and exam_names:
        exam_name = exam_names[0]

    students = Student.objects.select_related(
        "classroom"
    ).all()

    if search:

        if search.isdigit():

            students = students.filter(
                id=int(search)
            )

        else:

            students = students.filter(
                name__icontains=search
            )

    if classroom_id:

        students = students.filter(
            classroom_id=classroom_id
        )

    if exam_name:

        students = students.filter(
            marks__exam_name__iexact=exam_name
        ).distinct()

    students = students.order_by(
        "classroom__name",
        "classroom__section",
        "name"
    )

    classrooms = ClassRoom.objects.all().order_by(
        "name",
        "section"
    )

    paginator = Paginator(
        students,
        25
    )

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(
        page_number
    )

    context = {

        "students": page_obj,

        "page_obj": page_obj,

        "paginator": paginator,

        "classrooms": classrooms,

        "exam_names": exam_names,

        "search": search,

        "selected_classroom": classroom_id,

        "selected_exam": exam_name,
    }

    return render(
        request,
        "students/admin_report_card.html",
        context
    )


@login_required
def admin_student_report_card(request, student_id):

    # Only Admin / Superuser
    if request.user.role != "ADMIN" and not request.user.is_superuser:

        return redirect("dashboard")

    student = get_object_or_404(
        Student.objects.select_related("classroom"),
        pk=student_id
    )

    # Get all exams for this student

    exam_names = (
        Marks.objects
        .filter(student=student)
        .values_list("exam_name", flat=True)
        .distinct()
        .order_by("exam_name")
    )

    selected_exam = request.GET.get(
        "exam_name",
        ""
    ).strip()

    if not selected_exam:

        selected_exam = exam_names.first()

    marks = (
        Marks.objects
        .filter(
            student=student,
            exam_name=selected_exam
        )
        .select_related(
            "subject",
            "student__classroom"
        )
        .order_by("subject__name")
    )

    subject_rows = []

    total_full_marks = 0
    total_obtained_marks = 0

    for mark in marks:

        full_marks = mark.full_marks or 0
        obtained_marks = mark.marks_obtained or 0

        percentage = (
            round(
                (obtained_marks / full_marks) * 100,
                2
            )
            if full_marks
            else 0
        )

        total_full_marks += full_marks
        total_obtained_marks += obtained_marks

        subject_rows.append({
            "subject": mark.subject.name,
            "full_marks": full_marks,
            "obtained_marks": obtained_marks,
            "percentage": percentage,
        })

    # Overall percentage
    overall_percentage = (
        round(
            (total_obtained_marks / total_full_marks) * 100,
            2
        )
        if total_full_marks
        else 0
    )

    if overall_percentage >= 90:
        grade = "A+"

    elif overall_percentage >= 80:
        grade = "A"

    elif overall_percentage >= 70:
        grade = "B+"

    elif overall_percentage >= 60:
        grade = "B"

    elif overall_percentage >= 50:
        grade = "C"

    else:
        grade = "F"

    result = (
        "PASS"
        if overall_percentage >= 40
        else "FAIL"
    )

    if overall_percentage >= 90:
        remarks = "Outstanding Performance"

    elif overall_percentage >= 80:
        remarks = "Excellent Work"

    elif overall_percentage >= 70:
        remarks = "Very Good Performance"

    elif overall_percentage >= 60:
        remarks = "Good Effort"

    elif overall_percentage >= 50:
        remarks = "Satisfactory"

    else:
        remarks = "Needs Improvement"

    context = {

        "student": student,

        "exam_name": selected_exam,

        "exam_names": exam_names,

        "subject_rows": subject_rows,

        "total_full_marks": total_full_marks,

        "total_obtained_marks": total_obtained_marks,

        "overall_percentage": overall_percentage,

        "grade": grade,

        "result": result,

        "remarks": remarks,

        "school_name": "Jhime Malika Secondary School",

        "school_address": "K.i singh 04, doti",

        "report_title": "Report Card",

        "academic_session": "2026",
    }

    return render(
        request,
        "students/admin_student_report_card.html",
        context
    )

