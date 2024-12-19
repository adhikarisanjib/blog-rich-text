from django.forms.widgets import ClearableFileInput


class CustomFileInput(ClearableFileInput):
    template_name = "widgets/clearable_file_input.html"
    