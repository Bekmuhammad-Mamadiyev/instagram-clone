from django.urls import path
from .views import UserCreateView, VerifyAPIView, GetNewVerifyView, ChangeInformationView, ChangeUserPhotoView, \
    LoginView, LogoutView, ForgotPasswordView, ResetPasswordView

urlpatterns = [
    path("login/",LoginView.as_view()),
    path("signup/",UserCreateView.as_view()),
    path('verify/',VerifyAPIView.as_view()),
    path('verify-new/',GetNewVerifyView.as_view()),
    path("change-update/", ChangeInformationView.as_view()),
    path('change-photo/',ChangeUserPhotoView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('forgot-password/', ForgotPasswordView.as_view()),
    path('reset-password/', ResetPasswordView.as_view()),
]