from django import forms
from students.models import ClassRoom,Student


class StudentUpgradeForm(forms.Form):
    from_class = forms.ModelChoiceField(
        queryset=ClassRoom.objects.all(),
        label="From Class"
    )

    to_class = forms.ModelChoiceField(
        queryset=ClassRoom.objects.all(),
        label="To Class"
    )

class ClassRoomForm(forms.ModelForm):
    class Meta:
        model = ClassRoom
        fields = ["name", "section", "teacher"]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "w-full border rounded-lg p-3"
                }
            ),
            "section": forms.TextInput(
                attrs={
                    "class": "w-full border rounded-lg p-3"
                }
            ),
            "teacher": forms.Select(
                attrs={
                    "class": "w-full border rounded-lg p-3"
                }
            ),
        }


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            "name",
            "classroom",
            "address",
            "phone",
            "date_of_birth",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "w-full border rounded-lg p-3"
                }
            ),
            "classroom": forms.Select(
                attrs={
                    "class": "w-full border rounded-lg p-3"
                }
            ),
            "address": forms.Textarea(
                attrs={
                    "class": "w-full border rounded-lg p-3",
                    "rows": 3
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "w-full border rounded-lg p-3"
                }
            ),
            "date_of_birth": forms.DateInput(
                attrs={
                    "class": "w-full border rounded-lg p-3",
                    "type": "date"
                }
            ),
        }