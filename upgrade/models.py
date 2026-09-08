from django.db import models
from students.models import Student,ClassRoom
from accounts.models import User
# Create your models here.
class StudentUpgrade(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='upgrades'
    )

    from_class = models.ForeignKey(
        ClassRoom,
        on_delete=models.CASCADE,
        related_name='promoted_from'
    )

    to_class = models.ForeignKey(
        ClassRoom,
        on_delete=models.CASCADE,
        related_name='promoted_to'
    )

    promoted_date = models.DateField(auto_now_add=True)

    promoted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )