from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages

class BibliotecarioRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.is_bibliotecario or self.request.user.is_admin_system)
    
    def handle_no_permission(self):
        messages.error(self.request, "Acesso restrito a bibliotecários e administradores.")
        return redirect('home')

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin_system
    
    def handle_no_permission(self):
        messages.error(self.request, "Acesso restrito a administradores.")
        return redirect('home')
