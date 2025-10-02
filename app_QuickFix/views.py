from django.db.models import Q, Avg
from django.shortcuts import render, get_object_or_404, redirect
from .models import DirectThread, DirectMessage, CustomUser
from uuid import UUID

#from django.contrib import auth
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required

#from .forms import PerfilForm #! pra que?
from .models import Servico, Servico_favoritos, Servico_avaliacao, Servico_visualizacao

#* Pegamos o modelo de usuário correto (CustomUser) pelo *Django*.
CustomUser = get_user_model()

Area_usuario = 'area_usuario/'
Area_login = 'login/'

# ----------------------------
# Areas Gerais
# ----------------------------

def index_view(request):

    services = Servico.objects.all().order_by('-data_criacao')

    sender_page = {
        'servicos': services,
        'incluir_favoritos': None
    }

    user = request.user; # print(f'Usuário logado: {user.id}')  # Pega o usuário logado
    favoritos = None

    if user.is_authenticated:
        sender_page['incluir_favoritos'] = [f.servico for f in Servico_favoritos.objects.filter(user=request.user)] or  [{'ative:': True}]
        

    return render(request, 'index.html', sender_page)

def base_view(request):
    return render(request, 'base.html')

def base_Usuario_view(request):
    return render(request, Area_usuario+'base.html')

# ----------------------------
# Area do Usuario
# ----------------------------

@login_required
def dashboard(request):
    user = request.user
    print(f'Usuário logado: {user.id}')  

    # Quantidade de visualizações dos serviços do usuário
    visualizacoes = Servico_visualizacao.objects.filter(servico__user=user).count()

    # Mensagens recebidas pelo usuário
    mensagens = DirectMessage.objects.filter(
        thread__user1=user
    ).exclude(sender=user).count()

    # Nota média das avaliações
    nota_media = Servico_avaliacao.objects.filter(servico__user=user).aggregate(
        avg=Avg("avaliacao")
    )["avg"] or 0

    # Taxa de aceitação (placeholder, futuramente com base em propostas aceitas)
    taxa_aceitacao = 0  

    return render(request, Area_usuario + 'dashboard_user.html', {
        'pagina': {
            'name': 'Painel de Controle',
            'code': 'dashboard'
        },
        'visualizacoes': visualizacoes,
        'mensagens': mensagens,
        'nota_media': round(nota_media, 1),
        'taxa_aceitacao': taxa_aceitacao,
        # placeholders
        'novas_propostas': None,
        'pagamentos_pendentes': None,
    })


@login_required
def favoritos(request):
    user = request.user
    query = request.GET.get('q', '')  # pega o termo de busca

    # Busca os objetos de favoritos do usuário
    favoritos_qs = Servico_favoritos.objects.filter(user=user).order_by('-data_criacao')

    # Aplica filtro se houver pesquisa
    if query:
        favoritos_qs = favoritos_qs.filter(servico__titulo__icontains=query)

    # Extrai os serviços favoritos já filtrados
    favoritos = [fav.servico for fav in favoritos_qs]

    return render(request, Area_usuario + 'favoritos.html', {
        'pagina': {
            'name': 'Favoritados',
            'code': 'favoritos'
        },
        'servicos_favoritos': favoritos,
        'incluir_favoritos': [f.servico for f in Servico_favoritos.objects.filter(user=request.user)],
        'q': query  # envia o valor da busca para o template (opcional)
    })

@login_required
def amigos(request):

    user = request.user; print(f'Usuário logado: {user.id}')  # Pega o usuário logado

    #amigos = (Servico_favoritos.objects.filter(user=user))

    return render(request, Area_usuario+'amigos.html', {
        'pagina': {
            'name': 'Amizades',
            'code': 'amigos'
        },
        #'amigos': amigos
    })

@login_required
def home_user(request):
    query = request.GET.get('q', '')

    if query:
        services = Servico.objects.filter(
            titulo__icontains=query
        ).order_by('-data_criacao')
    else:
        services = Servico.objects.all().order_by('-data_criacao')

    sender_page = {
        'servicos': services,
        'incluir_favoritos': [],
        'q': query
    }

    if request.user.is_authenticated:
        sender_page['incluir_favoritos'] = [
            f.servico for f in Servico_favoritos.objects.filter(user=request.user)
        ]

    return render(request, Area_usuario + 'home.html', sender_page)


@login_required
def meus_servicos(request):
    user = request.user
    query = request.GET.get('q', '')  # Captura o termo de busca

    # Busca apenas os serviços do usuário logado
    meus_servicos_qs = Servico.objects.filter(user=user).order_by('-data_criacao')

    # Aplica filtro se houver busca
    if query:
        meus_servicos_qs = meus_servicos_qs.filter(titulo__icontains=query)

    return render(request, Area_usuario + 'meus_servicos.html', {
        'pagina': {
            'name': 'Meus Servicos',
            'code': 'meus_servicos'
        },
        'button_info': {
            'text': 'Editar servico',
            'url': 'editar_servico'
        },
        'servicos_meus': meus_servicos_qs,
        'incluir_favoritos': [f.servico for f in Servico_favoritos.objects.filter(user=request.user)],
        'q': query  # envia a query para o template
    })


@login_required
def configuracoes(request):
    return render(request, Area_usuario+'settings.html', {
        'pagina': {
            'name': 'Configurações',
            'code': 'configuracoes'
        },
    })

# ----------------------------
# Paginas de servicos
# ----------------------------

def servico_detalhe(request, id):
    try:
        servico = Servico.objects.get(id=id)
        user = request.user if request.user.is_authenticated else None

        # ID do criador do anúncio
        criador_id = servico.user.id if servico.user else None

        # Evita que o criador fale consigo mesmo
        pode_conversar = user and servico.user and user.id != servico.user.id

        # Registra visualização
        Servico_visualizacao.objects.create(
            client=user,
            servico=servico,
        )

    except Servico.DoesNotExist:
        return render(request, '404.html', status=404)

    return render(
        request,
        'servico_detalhe.html',
        {
            'servico': servico,
            'criador_id': criador_id,
            'pode_conversar': pode_conversar,
        }
    )

@login_required(login_url='login')
def cadastro_de_servico(request):

    user = request.user; # print(f'Usuário logado: {user.id}')  # Pega o usuário logado

    if request.method == 'POST': #* Verifica se o método é POST (ou seja, se o formulário foi enviado)

        send_servico(request,user) # Envia os dados do formulario para o banco de dados

        return redirect('/home')

    return render(request, Area_usuario+'cadastro_de_servico.html',{
        'pagina': {
            'name': 'Cadastro de servico',
            'code': 'cadastro_de_servico'
        },
    })

@login_required(login_url='login')
def editar_servico(request, id):
    
    try:
        servico = Servico.objects.get(id=id); print(f'Servico: {servico}') # Pega o servico a ser editado
    except Servico.DoesNotExist: # Erro, caso não consiga puxar o servico
        return render(request, '404.html', status=404)  # ou crie um template customizado

    sender_page = {
        'pagina': {
            'name': 'Editar servico',
        },
        'servico': servico
    }

    if request.method == 'POST': #* Verifica se o método é POST (ou seja, se o formulário foi enviado)
        user = request.user; print(f'Usuário logado: {user.id}')  # Pega o usuário logado
        send_servico(request,user,servico) # Envia os dados do formulario para o banco de dados
        return redirect('/home')

    else:
        return render(request, Area_usuario+'cadastro_de_servico.html', sender_page)
    
def send_servico(request,user,servico=None):

    print(f'Usuário logado: {user.id}')  # Pega o usuário logado
    
    #* Intepreta os dados do formulario
    form = request.POST.dict(); # print('Form: I', form) # Dados do formulário
    imagem_p = request.FILES.get('input_image')  # Obtém o arquivo enviado pelo formulário
        
    #print('Imagem:', imagem_p)
    if imagem_p is not None:
        form['imagem_p'] = imagem_p
    else:
        del form['input_image']
        
    # comprimindo info, permitindo facil alteracao e restruturacao futura
    form['atendimento'] = {
        'presencial': form.get('presencial') or False,
        'remoto': form.get('remoto') or False,
        'endereco': form.get('endereco') or "", # sera necessario fazer um dicionario mais completo de enderenco (Requer front)
    }

    form['cancelamento'] = True if form.get('cancelamento') == 'on' else False

    del form['csrfmiddlewaretoken'] # Remove o token CSRF
    del form['endereco']
        
    if form.get('presencial'): del form['presencial']; 
    if form.get('remoto'): del form['remoto']; 
        
    form['user'] = user; #print('Form: F', form) # Dados do formulário

    if servico is not None:
        print('Editar')
        # Atualiza os campos do serviço existente com os valores do formulário
        for chave, valor in form.items():
            setattr(servico, chave, valor)
        servico.save()  # Salva as alterações no serviço
    else:
        # Cria um novo serviço com os dados do formulário
        servico = Servico.objects.create(**form)
    
    #servico.save() # Salva o objeto Servico no banco de dados
    
    return 'ok'

        
# ----------------------------
# Login, perfil, configuracos e afins
# ----------------------------

def cadastro(request):
    if request.method == 'POST': #* Verifica se o método é POST (ou seja, se o formulário foi enviado)

        #print('Form:', request.POST)

        #* Pega os dados do formulário e manda pro usuario
        username = request.POST.get('username')
        password = request.POST.get('senha')

        #* verfica se a senha foi preenchida corretamente
        if password != (request.POST.get('senha_confirmada')):
            return render(request, Area_login+'register.html', {'form_err': 'As senhas não coincidem.'})

        #* Verifica se o usuário já existe
        if CustomUser.objects.filter( username=username ).exists():
            return render(request, Area_login+'register.html', {'form_err': 'Usuário já existe.'})

        #* Cria o usuário no banco de dados
        user = CustomUser.objects.create_user(
            username=username,
            password=password,
        )
        user.save() # Salva o usuário no banco de dados

        # usuario = authenticate(request, user) #* Faz o login do usuário

        # if usuario is not None:
        #     login(request, usuario)
        #     return redirect('home') # Redireciona para a página de login após o cadastro
        # else:

        return redirect('login')

    return render(request, Area_login+'register.html') # Renderiza o template de cadastro

def login_view(request):
    if request.method == 'POST':
        #print('Form:', request.POST)
        username = request.POST.get('username')
        password = request.POST.get('senha')

        #* Verifica se o usuário e a senha foram preenchidos
        if not username or not password:
            return render(request, Area_login+'login.html', {'form_err': 'Usuário e senha são obrigatórios.'})
        
        #* Autentica o usuário
        user = authenticate(request, username=username, password=password)

        #* Verifica se o usuário existe e se a senha está correta'
        if user is not None:
            login(request, user) #* Faz o login do usuário

            #print('Me Lembre', request.POST.get('remember_me'))
            if( (request.POST.get('remember_me')) is not None): #* define o tempo de expiração da sessão
                request.session.set_expiry(60 * 60 * 24 * 30) # 30 dias
            else:
                request.session.set_expiry(60 * 60 * 24 * 1) # 1 dia

            return redirect('/home')
        else:
            return render(request, Area_login+'login.html', {'form_err': 'Usuário ou senha inválidos'})

    return render(request, Area_login+'login.html')

def logout_view(request):
    logout(request)
    return redirect('/')

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        try:
            user = CustomUser.objects.get(email=email)
            # Aqui você poderia enviar email real no futuro (não vamos enviar agora)
            mensagem = 'Se o email estiver correto, enviaremos instruções para redefinir a senha.'
            return render(request, Area_login+'forgot_password.html', {'mensagem': mensagem})
        except CustomUser.DoesNotExist:
            erro = 'Email não encontrado no sistema.'
            return render(request, Area_login+'forgot_password.html', {'erro': erro})

    return render(request, Area_login+'forgot_password.html')

@login_required
def perfil(request):

    user = request.user; print(user)  # Pega o usuário logado

    if request.method == 'POST': #* Verifica se o método é POST (ou seja, se o formulário foi enviado)

        print('Form:', request.POST)

        user.nome = request.POST.get('nome') or "" # Pega o nome do formulário e manda pro usuario
        user.email = request.POST.get('email') # Pega o email do formulário e manda pro usuario
        
        imagem_p = request.FILES.get('input_image')  # Obtém o arquivo enviado pelo formulário

        print('Imagem:', imagem_p)
        if imagem_p is not None:
            user.profile_image = imagem_p # Salva a imagem no banco de dados

        user.save() # Salva o usuário no banco de dados

        return render(request, Area_login+'perfil.html', {
            'pagina': {
                'intro': False
            },
            'form_info': {
                'msg': 'Perfil atualizado com sucesso!', # Mesagem na tela
                'type': 'success' # class do Bootstrap
            }
        }) # Renderiza o template de perfil


    return render(request, Area_login+'perfil.html',{
        'pagina': {
            'intro': False
        }
    })

@login_required
def favoritar(request):#* Adiciona um item aos favoritos do usuário

    if request.method == "POST" and "favoritar" in request.POST:
        user = request.user; print(f'Usuário logado: {user.id}')  # Pega o usuário logad
        print('Form:', request.POST)

        favoritar = (request.POST.get('favoritar')).split(','); print('Favoritar:', favoritar) # Pega o id do servico a ser favoritado

        if favoritar[1] == 'True': # Favoritar item no banco de dados
            print('Favoritar:', favoritar[0])
            try:
                servico = Servico.objects.get(id=favoritar[0]) # Pega o servico a ser favoritado
                favo = Servico_favoritos.objects.create(user=user, servico=servico) # Cria o objeto Servico_favoritos com os dados do formulário
                print('\n✅ Favoritado:', favo)
            except Exception as e: # Erro, caso não consiga puxar o servico
                print('\n❌ Erro ao favoritar o servico:', favoritar[0])
                print('\n⚠️     Err:', e)
        else:
            print('Desfavoritar:', favoritar[0])
            try:
                favo = Servico_favoritos.objects.get(user=user, servico__id=favoritar[0]) # Pega o servico a ser desfavoritado
                favo.delete() # Deleta o objeto Servico_favoritos do banco de dados
                print('\n✅ Desfavoritado:', favo)
            except Exception as e: # Erro, caso não consiga puxar o servico
                print('\n❌ Erro ao desfavoritar o servico:', favoritar[0])
                print('\n⚠️     Err:', e)

        url_origem = request.META.get('HTTP_REFERER', '/'); # print('URL de origem:', url_origem) # Pega a URL de origem
        return redirect(url_origem)
    
    return render(request, '404.html', status=404) # Retorna erro 404 se não for um POST


# CHAT Views
@login_required
def direct_chat(request, user_id):
    other = get_object_or_404(CustomUser, id=user_id)

    # procura thread já existente entre os dois usuários
    thread = DirectThread.objects.filter(
        Q(user1=request.user, user2=other) | Q(user1=other, user2=request.user)
    ).first()
    if not thread:
        thread = DirectThread.objects.create(user1=request.user, user2=other)

    # se enviou mensagem
    if request.method == "POST":
        content = request.POST.get("message")
        if content:
            DirectMessage.objects.create(thread=thread, sender=request.user, content=content)
        return redirect("direct_chat", user_id=other.id)

    messages = thread.messages.order_by("created_at")

    # ⚡️ se veio com ?ajax=1, devolve só as mensagens (sem layout)
    if request.GET.get("ajax"):
        return render(request, "chat/_messages.html", {"messages": messages})

    return render(request, "chat/direct_chat.html", {
        "other": other,
        "messages": messages
    })

@login_required
def minhas_conversas(request):
    user = request.user

    # Threads onde o user é o "dono do post" (recebidas)
    recebidas = DirectThread.objects.filter(user1=user)

    # Threads onde o user iniciou a conversa em um post de outro usuário
    iniciadas = DirectThread.objects.filter(user2=user)

    lista_recebidas = []
    for t in recebidas:
        other = t.user2  # visitante
        lista_recebidas.append({
            "thread": t,
            "other": other,
            "last_message": t.messages.last()
        })

    lista_iniciadas = []
    for t in iniciadas:
        other = t.user1  # dono do post
        lista_iniciadas.append({
            "thread": t,
            "other": other,
            "last_message": t.messages.last()
        })

    return render(request, "chat/minhas_conversas.html", {
        "recebidas": lista_recebidas,
        "iniciadas": lista_iniciadas,
        "pagina": {"code": "minhas_conversas", "name": "Minhas Conversas"},
    })