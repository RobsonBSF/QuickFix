# app_QuickFix/views.py
import re
from decimal import Decimal, InvalidOperation
from django.db.models import Q, Avg
from django.shortcuts import render, get_object_or_404, redirect
from .models import DirectThread, DirectMessage, CustomUser
from uuid import UUID

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .models import (
    Servico, Servico_favoritos, Servico_visualizacao, Servico_contratado,
    DirectThread, DirectMessage, CustomUser, Servico_avaliacao
)
from .filters import ServicoFilter

CustomUser = get_user_model()

Area_usuario = 'area_usuario/'
Area_login = 'login/'

ALLOWED_ORDER = {
    "-data_criacao", "data_criacao",
    "preco", "-preco",
    "titulo", "-titulo",
    "avg_rating", "-avg_rating",
}

def _servico_base_queryset():
    return (
        Servico.objects
        .select_related('user')
        .prefetch_related('avaliacoes')
        .annotate(
            avg_rating=Avg('avaliacoes__avaliacao'),
            num_ratings=Count('avaliacoes')
        )
    )


# ---------------------------
# Perfil
# ---------------------------
@login_required
def perfil(request):
    user = request.user

    if request.method == 'POST':
        user.nome = request.POST.get('nome') or ""
        novo_email = request.POST.get('email')
        if novo_email is not None:
            user.email = novo_email

        imagem_p = request.FILES.get('input_image')
        if imagem_p:
            user.profile_image = imagem_p

        user.save()
        messages.success(request, 'Perfil atualizado com sucesso!')
        return redirect('perfil')

    # usa o template correto:
    return render(request, 'area_usuario/perfil.html', {
        'pagina': {'intro': False}
    })

# ---------------------------
# PIX helpers
# ---------------------------
def _emv(field_id: str, value: str) -> str:
    return f"{field_id}{len(value):02d}{value}"

def _crc16(payload: str) -> str:
    polynomial = 0x1021
    crc = 0xFFFF
    for ch in payload.encode("utf-8"):
        crc ^= (ch << 8)
        for _ in range(8):
            if (crc & 0x8000) != 0:
                crc = (crc << 1) ^ polynomial
            else:
                crc <<= 1
            crc &= 0xFFFF
    return f"{crc:04X}"

def _sanitize(s, maxlen):
    import re as _re
    s = _re.sub(r"[^A-Za-z0-9 @\.\-]", "", (s or "")).upper()
    return s[:maxlen]

def build_pix_br_code(chave: str, nome: str, cidade: str, valor: Decimal, txid: str) -> str:
    nome = _sanitize(nome, 25)
    cidade = _sanitize(cidade, 15)
    txid = _sanitize(txid, 25)

    mai = _emv("26", _emv("00", "br.gov.bcb.pix") + _emv("01", chave))
    payload = (
        _emv("00", "01")
        + _emv("01", "12")
        + mai
        + _emv("52", "0000")
        + _emv("53", "986")
        + _emv("54", f"{Decimal(valor):.2f}")
        + _emv("58", "BR")
        + _emv("59", nome)
        + _emv("60", cidade)
        + _emv("62", _emv("05", txid))
    )
    to_crc = payload + "6304"
    return payload + "63" + "04" + _crc16(to_crc)

# ---------------------------
# Checkout PIX
# ---------------------------
@login_required
def servico_checkout_pix(request, servico_id):
    servico = get_object_or_404(Servico, id=servico_id)

    if servico.user_id == request.user.id:
        messages.error(request, "Você não pode contratar o seu próprio serviço.")
        return redirect('servico_detalhe', id=servico.id)

    txid = f"QF{str(servico.id)[:10]}"
    brcode = build_pix_br_code(
        chave=getattr(settings, "PIX_KEY", ""),
        nome=getattr(settings, "PIX_MERCHANT_NAME", "QUICKFIX"),
        cidade=getattr(settings, "PIX_MERCHANT_CITY", "CAMPINAS"),
        valor=servico.preco or Decimal("0.00"),
        txid=txid,
    )
    ctx = {
        "servico": servico,
        "pix_brcode": brcode,
        "pix_copia_cola": brcode,
        "txid": txid,
        "voltar_url": reverse("servico_detalhe", kwargs={"id": servico.id}),
        "confirm_url": reverse("servico_checkout_confirm", kwargs={"servico_id": servico.id}),
    }
    return render(request, "area_usuario/checkout_pix.html", ctx)

@login_required
@require_http_methods(["POST"])
def servico_checkout_confirm(request, servico_id):
    servico = get_object_or_404(Servico, id=servico_id)

    if servico.user_id == request.user.id:
        messages.error(request, "Você não pode contratar o seu próprio serviço.")
        return redirect('servico_detalhe', id=servico.id)

    txid = request.POST.get("txid") or f"QF{str(servico.id)[:10]}"

    Servico_contratado.objects.create(
        user=request.user,
        servico=servico,
        valor=servico.preco,
        txid=txid,
        status="CONFIRMADO",
    )

    try:
        if request.user.email:
            send_mail(
                f"Confirmação de compra - {servico.titulo}",
                f"Olá, {request.user.username}!\nPagamento via PIX confirmado.\nValor: R$ {servico.preco:.2f}",
                None, [request.user.email], fail_silently=True,
            )
        if servico.user and servico.user.email:
            send_mail(
                f"Seu serviço foi contratado - {servico.titulo}",
                f"{request.user.username} contratou seu serviço.",
                None, [servico.user.email], fail_silently=True,
            )
    except Exception:
        pass

    messages.success(request, "Pagamento confirmado! Enviamos um e-mail para você.")
    return redirect("servico_detalhe", id=servico.id)




# -------------------------------------------------
# Filtros e buscas
# -------------------------------------------------
def build_servico_queryset(request, base_qs=None):
    qs = base_qs or Servico.objects.all()

    q = request.GET.get("q")
    if q:
        qs = qs.filter(
            Q(titulo__icontains=q) |
            Q(descricao__icontains=q) |
            Q(categoria__icontains=q)
        )

    status = request.GET.get("status")
    if status in {"A", "I"}:
        qs = qs.filter(status=status)

    categoria = request.GET.get("categoria")
    if categoria:
        qs = qs.filter(categoria__icontains=categoria)

    if request.GET.get("presencial") == "1":
        qs = qs.filter(atendimento__presencial=True)
    if request.GET.get("remoto") == "1":
        qs = qs.filter(atendimento__remoto=True)

    if request.GET.get("cancelamento") == "1":
        qs = qs.filter(cancelamento=True)

    preco_min = request.GET.get("preco_min")
    preco_max = request.GET.get("preco_max")
    try:
        if preco_min:
            qs = qs.filter(preco__gte=Decimal(preco_min))
        if preco_max:
            qs = qs.filter(preco__lte=Decimal(preco_max))
    except (InvalidOperation, TypeError):
        pass

    tempo_max = request.GET.get("tempo_max")
    if tempo_max and tempo_max.isdigit():
        qs = qs.filter(tempo_estimado__lte=int(tempo_max))

    qs = qs.annotate(
        avg_rating=Avg('avaliacoes__avaliacao'),
        num_ratings=Count('avaliacoes'),
    )
    nota_min = request.GET.get("nota_min")
    try:
        if nota_min:
            qs = qs.filter(avg_rating__gte=float(nota_min))
    except ValueError:
        pass

    if request.GET.get("so_favoritos") == "1" and request.user.is_authenticated:
        qs = qs.filter(favoritos__user=request.user)

    order = request.GET.get("ord") or "-data_criacao"
    if order in ALLOWED_ORDER:
        qs = qs.order_by(order)

    return qs

# -------------------------------------------------
# Páginas gerais
# -------------------------------------------------
def index_view(request):
    base = _servico_base_queryset().order_by('-data_criacao')
    filtro = ServicoFilter(request.GET, queryset=base)
    qs = filtro.qs

    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    ctx = {
        'servicos': page_obj.object_list,
        'page_obj': page_obj,
        'filter': filtro,
        'q': request.GET.get('q', ''),
        'incluir_favoritos': None,
    }

    if request.user.is_authenticated:
        ctx['incluir_favoritos'] = [
            f.servico for f in Servico_favoritos.objects.filter(user=request.user)
        ]

    return render(request, 'index.html', ctx)

def base_view(request):
    return render(request, 'base.html')

def base_Usuario_view(request):
    return render(request, Area_usuario+'base.html')

# -------------------------------------------------
# Área do usuário
# -------------------------------------------------
@login_required
def dashboard(request):
    user = request.user
    visualizacoes = Servico_visualizacao.objects.filter(servico__user=user).count()
    return render(request, Area_usuario+'dashboard_user.html', {
        'pagina': {'name': 'Painel de Controle', 'code': 'dashboard'},
        'visualizacoes': visualizacoes
    })
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
    query = request.GET.get('q', '')
    favoritos_qs = Servico_favoritos.objects.filter(user=user).order_by('-data_criacao')
    if query:
        favoritos_qs = favoritos_qs.filter(servico__titulo__icontains=query)
    favoritos = [fav.servico for fav in favoritos_qs]
    return render(request, Area_usuario + 'favoritos.html', {
        'pagina': {'name': 'Favoritados', 'code': 'favoritos'},
        'servicos_favoritos': favoritos,
        'incluir_favoritos': [f.servico for f in Servico_favoritos.objects.filter(user=request.user)],
        'q': query
    })

@login_required
def amigos(request):
    return render(request, Area_usuario+'amigos.html', {
        'pagina': {'name': 'Amizades', 'code': 'amigos'}
    })

@login_required
def home_user(request):
    base = (
        Servico.objects
        .select_related('user')
        .prefetch_related('avaliacoes')
        .annotate(
            avg_rating=Avg('avaliacoes__avaliacao'),
            num_ratings=Count('avaliacoes'),
        )
    )
    filtro = ServicoFilter(request.GET, queryset=base)
    qs = filtro.qs
    if "ordenar" not in request.GET:
        qs = qs.order_by("-data_criacao")

    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    ctx = {
        'servicos': page_obj.object_list,
        'page_obj': page_obj,
        'filter': filtro,
        'q': request.GET.get('q', ''),
        'incluir_favoritos': [f.servico for f in Servico_favoritos.objects.filter(user=request.user)],
    }
    return render(request, 'area_usuario/home.html', ctx)

@login_required
def meus_servicos(request):
    user = request.user
    query = request.GET.get('q', '')
    meus_servicos_qs = Servico.objects.filter(user=user).order_by('-data_criacao')
    if query:
        meus_servicos_qs = meus_servicos_qs.filter(titulo__icontains=query)
    return render(request, Area_usuario + 'meus_servicos.html', {
        'pagina': {'name': 'Meus Servicos', 'code': 'meus_servicos'},
        'button_info': {'text': 'Editar servico', 'url': 'editar_servico'},
        'servicos_meus': meus_servicos_qs,
        'incluir_favoritos': [f.servico for f in Servico_favoritos.objects.filter(user=request.user)],
        'q': query
    })

@login_required
def configuracoes(request):
    return render(request, Area_usuario+'settings.html', {
        'pagina': {'name': 'Configurações', 'code': 'configuracoes'}
    })

# -------------------------------------------------
# Páginas de serviço
# -------------------------------------------------
def servico_detalhe(request, id):
    servico = get_object_or_404(Servico, id=id)
    user = request.user if request.user.is_authenticated else None

    criador_id = servico.user.id if servico.user else None
    pode_conversar = bool(user and servico.user and user.id != servico.user.id)

    Servico_visualizacao.objects.create(
        client=user,
        servico=servico,
        ip_address=request.META.get("REMOTE_ADDR")
    )

    return render(request, 'servico_detalhe.html', {
        'servico': servico,
        'criador_id': criador_id,
        'pode_conversar': pode_conversar,
    })

@login_required(login_url='login')
def cadastro_de_servico(request):
    if request.method == 'POST':
        send_servico(request, request.user)
        return redirect('/home')
    return render(request, Area_usuario+'cadastro_de_servico.html', {
        'pagina': {'name': 'Cadastro de servico', 'code': 'cadastro_de_servico'},
    })

@login_required(login_url='login')
def editar_servico(request, id):
    servico = get_object_or_404(Servico, id=id)
    sender_page = {'pagina': {'name': 'Editar servico'}, 'servico': servico}
    if request.method == 'POST':
        send_servico(request, request.user, servico)
        return redirect('/home')
    return render(request, Area_usuario+'cadastro_de_servico.html', sender_page)

def send_servico(request, user, servico=None):
    form = request.POST.dict()

    # imagem
    if 'input_image' in request.FILES:
        form['imagem_p'] = request.FILES['input_image']
    form.pop('input_image', None)
    form.pop('csrfmiddlewaretoken', None)

    # atendimento
    form['atendimento'] = {
        'presencial': request.POST.get('presencial') == 'on',
        'remoto': request.POST.get('remoto') == 'on',
        'endereco': request.POST.get('endereco', ''),
    }
    form.pop('endereco', None)

    form['cancelamento'] = (request.POST.get('cancelamento') == 'on')

    # limpa auxiliares
    form.pop('presencial', None)
    form.pop('remoto', None)

    form['user'] = user

    if servico is not None:
        for chave, valor in form.items():
            setattr(servico, chave, valor)
        servico.save()
    else:
        servico = Servico.objects.create(**form)

    return 'ok'

# -------------------------------------------------
# Auth
# -------------------------------------------------
def cadastro(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('senha')

        if password != request.POST.get('senha_confirmada'):
            return render(request, Area_login+'register.html', {'form_err': 'As senhas não coincidem.'})

        if CustomUser.objects.filter(username=username).exists():
            return render(request, Area_login+'register.html', {'form_err': 'Usuário já existe.'})

        user = CustomUser.objects.create_user(username=username, password=password)
        user.save()
        return redirect('login')

    return render(request, Area_login+'register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('senha')

        if not username or not password:
            return render(request, Area_login+'login.html', {'form_err': 'Usuário e senha são obrigatórios.'})

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if request.POST.get('remember_me') is not None:
                request.session.set_expiry(60 * 60 * 24 * 30)
            else:
                request.session.set_expiry(60 * 60 * 24 * 1)
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
            _ = CustomUser.objects.get(email=email)
            mensagem = 'Se o email estiver correto, enviaremos instruções para redefinir a senha.'
            return render(request, Area_login+'forgot_password.html', {'mensagem': mensagem})
        except CustomUser.DoesNotExist:
            erro = 'Email não encontrado no sistema.'
            return render(request, Area_login+'forgot_password.html', {'erro': erro})
    return render(request, Area_login+'forgot_password.html')

# -------------------------------------------------
# Chat
# -------------------------------------------------
@login_required
def direct_chat(request, user_id):
    other = get_object_or_404(CustomUser, id=user_id)

    # normaliza para evitar duplicata (A,B == B,A)
    thread = DirectThread.objects.filter(
        Q(user1=request.user, user2=other) | Q(user1=other, user2=request.user)
    ).first()
    if not thread:
        thread = DirectThread.get_or_create_thread(request.user, other)

    if request.method == "POST":
        content = request.POST.get("message")
        if content:
            DirectMessage.objects.create(thread=thread, sender=request.user, content=content)
        return redirect("direct_chat", user_id=other.id)

    msgs = thread.messages.order_by("created_at")

    if request.GET.get("ajax"):
        return render(request, "chat/_messages.html", {"messages": msgs})

    return render(request, "chat/direct_chat.html", {"other": other, "messages": msgs})

@login_required
def minhas_conversas(request):
    user = request.user
    # Quem iniciou a conversa (user1 = usuário logado)
    iniciadas = DirectThread.objects.filter(user1=user)
    # Quem recebeu a conversa (user2 = usuário logado)
    recebidas = DirectThread.objects.filter(user2=user)

    lista_recebidas = [{
        "thread": t,
        "other": t.user1,  # remetente
        "last_message": t.messages.last()
    } for t in recebidas]

    lista_iniciadas = [{
        "thread": t,
        "other": t.user2,  # destinatário
        "last_message": t.messages.last()
    } for t in iniciadas]

    return render(request, "chat/minhas_conversas.html", {
        "recebidas": lista_recebidas,
        "iniciadas": lista_iniciadas,
        "pagina": {"code": "minhas_conversas", "name": "Minhas Conversas"},
    })

@login_required
def favoritar(request):
    if request.method == "POST" and "favoritar" in request.POST:
        user = request.user
        raw = request.POST.get('favoritar', '')
        parts = raw.split(',')
        if len(parts) != 2:
            return redirect(request.META.get('HTTP_REFERER', '/'))

        servico_id, marcar_str = parts
        marcar = (marcar_str == 'True')

        servico = get_object_or_404(Servico, id=servico_id)

        if marcar:
            # evita erro por constraint única
            _, _created = Servico_favoritos.objects.get_or_create(user=user, servico=servico)
        else:
            Servico_favoritos.objects.filter(user=user, servico=servico).delete()

        return redirect(request.META.get('HTTP_REFERER', '/'))

    return render(request, '404.html', status=404)
