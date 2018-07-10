from django.db import models

from oauth2client.contrib.django_util.models import CredentialsField

class slackUserModel(models.Model):
    user = models.CharField(max_length=100,primary_key=True)

class CredentialsModel(models.Model):
    credential = CredentialsField()

