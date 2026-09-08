from django.core.checks import messages
from django.shortcuts import render, redirect
from datetime import date
from .models import Attendance
from django.db.models import Count, Q

from attendance.models import Attendance
from students.models import ClassRoom
from datetime import date

from django.contrib import messages
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone


def today_attendance(request):
    today = date.today()

    attendance_records = Attendance.objects.filter(
        date=today, student__classroom__teacher=request.user
    ).select_related("student")
    present = attendance_records.filter(status="PRESENT").count()
    absent = attendance_records.filter(status="ABSENT").count()

    context = {
        "attendance_records": attendance_records,
        "today": today,
        "present": present,
        "absent": absent,
    }
    return render(request, "attendance/today_attendance.html", context)


def mark_attendance(request):
    classroom = ClassRoom.objects.filter(teacher=request.user).first()
    if not classroom:
        messages.error(request, "No classroom assigned to you.")
        # return redirect("accounts:dashboard")
        return redirect("dashboard")
    students = classroom.students.all()
    if request.method == "POST":
        attendance_date = request.POST.get("date")
        for student in students:
            status = request.POST.get(f"student_{student.id}")
            if not status:
                continue
            Attendance.objects.update_or_create(
                student=student, date=attendance_date, defaults={"status": status}
            )
        messages.success(request, "Attendance saved successfully.")
        return redirect("attendance")
    context = {
        "classroom": classroom,
        "students": students,
        "today": date.today(),
    }
    return render(
        request,
        "attendance/attendance_form.html",
        context,
    )


def attendance_history(request):
    from_date = request.GET.get("from")
    to_date = request.GET.get("to")

    queryset = Attendance.objects.filter(student__classroom__teacher=request.user)

    if from_date:
        queryset = queryset.filter(date__gte=from_date)

    if to_date:
        queryset = queryset.filter(date__lte=to_date)

    attendance_records = (
        queryset.values(
            # added mannually
            # "student__name",
            "date", "student__classroom__name", "student__classroom__section"
        )
        .annotate(
            present_count=Count("id", filter=Q(status="PRESENT")),
            absent_count=Count("id", filter=Q(status="ABSENT")),
        )
        .order_by("-date")
    )
    
    # to check the percentage of student present in the specific date
    for record in attendance_records:
        total = record["present_count"] + record["absent_count"]

        if total > 0:
            record["attendance_percentage"] = round(
                (record["present_count"] / total) * 100,
                2,
            )
        else:
            record["attendance_percentage"] = 0

    context = {
        "attendance_records": attendance_records,
        "from_date": from_date,
        "to_date": to_date,
    }

    return render(request, "attendance/attendance_history.html", context)



def admin_mark_attendance(request):

    classrooms = ClassRoom.objects.all().order_by("name", "section")

    selected_classroom = None
    students = []

    # Get selected classroom from GET or POST
    classroom_id = (
        request.GET.get("classroom")
        or request.POST.get("classroom")
    )

    if classroom_id:
        try:
            selected_classroom = ClassRoom.objects.get(id=classroom_id)
            students = selected_classroom.students.all()
        except ClassRoom.DoesNotExist:
            messages.error(request, "Selected classroom does not exist.")

    # Save attendance
    if request.method == "POST":

        attendance_date = request.POST.get("date")

        if not selected_classroom:
            messages.error(request, "Please select a class.")
            return redirect("admin-mark-attendance")

        for student in students:

            status = request.POST.get(f"student_{student.id}")

            if status:
                Attendance.objects.update_or_create(
                    student=student,
                    date=attendance_date,
                    defaults={"status": status}
                )

        messages.success(request, "Attendance saved successfully.")

        return redirect(
            f"/attendance/admin/mark/?classroom={selected_classroom.id}"
        )

    context = {
        "classrooms": classrooms,
        "selected_classroom": selected_classroom,
        "students": students,
        "today": date.today(),
    }

    return render(
        request,
        "attendance/admin_attendance_form.html",
        context,
    )


@login_required
def admin_attendance_history(request):

    from_date = request.GET.get("from")
    to_date = request.GET.get("to")
    classroom_id = request.GET.get("classroom")

    classrooms = (
        ClassRoom.objects
        .all()
        .order_by("name", "section")
    )

    queryset = Attendance.objects.all()

    # Default = last 2 months attendance
    if not from_date and not to_date and not classroom_id:
        two_months_ago = timezone.now().date() - timedelta(days=60)
        queryset = queryset.filter(date__gte=two_months_ago)

    # Filter classroom
    if classroom_id:
        queryset = queryset.filter(
            student__classroom_id=classroom_id
        )

    # Filter from date
    if from_date:
        queryset = queryset.filter(
            date__gte=from_date
        )

    # Filter to date
    if to_date:
        queryset = queryset.filter(
            date__lte=to_date
        )

    attendance_records = (
        queryset.values(
            "date",
            "student__classroom__name",
            "student__classroom__section",
        )
        .annotate(
            present_count=Count(
                "id",
                filter=Q(status="PRESENT")
            ),
            absent_count=Count(
                "id",
                filter=Q(status="ABSENT")
            ),
        )
        .order_by("-date")
    )

    attendance_records = list(attendance_records)

    for record in attendance_records:

        total = (
            record["present_count"]
            + record["absent_count"]
        )

        if total:
            record["attendance_percentage"] = round(
                (record["present_count"] / total) * 100,
                2
            )
        else:
            record["attendance_percentage"] = 0

    # Pagination
    paginator = Paginator(
        attendance_records,
        10
    )

    page_number = request.GET.get("page")

    attendance_records = paginator.get_page(
        page_number
    )

    context = {
        "attendance_records": attendance_records,
        "classrooms": classrooms,
        "selected_classroom": classroom_id,
        "from_date": from_date,
        "to_date": to_date,
    }

    return render(
        request,
        "attendance/admin_attendance_history.html",
        context,
    )


def admin_today_attendance(request):

    today = date.today()

    # Get filters
    classroom_id = request.GET.get("classroom")
    status = request.GET.get("status")

    # Get all classrooms
    classrooms = ClassRoom.objects.all().order_by(
        "name",
        "section"
    )

    # Get today's attendance
    attendance_records = Attendance.objects.filter(
        date=today
    ).select_related(
        "student",
        "student__classroom"
    )

    # Filter by classroom
    if classroom_id:
        attendance_records = attendance_records.filter(
            student__classroom_id=classroom_id
        )

    # Filter by attendance status
    if status in ["PRESENT", "ABSENT"]:
        attendance_records = attendance_records.filter(
            status=status
        )

    # Order records
    attendance_records = attendance_records.order_by(
        "student__classroom__name",
        "student__classroom__section",
        "student__name"
    )

    # Count present
    present = attendance_records.filter(
        status="PRESENT"
    ).count()

    # Count absent
    absent = attendance_records.filter(
        status="ABSENT"
    ).count()

    context = {
        "attendance_records": attendance_records,
        "today": today,
        "present": present,
        "absent": absent,
        "classrooms": classrooms,
        "selected_classroom": classroom_id,
        "selected_status": status,
    }

    return render(
        request,
        "attendance/admin_today_attendance.html",
        context
    )




def admin_today_attendance(request):

    today = date.today()

    # Get filters
    classroom_id = request.GET.get("classroom")
    status = request.GET.get("status")

    # Get all classrooms
    classrooms = ClassRoom.objects.all().order_by(
        "name",
        "section"
    )

    # Get today's attendance
    attendance_records = Attendance.objects.filter(
        date=today
    ).select_related(
        "student",
        "student__classroom"
    )

    # Filter by classroom
    if classroom_id:
        attendance_records = attendance_records.filter(
            student__classroom_id=classroom_id
        )

    # Filter by attendance status
    if status in ["PRESENT", "ABSENT"]:
        attendance_records = attendance_records.filter(
            status=status
        )

    # Order records
    attendance_records = attendance_records.order_by(
        "student__classroom__name",
        "student__classroom__section",
        "student__name"
    )

    # Count present
    present = attendance_records.filter(
        status="PRESENT"
    ).count()

    # Count absent
    absent = attendance_records.filter(
        status="ABSENT"
    ).count()

    context = {
        "attendance_records": attendance_records,
        "today": today,
        "present": present,
        "absent": absent,
        "classrooms": classrooms,
        "selected_classroom": classroom_id,
        "selected_status": status,
    }

    return render(
        request,
        "attendance/admin_today_attendance.html",
        context
    )


