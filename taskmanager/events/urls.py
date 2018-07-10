from django.conf.urls import url
from . import views
from events.views import Events                                    #

urlpatterns = [
   
    url(r'^events/', Events.as_view()),
    url(r'^oauth2callback/',views.auth_return,name="callback"),

]

