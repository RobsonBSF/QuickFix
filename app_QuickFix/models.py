# app_QuickFix/models.py
#! Biblitecas do Django
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

# ----------------------------
# Usuário
# ----------------------------
class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("O campo 'username' é obrigatório.")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if not password:
            raise ValueError("Superusuário requer senha.")
        return self.create_user(username, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, unique=True)
    nome = models.CharField(max_length=150, blank=True, default="")
    email = models.EmailField(blank=True, null=True)

    profile_image = models.ImageField(upload_to='perfil', blank=True, null=True)

    data_criacao = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        db_table = 'Usuarios'

    def __str__(self):
        return self.username

# ----------------------------
# Serviço
# ----------------------------
class Servico(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=1, default='A')  # A/I

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='servicos',
        on_delete=models.CASCADE,
        db_constraint=True
    )

    titulo = models.CharField(max_length=255, db_index=True)
    categoria = models.CharField(max_length=255, blank=True, null=True)
    descricao = models.TextField(blank=True, null=True)
    tempo_estimado = models.IntegerField(default=0)
    preco = models.DecimalField(max_digits=10, decimal_places=2, null=True, db_index=True)
    atendimento = models.JSONField(blank=True, null=True)  # {presencial, remoto, endereco}
    requisitos = models.TextField(blank=True, null=True, default="")
    cancelamento = models.BooleanField(default=False)

    imagem_p = models.ImageField(upload_to='servicos', blank=True, null=True)

    data_criacao = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'Servicos'
        indexes = [
            models.Index(fields=['status', 'data_criacao']),
            models.Index(fields=['titulo']),
            models.Index(fields=['preco']),
        ]

    def __str__(self):
        return self.titulo

# ----------------------------
# Visualizações
# ----------------------------
class Servico_visualizacao(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='visualizado',
        null=True, blank=True
    )
    servico = models.ForeignKey(
        'app_QuickFix.Servico',
        on_delete=models.CASCADE,
        related_name='visualizacoes'          # <- corrigido (antes: 'visualicacoes')
    )

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Servico_visualizacao'
        indexes = [models.Index(fields=['data_criacao'])]

    def __str__(self):
        who = self.client.username if self.client else f"IP {self.ip_address}"
        return f"Visualização por {who} em {self.servico.titulo}"

# ----------------------------
# Avaliações
# ----------------------------
class Servico_avaliacao(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='avaliacao_feitas',
        null=True, blank=True
    )
    profissional = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='avaliacoes_recebidas'
    )
    servico = models.ForeignKey(
        'app_QuickFix.Servico',
        on_delete=models.SET_NULL,
        related_name='avaliacoes',
        null=True, blank=True
    )

    avaliacao = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Servico_avaliacao'
        indexes = [models.Index(fields=['data_criacao'])]

    def __str__(self):
        who = self.client.username if self.client else "Anônimo"
        title = self.servico.titulo if self.servico else "Serviço"
        return f"{who} → {title}: {self.avaliacao}"

# ----------------------------
# Contratação (para o PIX)
# ----------------------------
class Servico_contratado(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='servicos_contratados',
        null=True, blank=True,
    )
    servico = models.ForeignKey(
        'app_QuickFix.Servico',
        on_delete=models.SET_NULL,
        related_name='contratados',
        null=True, blank=True, default=None
    )

    valor = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    txid = models.CharField(max_length=35, db_index=True, blank=True, default="")  # (até 25 no BR Code)

    STATUS_CHOICES = (
        ('PENDENTE', 'Pendente'),
        ('CONFIRMADO', 'Confirmado'),
        ('CANCELADO', 'Cancelado'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CONFIRMADO')

    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Servico_contratados'
        ordering = ['-data_criacao']
        indexes = [models.Index(fields=['status', 'data_criacao'])]

    def __str__(self):
        u = self.user.username if self.user else "Usuário"
        s = self.servico.titulo if self.servico else "Serviço"
        return f"{u} contratou {s} [{self.status}]"

# ----------------------------
# Favoritos
# ----------------------------
class Servico_favoritos(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='servicos_favoritos'
    )
    servico = models.ForeignKey(
        'app_QuickFix.Servico',
        on_delete=models.CASCADE,
        related_name='favoritos'
    )

    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Servico_favoritos'
        constraints = [
            models.UniqueConstraint(fields=['user', 'servico'], name='uniq_fav_user_servico')
        ]
        indexes = [models.Index(fields=['data_criacao'])]

    def __str__(self):
        return f"{self.user.username} ♥ {self.servico.titulo}"

# ----------------------------
# Chat
# ----------------------------
class DirectThread(models.Model):
    user1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="threads_as_user1")
    user2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="threads_as_user2")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user1", "user2")

    @classmethod
    def get_or_create_thread(cls, user1, user2):
        # ordem estável para evitar duplicados; compare UUIDs como string
        if str(user1.id) > str(user2.id):
            user1, user2 = user2, user1
        thread, _ = cls.objects.get_or_create(user1=user1, user2=user2)
        return thread

class DirectMessage(models.Model):
    thread = models.ForeignKey(DirectThread, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']
