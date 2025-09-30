
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    
    # Paginas principais
    path('', views.index_view, name='index'),
    path('homeuser/', views.home_user, name='home_user'),
    path('home/', views.dashboard, name='home'),
    path('base/', views.base_view, name='base'),
    path('baseUser/', views.base_Usuario_view, name='user_base'),
    
    # Paginas de conta/login
    path('cadastro/', views.cadastro, name='cadastro'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.perfil, name='perfil'),
    
    # Paginas pessoas
    path('dashboard/', views.dashboard, name='dashboard'), #pagina para mostrar todos os servicos (atual home)
    path('friends/', views.amigos, name='amigos'),
    path('favoritos/', views.favoritos, name='favoritos'),
    path('config/', views.configuracoes, name='configuracoes'),

    # Paginas de servicos
    path('cadastro-anuncio/', views.cadastro_de_servico, name='cadastro_de_servico'),
    path('servicos/editar-anuncio/<uuid:id>/', views.editar_servico, name='editar_servico'),
    path('meus_servicos/', views.meus_servicos, name='meus_servicos'),
    path('servicos/<uuid:id>/', views.servico_detalhe, name='servico_detalhe'), #página para mostrar um servico especifico criei ela aqui
    path('servicos/editar/<uuid:id>/', views.editar_servico, name='editar_servico'), #página para editar um servico especifico criei ela aqui

    # Front functions to back
    path('executar/', views.favoritar, name='favoritar'),

    # Chat
    path('minhas/', views.minhas_conversas, name='minhas_conversas'),
    path('chat/<str:user_id>/', views.direct_chat, name='direct_chat'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)   

