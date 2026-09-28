from functools import wraps

from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from academics.models import Assignment, Marks, Subject,Notice
from attendance.models import Attendance
from students.models import ClassRoom, Student, LeaveApplication
from accounts.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone


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


from django.contrib import messages
from django.shortcuts import render, redirect

def student_lookup(request):
    if request.method == "POST":

        student_id = request.POST.get("student_id")
        date_of_birth = request.POST.get("date_of_birth")

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

            messages.error(
                request,
                "Invalid Student ID or Date of Birth."
            )

            return redirect("student-lookup")

    return render(
        request,
        "students/student_lookup.html"
    )


@student_login_required
def student_profile(request):
    student_id = request.session.get("student_id")

    # Student is not logged in
    if not student_id:
        messages.error(request, "Please login to access your profile.")
        return redirect("student-login")

    try:
        student = Student.objects.select_related("classroom").get(
            id=student_id
        )
    except Student.DoesNotExist:
        request.session.pop("student_id", None)

        messages.error(request, "Student profile not found.")
        return redirect("student-login")

    context = {
        "student": student,
    }

    return render(
        request,
        "students/student_profile.html",
        context
    )



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

    # Available exams
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

    # Select latest exam by default
    if not selected_exam and available_exams:
        selected_exam = available_exams[0]

    # Get marks for the selected student
    marks = Marks.objects.filter(
        student=student
    ).select_related("subject")

    # Filter by selected exam
    if selected_exam:
        marks = marks.filter(
            exam_name=selected_exam
        )

    # Search by subject
    if search_query:
        marks = marks.filter(
            subject__name__icontains=search_query
        )

    mark_rows = []

    for mark in marks:

        # Calculate percentage
        if mark.full_marks and mark.full_marks > 0:
            percentage = (
                mark.marks_obtained / mark.full_marks
            ) * 100
        else:
            percentage = 0

        # Calculate grade
        if percentage >= 90:
            grade = "A+"
        elif percentage >= 80:
            grade = "A"
        elif percentage >= 70:
            grade = "B+"
        elif percentage >= 60:
            grade = "B"
        elif percentage >= 50:
            grade = "C+"
        elif percentage >= 40:
            grade = "C"
        else:
            grade = "NG"

        mark_rows.append({
            "subject": mark.subject.name,
            "exam_name": mark.exam_name,
            "marks_obtained": mark.marks_obtained,
            "full_marks": mark.full_marks,
            "percentage": round(percentage, 2),
            "grade": grade,
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

        # Subject Grade
        if percentage < 40:
            subject_grade = "NG"
            has_failed_subject = True
        elif percentage >= 90:
            subject_grade = "A+"
        elif percentage >= 80:
            subject_grade = "A"
        elif percentage >= 70:
            subject_grade = "B+"
        elif percentage >= 60:
            subject_grade = "B"
        elif percentage >= 50:
            subject_grade = "C+"
        else:
            subject_grade = "C"

        total_full_marks += full_marks
        total_obtained_marks += obtained_marks

        subject_rows.append({
            "subject": mark.subject.name,
            "full_marks": full_marks,
            "obtained_marks": obtained_marks,
            "percentage": percentage,
            "grade": subject_grade,
        })

    overall_percentage = (
        round(
            (total_obtained_marks / total_full_marks) * 100,
            2
        )
        if total_full_marks > 0
        else 0
    )

    # FINAL RESULT
    if overall_percentage >= 40 and not has_failed_subject:
        result = "PASS"
    else:
        result = "FAIL"

    # OVERALL GRADE
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
    elif overall_percentage >= 50:
        grade = "C+"
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


@student_login_required
def student_leave_applications(request):
    student_id = request.session.get("student_id")

    if not student_id:
        messages.error(request, "Please login as a student first.")
        return redirect("student-login")

    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        messages.error(request, "Student not found.")
        return redirect("student-login")

    leave_applications = LeaveApplication.objects.filter(
        student=student
    )

    context = {
        "student": student,
        "leave_applications": leave_applications,
    }

    return render(
        request,
        "students/leave_applications.html",
        context
    )


from datetime import date, timedelta

@student_login_required
def student_apply_leave(request):

    student_id = request.session.get("student_id")

    if not student_id:
        messages.error(request, "Please login as a student first.")
        return redirect("student-login")

    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        messages.error(request, "Student not found.")
        return redirect("student-login")

    today = date.today()

    # Student can apply only within the next 7 days
    max_date = today + timedelta(days=6)

    if request.method == "POST":

        leave_from = request.POST.get("leave_from")
        leave_to = request.POST.get("leave_to")
        reason = request.POST.get("reason", "").strip()

        # Check required fields
        if not leave_from or not leave_to or not reason:
            messages.error(
                request,
                "Please fill in all required fields."
            )

            return render(
                request,
                "students/apply_leave.html",
                {
                    "student": student,
                    "today": today,
                    "max_date": max_date,
                }
            )

        # Convert strings to date objects
        try:
            leave_from = date.fromisoformat(leave_from)
            leave_to = date.fromisoformat(leave_to)

        except ValueError:
            messages.error(
                request,
                "Invalid leave date."
            )

            return render(
                request,
                "students/apply_leave.html",
                {
                    "student": student,
                    "today": today,
                    "max_date": max_date,
                }
            )

        # 1. Leave cannot start in the past
        if leave_from < today:
            messages.error(
                request,
                "You cannot apply for leave for a past date."
            )

            return render(
                request,
                "students/apply_leave.html",
                {
                    "student": student,
                    "today": today,
                    "max_date": max_date,
                }
            )

        # 2. Leave ending date cannot be before starting date
        if leave_to < leave_from:
            messages.error(
                request,
                "The leave end date cannot be before the start date."
            )

            return render(
                request,
                "students/apply_leave.html",
                {
                    "student": student,
                    "today": today,
                    "max_date": max_date,
                }
            )

        # 3. Leave cannot be requested beyond one week
        if leave_from > max_date or leave_to > max_date:
            messages.error(
                request,
                "Leave can only be requested within the next 7 days."
            )

            return render(
                request,
                "students/apply_leave.html",
                {
                    "student": student,
                    "today": today,
                    "max_date": max_date,
                }
            )

        # 4. Maximum leave duration = 7 days
        leave_duration = (leave_to - leave_from).days + 1

        if leave_duration > 7:
            messages.error(
                request,
                "You can apply for a maximum of 7 days of leave."
            )

            return render(
                request,
                "students/apply_leave.html",
                {
                    "student": student,
                    "today": today,
                    "max_date": max_date,
                }
            )

        # Create leave application
        LeaveApplication.objects.create(
            student=student,
            leave_from=leave_from,
            leave_to=leave_to,
            reason=reason,
        )

        messages.success(
            request,
            "Leave application submitted successfully."
        )

        return redirect("student-leave-applications")

    return render(
        request,
        "students/apply_leave.html",
        {
            "student": student,
            "today": today,
            "max_date": max_date,
        }
    )



    
# added Logout
def student_logout(request):
    request.session.flush()   
    messages.success(
                request,
                "Logout successful."
            )  
    return redirect("home")



@login_required
def teacher_leave_applications(request):
    """
    Display leave applications only from students
    belonging to classrooms assigned to the logged-in teacher.
    """

    # Make sure only teachers can access
    if request.user.role != "TEACHER":
        messages.error(
            request,
            "You are not authorized to access leave applications."
        )
        return redirect("dashboard")

    # Get leave applications of students
    # from classrooms assigned to this teacher
    leave_applications = LeaveApplication.objects.filter(
        student__classroom__teacher=request.user
    ).select_related(
        "student",
        "student__classroom"
    )

    # Counts
    pending_count = leave_applications.filter(
        status="PENDING"
    ).count()

    approved_count = leave_applications.filter(
        status="APPROVED"
    ).count()

    rejected_count = leave_applications.filter(
        status="REJECTED"
    ).count()

    context = {
        "leave_applications": leave_applications,
        "pending_count": pending_count,
        "approved_count": approved_count,
        "rejected_count": rejected_count,
    }

    return render(
        request,
        "students/teacher_leave_applications.html",
        context
    )


@login_required
def teacher_update_leave(request, leave_id):
    """
    Allow a teacher to approve/reject a leave application
    only if the student belongs to the teacher's classroom.
    """

    # Make sure only teachers can access
    if request.user.role != "TEACHER":
        messages.error(
            request,
            "You are not authorized to perform this action."
        )
        return redirect("dashboard")

    # Get leave application
    leave = get_object_or_404(
        LeaveApplication,
        id=leave_id
    )

    # Security check:
    # Teacher can only update leave requests
    # from their own assigned classrooms.
    if leave.student.classroom.teacher != request.user:
        messages.error(
            request,
            "You are not authorized to update this leave application."
        )
        return redirect("teacher-leave-applications")

    if request.method == "POST":

        status = request.POST.get("status")
        teacher_remarks = request.POST.get(
            "teacher_remarks",
            ""
        ).strip()

        # Validate status
        if status not in ["PENDING", "APPROVED", "REJECTED"]:

            messages.error(
                request,
                "Invalid leave status."
            )

            return redirect(
                "teacher-update-leave",
                leave_id=leave.id
            )

        # Update application
        leave.status = status
        leave.teacher_remarks = teacher_remarks
        leave.reviewed_by = request.user
        leave.reviewed_at = timezone.now()

        leave.save()

        if status == "APPROVED":

            messages.success(
                request,
                "Leave application approved successfully."
            )

        elif status == "REJECTED":

            messages.success(
                request,
                "Leave application rejected successfully."
            )

        else:

            messages.success(
                request,
                "Leave application updated successfully."
            )

        return redirect(
            "teacher-leave-applications"
        )

    context = {
        "leave": leave,
    }

    return render(
        request,
        "students/teacher_update_leave.html",
        context
    )
# admin
@login_required
def admin_students(request):

    # Only Admin / Superuser
    if request.user.role != "ADMIN" and not request.user.is_superuser:
        return redirect("home")

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
        return redirect("home")

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

    if request.user.role != "ADMIN" and not request.user.is_superuser:

        return redirect("home")

    student = get_object_or_404(
        Student.objects.select_related("classroom"),
        pk=student_id
    )

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

