from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from students.models import Student,ClassRoom
from .models import StudentUpgrade
from .forms import StudentUpgradeForm,ClassRoomForm,StudentForm




@login_required
def student_upgrade(request):

    form = StudentUpgradeForm()
    students = []

    class_id = request.GET.get("class_id")

    if class_id:
        students = Student.objects.filter(
            classroom_id=class_id
        )

    if request.method == "POST":

        from_class_id = request.POST.get(
            "from_class"
        )

        to_class_id = request.POST.get(
            "to_class"
        )

        selected_students = request.POST.getlist(
            "students"
        )

        if not selected_students:

            messages.error(
                request,
                "Please select at least one student."
            )

            return redirect(
                f"{request.path}?class_id={from_class_id}"
            )

        try:

            to_class = form.fields[
                "to_class"
            ].queryset.get(
                id=to_class_id
            )

        except Exception:

            messages.error(
                request,
                "Please select a valid class."
            )

            return redirect(
                f"{request.path}?class_id={from_class_id}"
            )

        students_to_promote = Student.objects.filter(
            id__in=selected_students
        )

        count = 0

        for student in students_to_promote:

            StudentUpgrade.objects.get_or_create(
                student=student,
                from_class_id=from_class_id,
                to_class=to_class,
                defaults={
                    "promoted_by": request.user
                }
            )

            student.classroom = to_class
            student.save()

            count += 1

        if count == 1:

            messages.success(
                request,
                "1 student promoted successfully."
            )

        else:

            messages.success(
                request,
                f"{count} students promoted successfully."
            )

        return redirect(
            "admin-students"
        )

    return render(
        request,
        "upgrade/student_upgrade.html",
        {
            "form": form,
            "students": students,
        }
    )
    

def create_classroom(request):

    if request.method == "POST":
        form = ClassRoomForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Class created successfully."
            )

            return redirect("create-classroom")

    else:
        form = ClassRoomForm()

    classes = ClassRoom.objects.select_related(
        "teacher"
    ).all()

    return render(
        request,
        "upgrade/create_classroom.html",
        {
            "form": form,
            "classes": classes,
        }
    )


def add_student(request):

    if request.method == "POST":

        form = StudentForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Student added successfully."
            )

            return redirect("add-student")

    else:
        form = StudentForm()

    student_list = Student.objects.select_related(
        "classroom"
    ).order_by("name")

    paginator = Paginator(student_list, 20)

    page_number = request.GET.get("page")

    students = paginator.get_page(page_number)

    return render(
        request,
        "upgrade/add_student.html",
        {
            "form": form,
            "students": students,
        }
    )
