"""
Authentication views for treinamento app.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from ..models import Individuo
from ..forms import SimpleCaptchaLoginForm


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    form_class = SimpleCaptchaLoginForm
    
    def get_success_url(self):
        return reverse_lazy('home')
    
    def form_invalid(self, form):
        messages.error(self.request, 'Usuário, senha ou captcha incorretos.')
        return super().form_invalid(form)
    
    def form_valid(self, form):
        # Verifica o CAPTCHA primeiro
        captcha_verified = form.cleaned_data.get('captcha_verified', False)
        if not captcha_verified:
            messages.error(self.request, 'Por favor, confirme que você não é um robô.')
            return self.form_invalid(form)
        
        # Deixa o Django cuidar da autenticação
        return super().form_valid(form)


def login_view(request):
    return CustomLoginView.as_view()(request)


def register_view(request):
    # Se o usuário já estiver logado e não for admin, redirecionar
    if request.user.is_authenticated and not request.user.is_staff and not request.user.is_superuser:
        messages.warning(request, 'Você já está logado. Faça logout para criar uma nova conta.')
        return redirect('dashboard_view')
    
    if request.method == 'POST':
        # Verificar CAPTCHA primeiro
        captcha_verified = request.POST.get('captcha_verified', 'false')
        if captcha_verified != 'true':
            messages.error(request, 'Por favor, complete o CAPTCHA para continuar.')
            return render(request, 'treinamento/register.html')
        
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        nome_completo = request.POST.get('nome_completo')
        data_nascimento = request.POST.get('data_nascimento')
        idade = request.POST.get('idade')
        peso = request.POST.get('peso')
        sexo = request.POST.get('sexo')
        observacoes = request.POST.get('observacoes')
        
        # Validação básica
        if password1 != password2:
            messages.error(request, 'As senhas não coincidem.')
            return render(request, 'treinamento/register.html')
        
        if len(password1) < 6:
            messages.error(request, 'A senha deve ter pelo menos 6 caracteres.')
            return render(request, 'treinamento/register.html')
        
        if not nome_completo:
            messages.error(request, 'O nome completo é obrigatório.')
            return render(request, 'treinamento/register.html')
        
        if not email:
            messages.error(request, 'O email é obrigatório.')
            return render(request, 'treinamento/register.html')
        
        # Verificar se o email já está em uso
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Este email já está em uso. Por favor, escolha outro.')
            return render(request, 'treinamento/register.html')
        
        try:
            # Validação adicional
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Nome de usuário já existe. Escolha outro.')
                return render(request, 'treinamento/register.html')
            
            # Cria o usuário
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1
            )
            
            # Processa a data de nascimento ou idade
            from datetime import date, timedelta
            
            processed_data_nascimento = None
            
            if data_nascimento:
                # Converte data do formato DD/MM/AAAA para YYYY-MM-DD
                try:
                    if '/' in data_nascimento:
                        partes = data_nascimento.split('/')
                        if len(partes) == 3:
                            dia, mes, ano = partes
                            # Verifica se cada parte é um número válido
                            dia = dia.zfill(2)
                            mes = mes.zfill(2)
                            ano = ano
                            # Validação adicional para garantir que os valores são válidos
                            dia_int = int(dia)
                            mes_int = int(mes)
                            ano_int = int(ano)
                            
                            if not (1 <= dia_int <= 31 and 1 <= mes_int <= 12 and 1900 <= ano_int <= 2025):
                                messages.error(request, 'Data inválida. Verifique os valores (dia, mês, ano).')
                                return render(request, 'treinamento/register.html')
                            
                            processed_data_nascimento = f'{ano}-{mes}-{dia}'
                        else:
                            messages.error(request, 'Formato de data inválido. Use DD/MM/AAAA.')
                            return render(request, 'treinamento/register.html')
                    else:
                        # Se já estiver no formato YYYY-MM-DD
                        processed_data_nascimento = data_nascimento
                except ValueError:
                    messages.error(request, 'Data inválida. Use DD/MM/AAAA com números válidos.')
                    return render(request, 'treinamento/register.html')
                except Exception:
                    messages.error(request, 'Formato de data inválido. Use DD/MM/AAAA.')
                    return render(request, 'treinamento/register.html')
            elif idade:
                # Se a idade for fornecida, calcula a data de nascimento aproximada
                try:
                    idade_int = int(idade)
                    if 1 <= idade_int <= 120:
                        # Calcula data de nascimento aproximada (assumindo aniversário este ano)
                        processed_data_nascimento = date.today().replace(year=date.today().year - idade_int).isoformat()
                    else:
                        messages.error(request, 'Idade deve estar entre 1 e 120.')
                        return render(request, 'treinamento/register.html')
                except ValueError:
                    messages.error(request, 'Idade inválida.')
                    return render(request, 'treinamento/register.html')
            
            # Cria o perfil de Indivíduo
            individuo = Individuo.objects.create(
                user=user,
                nome_completo=nome_completo,
                data_nascimento=processed_data_nascimento,
                peso=peso if peso else None,
                sexo=sexo if sexo else None,
                observacoes=observacoes if observacoes else ''
            )
            
            # Se for admin criando outro usuário, não fazer login automaticamente
            if request.user.is_staff or request.user.is_superuser:
                messages.success(request, 'Usuário criado com sucesso!')
                return redirect('home_view')
            else:
                login(request, user)
                messages.success(request, 'Registro realizado com sucesso!')
                return redirect('home_view')
        
        except Exception as e:
            messages.error(request, f'Erro ao criar usuário: {str(e)}')
            return render(request, 'treinamento/register.html')
    
    return render(request, 'treinamento/register.html')


@require_http_methods(["POST"])
def logout_view(request):
    """View para fazer logout do usuário. Aceita apenas requisições POST."""
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'Você saiu com sucesso!')
        return redirect('login')
    return redirect('home')
