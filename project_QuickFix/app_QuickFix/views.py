from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import auth

# Create your views here.

def home_view (request):
    return render(request, 'base.html')

def cadastro(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']

        if password == password2:
            if User.objects.filter(username=username).exists():
                return render(request, 'register.html', {'erro': 'Usuário já existe'})
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()
                return redirect('login')
        else:
            return render(request, 'register.html', {'erro': 'As senhas não coincidem'})
    else:
        return render(request, 'register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(request, username=username, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect('/')  # Redireciona para a página inicial
        else:
            return render(request, 'login.html', {'erro': 'Usuário ou senha inválidos'})

    else:
        return render(request, 'login.html')

def logout_view(request):
    auth.logout(request)
    return redirect('login')
