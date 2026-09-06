
from django.contrib import admin
from .models import Subject, Assignment, Marks,Notice
from django import forms

# admin.site.register(Subject)
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display=(
        "name",
        "classroom",
    )
    
    
# admin.site.register(Assignment)
@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display=(
        'title',
        'description',
        'subject',
        'classroom',
        'created_at',
    )

class MarksAdminForm(forms.ModelForm):

    class Meta:
        model = Marks
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Show Student with Class
        self.fields["student"].label_from_instance = (
            lambda student:
            f"{student.name} — {student.classroom}"
        )

        # Show Subject with Class
        self.fields["subject"].label_from_instance = (
            lambda subject:
            f"{subject.name} — {subject.classroom}"
        )


@admin.register(Marks)
class MarksAdmin(admin.ModelAdmin):

    form = MarksAdminForm

    list_display = (
        "student",
        "student_class",
        "subject",
        "subject_class",
        "exam_name",
        "marks_obtained",
        "full_marks",
    )

    list_filter = (
        "subject__classroom",
        "subject",
        "exam_name",
    )

    search_fields = (
        "student__name",
        "subject__name",
        "exam_name",
    )

    @admin.display(description="Student Class")
    def student_class(self, obj):
        return obj.student.classroom

    @admin.display(description="Subject Class")
    def subject_class(self, obj):
        return obj.subject.classroom


# admin.site.register(Notice)
@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display=(
        'title',
        'description',
        'created_at',
        
    )