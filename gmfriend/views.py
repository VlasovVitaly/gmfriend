from django.contrib.auth.views import LoginView, logout_then_login


class Login(LoginView):
    template_name = 'login.html'


logout = logout_then_login