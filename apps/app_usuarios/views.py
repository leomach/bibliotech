from django.shortcuts import render, redirect
from django.views.generic import CreateView, ListView, UpdateView
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import PublicUsuarioCreationForm, ProfileUpdateForm, AdminUsuarioUpdateForm
from .models import Usuario
from .permissions import AdminRequiredMixin

class RegistroView(CreateView):
    form_class = PublicUsuarioCreationForm
    template_name = 'usuarios/registro.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Cadastro realizado com sucesso! Faça login para continuar.")
        return response

@login_required
def perfil_view(request):
    return render(request, 'usuarios/perfil.html', {'usuario': request.user})

@login_required
def perfil_editar(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            if request.htmx:
                return render(request, 'usuarios/partials/perfil_dados.html', {'usuario': request.user})
            messages.success(request, "Perfil atualizado com sucesso!")
            return redirect('perfil')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    return render(request, 'usuarios/partials/perfil_form.html', {'form': form})

# Views Administrativas
class UsuarioListView(AdminRequiredMixin, ListView):
    model = Usuario
    template_name = 'usuarios/lista_usuarios.html'
    context_object_name = 'usuarios_lista'
    paginate_by = 10

class UsuarioUpdateView(AdminRequiredMixin, UpdateView):
    model = Usuario
    form_class = AdminUsuarioUpdateForm
    template_name = 'usuarios/admin_edit_user.html'
    success_url = reverse_lazy('lista_usuarios')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.username = user.email # Mantendo integridade
        user.save()
        messages.success(self.request, f"Usuário {user.nome} atualizado com sucesso!")
        return redirect(self.get_success_url())

def home_view(request):
    return render(request, 'home.html')
