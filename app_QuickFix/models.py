#! Biblitecas do Django
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MinValueValidator, MaxValueValidator

#! Biblitecas do Python
import uuid # Para gerar _id únicos

#! Não esquecer para manipular os ForeignKey, tem que mapear tbm no "mysql_sync.py"

# ----------------------------
# Modelo de Usuário Customizado
# ----------------------------
class CustomUserManager(BaseUserManager): # Atenticação de usuário customizada
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("O campo 'username' é obrigatório.")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)  # ← gera hash de forma segura
        user.save()
        return user

class CustomUser(AbstractBaseUser): # Modelo de usuário customizado

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    username = models.CharField(max_length=150, unique=True)
    nome = models.CharField(max_length=150)
    email = models.EmailField(blank=True, null=True)  # apenas se quiser
    
    profile_image = models.ImageField(upload_to='perfil', blank=True, null=True)  # Campo para imagem

    #! Campos sistema
    data_criacao = models.DateTimeField(auto_now_add=True)

    #! Campos obrigatorios Django # Campo padrão do Django
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()
    class Meta:
        db_table = 'Usuarios'  # Nome exato da tabela no MySQL

    def __str__(self):
        return f" ID: {self.id} \n Username: {self.username}"

# ----------------------------
# Modelo de Serviço
# ----------------------------
class Servico(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=1, default='A') #* A = Ativo, I = Inativo/Desativado

    # Relacionamento com o modelo Servico
    user = models.ForeignKey(
        CustomUser, 
        related_name='servicos',
        on_delete=models.CASCADE,  # Deleta os servicos se o usuario for deletado
        db_constraint=True 
    )

    titulo = models.CharField(max_length=255)
    categoria = models.TextField(blank=True, null=True)
    descricao = models.TextField(blank=True, null=True)
    tempo_estimado = models.IntegerField(default=0)
    preco = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    atendimento = models.JSONField(blank=True, null=True)
    requisitos = models.TextField(blank=True, null=True, default="")
    cancelamento = models.BooleanField(default=False)

    imagem_p = models.ImageField(upload_to='servicos', blank=True, null=True)  # Campo para imagem

    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Servicos'  # Nome exato da tabela no MySQL

    def __str__(self):
        return self.titulo
    
class Servico_visualizacao(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relacionamento opcional com o modelo CustomUser (usuário autenticado)
    client = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL,  # Define como NULL se o usuário for deletado
        related_name='visualizado',
        null=True,  # Permite que seja nulo
        blank=True
    )

    # Relacionamento com o modelo Servico
    servico = models.ForeignKey(
        Servico, 
        on_delete=models.CASCADE, # deleta visualizaão se servico for deletado
        related_name='visualicacoes'
    )

    # Campo para armazenar o IP do visitante (para anônimos)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Servico_visualizacao'  # Nome exato da tabela no MySQL

    def __str__(self):
        if self.client:
            return f"Visualização por {self.client.username} no serviço {self.servico.titulo}"
        return f"Visualização anônima (IP: {self.ip_address}) no serviço {self.servico.titulo}"

class Servico_avaliacao(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    client = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL,  # Define como NULL se o usuário for deletado
        related_name='avaliacao_feitas',
        null=True,  # Permite que seja nulo
        blank=True
    )

    # Relacionamento com o modelo Servico
    profissional = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE,  # Deleta as avalicacoes se o profissional for deletado
        related_name='avaliacoes_recebidas'
    )

    # Relacionamento com o modelo Servico
    servico = models.ForeignKey(
        Servico, 
        on_delete=models.SET_NULL,  # Define como NULL se o servico for deletado
        related_name='avaliacoes',
        null=True,  # Permite que seja nulo
        blank=True
    )

    # Campo de avaliação com valores entre 1 e 5
    avaliacao = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Servico_avaliacao'  # Nome exato da tabela no MySQL

    def __str__(self):
        if self.client:
            return f"Avaliação: {self.avaliacao} para {self.servico.titulo} por {self.client.username}"
        return f"Avaliação anônima: {self.avaliacao} para {self.servico.titulo}"
    
class Servico_contratado(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relacionamento com o modelo Usuario
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL,  # Define como NULL se o Usuario for deletado
        related_name='servicos_contratados',
        blank=True,
        null=True,
    )

    #! Modificar: Salvar informacoes do servico, caso ele seja excluido
    # Relacionamento com o modelo Servico
    servico = models.ForeignKey(
        Servico, 
        on_delete=models.SET_NULL,  # Define como NULL se o servico for deletado
        related_name='contratados',
        blank=True,
        null=True,
        default=None
    )

    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Servico_contratados'  # Nome exato da tabela no MySQL

    def __str__(self):
        user_str = self.user.username if self.user else "Usuário desconhecido"
        servico_str = self.servico.titulo if self.servico else "Serviço desconhecido"
        return f"Usuario: {user_str} contratou {servico_str}"
    
class Servico_favoritos(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relacionamento com o modelo Usuario
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE,  # Deleta se o usuario for deletado
        related_name='servicos_favoritos'
    )

    # Relacionamento com o modelo Servico
    servico = models.ForeignKey(
        Servico, 
        on_delete=models.CASCADE,  # Deleta se serviço for deletado
        related_name='favoritos'
    )

    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Servico_favoritos'  # Nome exato da tabela no MySQL

    def __str__(self):
        return f"Usuario: {self.user.username} favoritou {self.servico.titulo}"
    
# Chat models
User = settings.AUTH_USER_MODEL


User = get_user_model()

class DirectThread(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="threads_as_user1")
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="threads_as_user2")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user1", "user2")

    @classmethod
    def get_or_create_thread(cls, user1, user2):
        """Retorna a thread existente entre dois usuários ou cria uma nova"""
        # sempre manter ordem estável para evitar duplicados
        if user1.id > user2.id:
            user1, user2 = user2, user1

        thread, created = cls.objects.get_or_create(user1=user1, user2=user2)
        return thread


class DirectMessage(models.Model):
    thread = models.ForeignKey(DirectThread, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']