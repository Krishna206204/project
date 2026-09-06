from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .models import Assignment, Marks, Subject,Notice
from students.models import ClassRoom, Student
from django.core.paginator import Paginator
@login_required
def add_assignment(request):
    classroom = ClassRoom.objects.filter(teacher=request.user).first()

    if not classroom:
        messages.error(request, "No Classroom assigned to you")
        return redirect("dashboard")

    subjects = Subject.objects.filter(classroom=classroom)
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        subject_id = request.POST.get("subject")

        subject = Subject.objects.get(id=subject_id)
        Assignment.objects.create(
            title=title, description=description, subject=subject, classroom=classroom
        )
        messages.success(request, "Assignment Created Successfully")
        return redirect("assignment-list")
    context = {"classroom": classroom, "subjects": subjects}
    return render(request, "academics/assignment_form.html", context)



@login_required
def assignment_list(request):
    classroom = ClassRoom.objects.filter(teacher=request.user).first()

    assignments = Assignment.objects.none()
    search_query = request.GET.get("search", "")

    if classroom:
        assignments = (
            Assignment.objects.filter(classroom=classroom)
            .select_related("subject", "classroom")
            .order_by("-created_at")
        )

        if search_query:
            assignments = assignments.filter(
                title__icontains=search_query
            )

    context = {
        "assignments": assignments,
        "search_query": search_query,
    }

    return render(
        request,
        "academics/assignment_list.html",
        context
    )
    
@login_required
def delete_assignment(request,id):
    assignment = get_object_or_404(Assignment, id=id)
    assignment.delete()
    messages.success(request, "Assignment Deleted Successfully")
    return redirect(request.META.get("HTTP_REFERER"))


@login_required
def edit_assignment(request, id):
    # Get the assignment only if it belongs to the logged-in teacher's classroom
    assignment = get_object_or_404(
        Assignment,
        id=id,
        classroom__teacher=request.user
    )

    classroom = assignment.classroom

    # Only subjects belonging to this classroom
    subjects = Subject.objects.filter(classroom=classroom)

    if request.method == "POST":

        title = request.POST.get("title")
        description = request.POST.get("description")
        subject_id = request.POST.get("subject")

        # Make sure the selected subject belongs to the teacher's classroom
        subject = get_object_or_404(
            Subject,
            id=subject_id,
            classroom=classroom
        )

        assignment.title = title
        assignment.description = description
        assignment.subject = subject

        # Classroom is not changed
        assignment.classroom = classroom

        assignment.save()

        messages.success(
            request,
            "Assignment Updated Successfully"
        )

        return redirect("assignment-list")

    context = {
        "assignment": assignment,
        "classroom": classroom,
        "subjects": subjects,
    }

    return render(
        request,
        "academics/assignment_edit.html",
        context
    )

@login_required
def notice_list(request):

    notices = (
        Notice.objects
        .all()
        .order_by("-created_at")
    )

    return render(
        request,
        "academics/notice_list.html",
        {
            "notice_list": notices
        }
    )
    
    
def notice(request):

    notices = (
        Notice.objects
        .all()
        .order_by("-created_at")
    )

    return render(
        request,
        "academics/notice.html",
        {
            "notices": notices
        }
    )
    


def admin_notice_list(request):

    notices = (
        Notice.objects
        .all()
        .order_by("-created_at")
    )

    return render(
        request,
        "academics/admin_notice_list.html",
        {
            "notice_list": notices
        }
    )
    
    
    
def admin_add_notice(request):

    if request.method == "POST":

        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()

        if not title:
            messages.error(request, "Notice title is required.")
            return render(
                request,
                "academics/admin_add_notice.html"
            )

        Notice.objects.create(
            title=title,
            description=description
        )

        messages.success(
            request,
            "Notice published successfully."
        )

        return redirect("admin-notice-list")

    return render(
        request,
        "academics/admin_add_notice.html"
    )


@login_required
def add_marks(request):
    classroom = ClassRoom.objects.filter(teacher=request.user).first()

    if not classroom:
        messages.error(request, "No Classroom assigned to you.")
        return redirect("dashboard")

    students = classroom.students.all()
    subjects = Subject.objects.filter(classroom=classroom)

    if request.method == "POST":

        subject_id = request.POST.get("subject")
        exam_name = request.POST.get("exam_name", "").strip().title()
        full_marks = request.POST.get("full_marks", "").strip()

        # Validate required fields
        if not subject_id or not exam_name or not full_marks:
            messages.error(
                request,
                "Subject, exam name and full marks are required."
            )
            return redirect("add-marks")

        # Validate full marks
        try:
            full_marks = int(full_marks)

            if full_marks <= 0:
                messages.error(
                    request,
                    "Full marks must be greater than 0."
                )
                return redirect("add-marks")

        except ValueError:
            messages.error(
                request,
                "Full marks must be a valid number."
            )
            return redirect("add-marks")

        # Get subject belonging to teacher's classroom
        try:
            subject = Subject.objects.get(
                id=subject_id,
                classroom=classroom
            )
        except Subject.DoesNotExist:
            messages.error(
                request,
                "Invalid subject selected."
            )
            return redirect("add-marks")

        # Save marks for each student
        for student in students:

            marks_obtained = request.POST.get(
                f"student_{student.id}"
            )

            # Skip students where no marks were entered
            if marks_obtained == "":
                continue

            try:
                marks_obtained = int(marks_obtained)

                # Don't allow marks greater than full marks
                if marks_obtained < 0 or marks_obtained > full_marks:
                    messages.error(
                        request,
                        f"Marks for {student.name} must be between "
                        f"0 and {full_marks}."
                    )
                    return redirect("add-marks")

            except ValueError:
                messages.error(
                    request,
                    f"Invalid marks entered for {student.name}."
                )
                return redirect("add-marks")

            # Create or update marks
            Marks.objects.update_or_create(
                student=student,
                subject=subject,
                exam_name=exam_name,
                defaults={
                    "marks_obtained": marks_obtained,
                    "full_marks": full_marks,
                },
            )

        messages.success(
            request,
            "Marks saved successfully."
        )

        return redirect("add-marks")

    context = {
        "classroom": classroom,
        "students": students,
        "subjects": subjects,
    }

    return render(
        request,
        "academics/marks_form.html",
        context
    )
    

@login_required
def view_marks(request):

    classroom = ClassRoom.objects.filter(
        teacher=request.user
    ).first()

    marks = Marks.objects.none()
    subjects = Subject.objects.none()
    exam_names = []

    student_name = request.GET.get(
        "student",
        ""
    ).strip()

    subject_id = request.GET.get(
        "subject",
        ""
    ).strip()

    selected_exam = request.GET.get(
        "exam",
        ""
    ).strip()

    if classroom:

        subjects = Subject.objects.filter(
            classroom=classroom
        )

        marks = (
            Marks.objects
            .filter(
                student__classroom=classroom
            )
            .select_related(
                "student",
                "subject"
            )
            .order_by(
                "student__name"
            )
        )

        if student_name:

            marks = marks.filter(
                student__name__icontains=student_name
            )

        if subject_id:

            marks = marks.filter(
                subject_id=subject_id
            )

        if selected_exam:

            marks = marks.filter(
                exam_name=selected_exam
            )

        exam_names = (
            Marks.objects
            .filter(
                student__classroom=classroom
            )
            .values_list(
                "exam_name",
                flat=True
            )
            .distinct()
        )

    paginator = Paginator(
        marks,
        8
    )

    page_number = request.GET.get(
        "page"
    )

    page_obj = paginator.get_page(
        page_number
    )

    current_page = page_obj.number
    total_pages = paginator.num_pages

    page_range = []

    for num in range(
        1,
        total_pages + 1
    ):

        if (
            num == 1
            or num == total_pages
            or current_page - 2 <= num <= current_page + 2
        ):

            page_range.append(num)

        elif page_range and page_range[-1] != "...":

            page_range.append("...")

    context = {

        "marks": page_obj,

        "page_obj": page_obj,

        "paginator": paginator,

        "page_range": page_range,

        "subjects": subjects,

        "exam_names": exam_names,

        "selected_student": student_name,

        "selected_subject": subject_id,

        "selected_exam": selected_exam,
    }

    return render(
        request,
        "academics/marks_list.html",
        context
    )

@login_required
def edit_marks(request, mark_id):

    # Get the existing marks record
    mark = get_object_or_404(
        Marks,
        id=mark_id
    )

    # Only show subjects from the teacher's classroom
    classroom = ClassRoom.objects.filter(
        teacher=request.user
    ).first()

    if not classroom:
        messages.error(
            request,
            "You are not assigned to any classroom."
        )
        return redirect("view-marks")

    # Security check:
    # Make sure this mark belongs to the teacher's classroom
    if mark.student.classroom_id != classroom.id:
        messages.error(
            request,
            "You are not allowed to edit these marks."
        )
        return redirect("view-marks")

    subjects = Subject.objects.filter(
        classroom=classroom
    )

    if request.method == "POST":

        exam_name = request.POST.get(
            "exam_name",
            ""
        ).strip()

        subject_id = request.POST.get(
            "subject"
        )

        marks_obtained = request.POST.get(
            "marks_obtained"
        )

        full_marks = request.POST.get(
            "full_marks"
        )

        if not exam_name:
            messages.error(
                request,
                "Exam name is required."
            )

        elif not subject_id:
            messages.error(
                request,
                "Please select a subject."
            )

        elif not marks_obtained:
            messages.error(
                request,
                "Marks obtained is required."
            )

        elif not full_marks:
            messages.error(
                request,
                "Full marks is required."
            )

        else:

            try:
                marks_obtained_value = float(
                    marks_obtained
                )

                full_marks_value = float(
                    full_marks
                )

                if full_marks_value <= 0:
                    messages.error(
                        request,
                        "Full marks must be greater than 0."
                    )

                elif marks_obtained_value < 0:
                    messages.error(
                        request,
                        "Marks cannot be negative."
                    )

                elif marks_obtained_value > full_marks_value:
                    messages.error(
                        request,
                        "Marks obtained cannot be greater than full marks."
                    )

                else:

                    subject = get_object_or_404(
                        Subject,
                        id=subject_id,
                        classroom=classroom
                    )

                    # Update existing record
                    mark.subject = subject
                    mark.exam_name = exam_name
                    mark.marks_obtained = marks_obtained_value
                    mark.full_marks = full_marks_value

                    mark.save()

                    messages.success(
                        request,
                        "Student marks updated successfully."
                    )

                    return redirect("view-marks")

            except ValueError:

                messages.error(
                    request,
                    "Please enter valid numbers for marks."
                )

    context = {
        "mark": mark,
        "subjects": subjects,
    }

    return render(
        request,
        "academics/edit_mark.html",
        context
    )
    
    
    
    
# added
def report_card(request, student_id, exam_name):

    student = get_object_or_404(
        Student.objects.select_related("classroom__teacher"),
        pk=student_id,
    )

    marks = (
        Marks.objects.filter(student=student, exam_name=exam_name)
        .select_related("subject", "student__classroom")
        .order_by("subject__name")
    )

    subject_rows = []
    total_full_marks = 0
    total_obtained_marks = 0

    for mark in marks:
        full_marks = mark.full_marks or 0
        obtained_marks = mark.marks_obtained or 0
        percentage = round((obtained_marks / full_marks) * 100, 2) if full_marks else 0

        total_full_marks += full_marks
        total_obtained_marks += obtained_marks

        subject_rows.append(
            {
                "subject": mark.subject.name,
                "full_marks": full_marks,
                "obtained_marks": obtained_marks,
                "percentage": percentage,
            }
        )

    overall_percentage = (
        round((total_obtained_marks / total_full_marks) * 100, 2)
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

    if overall_percentage >= 40:
        result = "PASS"
    else:
        result = "FAIL"

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
        "school_name": "Jhime Malika Secondary School",
        "school_address": "K.i singh 04, Doti",
        "report_title": "Report Card",
        "academic_session": "2026",
        "student": student,
        "exam_name": exam_name,
        "subject_rows": subject_rows,
        "total_full_marks": total_full_marks,
        "total_obtained_marks": total_obtained_marks,
        "overall_percentage": overall_percentage,
        "grade": grade,
        "result": result,
        "remarks": remarks,
        "class_teacher": (
            student.classroom.teacher.get_full_name()
            or student.classroom.teacher.username
            if student.classroom.teacher
            else "Class Teacher"
        ),
        "principal_name": "Nar Bahadur Karki",
    }

    return render(request, "academics/report_card.html", context)


def marks_delete(request, mark_id):
    mark = get_object_or_404(Marks, id=mark_id)

    if request.method == "POST":
        mark.delete()

        messages.success(
            request,
            "Student marks deleted successfully."
        )

        return redirect("view-marks")

    return redirect("view-marks")





def student_results(request):
    classroom = ClassRoom.objects.filter(teacher=request.user).first()
    if not classroom:
        messages.error(request, "No classroom assigned to you.")
        return redirect("dashboard")

    search_query = request.GET.get("search", "").strip()
    selected_exam = request.GET.get("exam", "").strip()

    students = Student.objects.filter(classroom=classroom).select_related("classroom")

    if search_query:
        students = students.filter(name__icontains=search_query)

    available_exams = list(
        Marks.objects.filter(student__classroom=classroom)
        .values_list("exam_name", flat=True)
        .distinct()
        .order_by("exam_name")
    )

    student_results = []
    percentages = []

    for student in students:
        marks_qs = Marks.objects.filter(student=student)

        if selected_exam:
            marks_qs = marks_qs.filter(exam_name=selected_exam)

        marks_qs = marks_qs.select_related("subject")

        total_full_marks = 0
        total_obtained_marks = 0

        for mark in marks_qs:
            total_full_marks += mark.full_marks or 0
            total_obtained_marks += mark.marks_obtained or 0

        if total_full_marks:
            percentage = round((total_obtained_marks / total_full_marks) * 100, 2)
        else:
            percentage = 0

        if percentage >= 90:
            grade = "A+"
        elif percentage >= 80:
            grade = "A"
        elif percentage >= 70:
            grade = "B+"
        elif percentage >= 60:
            grade = "B"
        elif percentage >= 50:
            grade = "C"
        else:
            grade = "F"

        percentages.append(percentage)
        student_results.append(
            {
                "student": student,
                "total_marks": total_full_marks,
                "obtained_marks": total_obtained_marks,
                "percentage": percentage,
                "grade": grade,
                "report_url": (
                    reverse(
                        "report-card",
                        kwargs={
                            "student_id": student.id,
                            "exam_name": selected_exam or "",
                        },
                    )
                    if selected_exam
                    else reverse(
                        "report-card",
                        kwargs={"student_id": student.id, "exam_name": "Mid-Term"},
                    )
                ),
            }
        )

    total_students = len(student_results)
    class_average = round(sum(percentages) / total_students, 2) if total_students else 0
    highest_percentage = max(percentages) if percentages else 0
    lowest_percentage = min(percentages) if percentages else 0

    context = {
        "students_results": student_results,
        "total_students": total_students,
        "class_average": class_average,
        "highest_percentage": highest_percentage,
        "lowest_percentage": lowest_percentage,
        "available_exams": available_exams,
        "selected_exam": selected_exam,
        "search_query": search_query,
    }
    return render(request, "academics/student_results.html", context)




