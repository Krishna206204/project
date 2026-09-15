
# Create your models here.
from django.db import models
from accounts.models import User


class ClassRoom(models.Model):
    name = models.CharField(max_length=50)
    section = models.CharField(max_length=10)
    teacher = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True,null=True, limit_choices_to={"role": "TEACHER"}
    )
    
    def __str__(self):
        return f"{self.name}-{self.section}"

class Student(models.Model):
    name = models.CharField(max_length=50)
    classroom = models.ForeignKey(
        ClassRoom, on_delete=models.CASCADE, related_name="students"
    )
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=10, blank=True)
    date_of_birth = models.DateField(default="2000-01-01")

    def __str__(self):
        return self.name


class LeaveApplication(models.Model):

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="leave_applications"
    )

    leave_from = models.DateField()

    leave_to = models.DateField()

    reason = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    teacher_remarks = models.TextField(
        blank=True,
        null=True
    )

    applied_at = models.DateTimeField(
        auto_now_add=True
    )

    reviewed_at = models.DateTimeField(
        blank=True,
        null=True
    )

    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="reviewed_leave_applications"
    )

    class Meta:
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.student.name} - {self.leave_from} to {self.leave_to}"