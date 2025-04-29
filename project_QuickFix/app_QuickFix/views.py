from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required

# Pegamos o modelo de usuário correto (CustomUser)
CustomUser = get_user_model()

@login_required(login_url='login')
def home_view(request):
    return render(request, 'base.html')

def cadastro(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        senha = request.POST.get('senha')
        confirmar_senha = request.POST.get('confirmar_senha')
        cidade = request.POST.get('cidade')
        estado = request.POST.get('estado')

        username = email  # Aqui a gente define username como email

        if senha != confirmar_senha:
            return render(request, 'register.html', {'erro': 'As senhas não coincidem.'})

        if CustomUser.objects.filter(username=username).exists():
            return render(request, 'register.html', {'erro': 'Usuário já existe.'})

        user = CustomUser.objects.create_user(username=username, email=email, password=senha)
        user.cidade = cidade
        user.estado = estado
        user.save()

        return redirect('login')

    return render(request, 'register.html')

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        try:
            user = CustomUser.objects.get(email=email)
            # Aqui você poderia enviar email real no futuro (não vamos enviar agora)
            mensagem = 'Se o email estiver correto, enviaremos instruções para redefinir a senha.'
            return render(request, 'forgot_password.html', {'mensagem': mensagem})
        except CustomUser.DoesNotExist:
            erro = 'Email não encontrado no sistema.'
            return render(request, 'forgot_password.html', {'erro': erro})

    return render(request, 'forgot_password.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        senha = request.POST.get('senha')

        try:
            user_obj = CustomUser.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=senha)
        except CustomUser.DoesNotExist:
            user = None

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'login.html', {'erro': 'Usuário ou senha inválidos.'})

    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')
