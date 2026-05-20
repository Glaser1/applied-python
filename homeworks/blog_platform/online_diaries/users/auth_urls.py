from django.contrib.auth.views import LogoutView, LoginView
from django.contrib.auth.views import PasswordResetView, PasswordChangeView
from django.urls import path
from . import views

app_name = "auth"

urlpatterns = [
    path("logout/", LogoutView.as_view(template_name="users/logged_out.html"), name="logout"),
    path("signup/", views.SignUp.as_view(), name="signup"),
    path("edit_profile/", views.EditProfileView.as_view(), name="edit_profile"),
    path("login/", LoginView.as_view(template_name="users/login.html"), name="login"),
    path("reset/", PasswordResetView.as_view(template_name="users/password_reset_form.html"), name="reset"),
    path("change/", PasswordChangeView.as_view(template_name="users/password_change_form.html"), name="change"),
]
