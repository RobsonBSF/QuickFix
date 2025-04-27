from django.shortcuts import render, redirect
from django.contrib import auth
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required

# Pegamos o modelo de usuário correto (CustomUser)
CustomUser = get_user_model()

def home_view(request):
    return render(request, 'base.html')

def cadastro(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']

        if password == password2:
            if CustomUser.objects.filter(username=username).exists():
                return render(request, 'register.html', {'erro': 'Usuário já existe'})
            else:
                user = CustomUser.objects.create_user(username=username, email=email, password=password)
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
            return redirect('/')
        else:
            return render(request, 'login.html', {'erro': 'Usuário ou senha inválidos'})
    else:
        return render(request, 'login.html')

def logout_view(request):
    auth.logout(request)
    return redirect('login')
