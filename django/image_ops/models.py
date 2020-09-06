from django.db import models

class Image(models.Model):
    bucket = models.CharField(max_length=20)
    file_name = models.CharField(max_length=100)
