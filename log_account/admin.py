from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    LongTable,
    TableStyle,
    Paragraph,
    Spacer,
)
from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):

    # LIST DISPLAY
    list_display = (
        "log_id",
        "user",
        "user_name",
        "user_role",
        "action_type",
        "method",
        "path",
        "status_code",
        "ip_address",
        "timestamp",
    )
    # FILTERS
    list_filter = (
        "user",
        "action_type",
        "method",
        "status_code",
    )

    # SEARCH
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "action_type",
        "path",
        "ip_address",
        "description",
    )

    # ORDERING
    ordering = (
        "-timestamp",
    )

    # READ ONLY FIELDS
    readonly_fields = (
        "log_id",
        "user",
        "user_name",
        "user_role",
        "action_type",
        "alert_message",
        "path",
        "method",
        "status_code",
        "ip_address",
        "description",
        "timestamp",
    )

    # PAGINATION
    list_per_page = 25

    # ADMIN ACTIONS
    actions = (
        # "delete_selected",   # Delete activity logs - commented out

        "download_all_excel",
        "download_all_pdf",
        "download_selected_excel",
        "download_selected_pdf",
    )

    # REMOVE DEFAULT DELETE ACTION
    def get_actions(self, request):

        actions = super().get_actions(request)

        # Remove Django's built-in delete action
        actions.pop("delete_selected", None)

        return actions

    # DISABLE ADD ACTIVITY LOG
    def has_add_permission(self, request):
        return False

    # USER NAME
    @admin.display(
        description="Name"
    )
    def user_name(self, obj):

        if not obj.user:
            return "Unknown"

        full_name = (
            f"{obj.user.first_name} "
            f"{obj.user.last_name}"
        ).strip()

        if full_name:
            return full_name

        return obj.user.username

    # USER ROLE
    @admin.display(
        description="User Type"
    )
    def user_role(self, obj):

        if not obj.user:
            return "Unknown"

        if obj.user.is_superuser:
            return "Admin"

        if (
            hasattr(obj.user, "role")
            and obj.user.role
        ):
            return obj.user.role.capitalize()

        return "User"

    # USER INFORMATION
    def get_user_info(self, log):

        if not log.user:
            return (
                "Anonymous",
                "Unknown",
                "Unknown",
            )

        username = log.user.username

        full_name = (
            f"{log.user.first_name} "
            f"{log.user.last_name}"
        ).strip()

        if not full_name:
            full_name = username

        if log.user.is_superuser:
            role = "Admin"

        elif (
            hasattr(log.user, "role")
            and log.user.role
        ):
            role = log.user.role.capitalize()

        else:
            role = "User"

        return (
            username,
            full_name,
            role,
        )

    # EXPORT DATE/TIME

    def export_datetime(self):

        return timezone.localtime().strftime(
            "%Y%m%d_%H%M%S"
        )

    # CREATE EXCEL

    def create_excel(self, queryset):

        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Activity Logs"
        # HEADERS
        headers = [
            "Log ID",
            "Username",
            "User Name",
            "User Role",
            "Action",
            "Method",
            "Path",
            "Status Code",
            "IP Address",
            "Alert Message",
            "Description",
            "Timestamp",
        ]
        worksheet.append(headers)
        # HEADER STYLE
        for cell in worksheet[1]:

            cell.font = Font(
                bold=True
            )

            cell.alignment = Alignment(
                horizontal="center",
                vertical="center",
                wrap_text=True,
            )

        # LOG DATA
        logs = (
            queryset
            .select_related("user")
            .order_by("-timestamp")
        )

        for log in logs:

            (
                username,
                full_name,
                role,
            ) = self.get_user_info(log)

            worksheet.append([

                log.log_id,
                username,
                full_name,
                role,
                log.get_action_type_display(),
                log.method or "",
                log.path or "",
                log.status_code or "",
                log.ip_address or "",
                log.alert_message or "",
                log.description or "",
                log.nepali_timestamp,
            ])

        # COLUMN WIDTHS

        column_widths = {
            "A": 10,
            "B": 20,
            "C": 25,
            "D": 15,
            "E": 30,
            "F": 12,
            "G": 45,
            "H": 15,
            "I": 20,
            "J": 40,
            "K": 60,
            "L": 25,
        }

        for column, width in column_widths.items():

            worksheet.column_dimensions[
                column
            ].width = width

        # WRAP TEXT

        for row in worksheet.iter_rows():

            for cell in row:

                cell.alignment = Alignment(
                    vertical="top",
                    wrap_text=True,
                )

        # FREEZE HEADER

        worksheet.freeze_panes = "A2"

        # EXCEL FILTER

        worksheet.auto_filter.ref = (
            worksheet.dimensions
        )

        # HEADER HEIGHT

        worksheet.row_dimensions[1].height = 30

        return workbook

    # DOWNLOAD ALL EXCEL

    @admin.action(
        description="Download ALL activity logs as Excel"
    )
    def download_all_excel(
        self,
        request,
        queryset,
    ):

        # Get ALL logs from database.
        # This ignores pagination and current selection.

        all_logs = ActivityLog.objects.all()

        workbook = self.create_excel(
            all_logs
        )

        filename = (
            f"all_activity_logs_"
            f"{self.export_datetime()}.xlsx"
        )

        response = HttpResponse(
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            )
        )

        response["Content-Disposition"] = (
            f'attachment; filename="{filename}"'
        )

        workbook.save(response)

        return response

    # DOWNLOAD SELECTED EXCEL

    @admin.action(
        description="Download SELECTED activity logs as Excel"
    )
    def download_selected_excel(
        self,
        request,
        queryset,
    ):

        workbook = self.create_excel(
            queryset
        )

        filename = (
            f"selected_activity_logs_"
            f"{self.export_datetime()}.xlsx"
        )

        response = HttpResponse(
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            )
        )

        response["Content-Disposition"] = (
            f'attachment; filename="{filename}"'
        )

        workbook.save(response)

        return response

    # CREATE PDF

    def create_pdf(self, queryset):

        response = HttpResponse(
            content_type="application/pdf"
        )

        filename = (
            f"activity_logs_"
            f"{self.export_datetime()}.pdf"
        )

        response["Content-Disposition"] = (
            f'attachment; filename="{filename}"'
        )

        # PDF DOCUMENT

        document = SimpleDocTemplate(

            response,

            pagesize=landscape(A4),

            rightMargin=5 * mm,

            leftMargin=5 * mm,

            topMargin=8 * mm,

            bottomMargin=8 * mm,
        )

        styles = getSampleStyleSheet()

        # TITLE STYLE

        title_style = ParagraphStyle(

            "ActivityLogTitle",

            parent=styles["Title"],

            alignment=TA_CENTER,

            fontSize=16,

            leading=20,

            spaceAfter=5,
        )

        title = Paragraph(
            "Activity Log Report",
            title_style,
        )

        # TOTAL LOGS

        total = queryset.count()

        total_text = Paragraph(
            f"Total Activity Logs: {total}",
            styles["Normal"],
        )

        # CELL STYLE

        cell_style = ParagraphStyle(

            "ActivityLogCell",

            parent=styles["Normal"],

            fontName="Helvetica",

            fontSize=6.5,

            leading=8,

            spaceAfter=0,

            spaceBefore=0,
        )

        # HEADER STYLE

        header_style = ParagraphStyle(

            "ActivityLogHeader",

            parent=cell_style,

            fontName="Helvetica-Bold",

            fontSize=6.5,

            leading=8,

            textColor=colors.white,

            alignment=TA_CENTER,
        )

        # TABLE HEADER

        data = [

            [
                Paragraph(
                    "ID",
                    header_style
                ),

                Paragraph(
                    "Username",
                    header_style
                ),

                Paragraph(
                    "Name",
                    header_style
                ),

                Paragraph(
                    "Role",
                    header_style
                ),

                Paragraph(
                    "Action",
                    header_style
                ),

                Paragraph(
                    "Method",
                    header_style
                ),

                Paragraph(
                    "Path",
                    header_style
                ),

                Paragraph(
                    "Status",
                    header_style
                ),

                Paragraph(
                    "IP",
                    header_style
                ),

                Paragraph(
                    "Timestamp",
                    header_style
                ),
            ]
        ]

        # LOG DATA

        logs = (
            queryset
            .select_related("user")
            .order_by("-timestamp")
        )

        for log in logs:

            (
                username,
                full_name,
                role,
            ) = self.get_user_info(log)

            data.append([

                Paragraph(
                    str(log.log_id),
                    cell_style,
                ),

                Paragraph(
                    str(username),
                    cell_style,
                ),

                Paragraph(
                    str(full_name),
                    cell_style,
                ),

                Paragraph(
                    str(role),
                    cell_style,
                ),

                Paragraph(
                    str(
                        log.get_action_type_display()
                    ),
                    cell_style,
                ),

                Paragraph(
                    str(
                        log.method or ""
                    ),
                    cell_style,
                ),

                Paragraph(
                    str(
                        log.path or ""
                    ),
                    cell_style,
                ),

                Paragraph(
                    str(
                        log.status_code or ""
                    ),
                    cell_style,
                ),

                Paragraph(
                    str(
                        log.ip_address or ""
                    ),
                    cell_style,
                ),

                Paragraph(
                    str(
                        log.nepali_timestamp
                    ),
                    cell_style,
                ),
            ])

        # PDF TABLE

        table = LongTable(

            data,

            repeatRows=1,

            splitByRow=1,

            colWidths=[

                10 * mm,
                24 * mm,
                28 * mm,
                18 * mm,
                30 * mm,
                15 * mm,
                60 * mm,
                16 * mm,
                25 * mm,
                35 * mm,
            ],
        )

        # TABLE STYLE

        table.setStyle(

            TableStyle([

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.grey,
                ),

                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.grey,
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
            ])
        )

        # BUILD PDF

        document.build([

            title,

            total_text,

            Spacer(
                1,
                4 * mm,
            ),

            table,
        ])

        return response


    # DOWNLOAD ALL PDF
    @admin.action(
        description="Download ALL activity logs as PDF"
    )
    def download_all_pdf(
        self,
        request,
        queryset,
    ):

        # Get ALL logs from database.
        # This ignores pagination and current selection.
        all_logs = ActivityLog.objects.all()

        return self.create_pdf(
            all_logs
        )

    # DOWNLOAD SELECTED PDF
    @admin.action(
        description="Download SELECTED activity logs as PDF"
    )
    def download_selected_pdf(
        self,
        request,
        queryset,
    ):

        return self.create_pdf(
            queryset
        )
        