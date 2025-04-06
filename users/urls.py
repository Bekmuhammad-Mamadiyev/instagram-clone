from django.urls import path
from .views import UserCreateView, VerifyAPIView

urlpatterns = [
    path("signup/",UserCreateView.as_view()),
    path('verify/',VerifyAPIView.as_view())
]