from django.db import models
# Create your models here.

class Project(models.Model):
    project_title = models.CharField(max_length=300)
    project_description = models.TextField()
    project_date = models.DateTimeField('date published')

    def __str__(self):
        return self.project_title
