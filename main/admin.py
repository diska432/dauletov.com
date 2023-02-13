from django.contrib import admin
from django.db import models
from .models import Project
from tinymce.widgets import TinyMCE

class ProjectAdmin(admin.ModelAdmin):
    fields = ["project_title",
              "project_date",
              "project_description"]

    formfield_overrides = {
        models.TextField: {'widget': TinyMCE()},

    }

admin.site.register(Project, ProjectAdmin)
# Register your models here.
