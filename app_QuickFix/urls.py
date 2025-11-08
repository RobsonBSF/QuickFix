# app_QuickFix/urls.py
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Páginas principais
    path('', views.index_view, name='index'),
    path('homeuser/', views.home_user, name='home_user'),
    path('home/', views.dashboard, name='home'),
    path('base/', views.base_view, name='base'),
    path('baseUser/', views.base_Usuario_view, name='user_base'),

    # Conta / login
    path('cadastro/', views.cadastro, name='cadastro'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.perfil, name='perfil'),  # ← REPOSTO

    # Área do usuário
    path('dashboard/', views.dashboard, name='dashboard'),
    path('friends/', views.amigos, name='amigos'),
    path('favoritos/', views.favoritos, name='favoritos'),
    path('config/', views.configuracoes, name='configuracoes'),

    # Serviços
    path('cadastro-anuncio/', views.cadastro_de_servico, name='cadastro_de_servico'),
    path('servicos/<uuid:id>/', views.servico_detalhe, name='servico_detalhe'),
    path('servicos/<uuid:id>/editar/', views.editar_servico, name='editar_servico'),
    path('meus-servicos/', views.meus_servicos, name='meus_servicos'),

    # Pagamento PIX
    path('pagamento/pix/<uuid:servico_id>/', views.servico_checkout_pix, name='servico_checkout_pix'),
    path('pagamento/pix/confirmar/<uuid:servico_id>/', views.servico_checkout_confirm, name='servico_checkout_confirm'),
    path("pagamento/<uuid:contratado_id>/confirmar/", views.servico_confirmar_recebimento, name="servico_confirmar_recebimento"),
    path("contratos/<uuid:contrato_id>/confirmar/", views.servico_confirmar_pagamento, name="servico_confirmar_pagamento"),
    path('pagamento/<uuid:contrato_id>/confirmar/', views.servico_confirmar_pagamento, name='servico_confirmar_pagamento'),
    # Ações do front -> back
    path('favoritar/', views.favoritar, name='favoritar'),

    # Chat
    path('minhas-conversas/', views.minhas_conversas, name='minhas_conversas'),
    path('chat/<uuid:user_id>/', views.direct_chat, name='direct_chat'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
