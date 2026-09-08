
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
