from django.urls import path
from . import views
urlpatterns = [
    path('api', views.GetAllUserList.as_view()),
]