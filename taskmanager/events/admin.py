from django.contrib import admin
from .models import slackUserModel
from .models import CredentialsModel



admin.site.register(slackUserModel)
admin.site.register(CredentialsModel)

# Register your models here.
