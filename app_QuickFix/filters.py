# app/filters.py
import django_filters as df
from django import forms
from django.db.models import Q
from .models import Servico

ALLOWED_ORDER = (
    ("-data_criacao", "Mais recentes"),
    ("data_criacao", "Mais antigos"),
    ("-preco", "Preço: maior → menor"),
    ("preco", "Preço: menor → maior"),
    ("-titulo", "Título: Z → A"),
    ("titulo", "Título: A → Z"),
    ("-avg_rating", "Nota: maior → menor"),
    ("avg_rating", "Nota: menor → maior"),
)

class ServicoFilter(df.FilterSet):
    # Busca livre
    q = df.CharFilter(
        method="filter_q",
        label="",
        widget=forms.TextInput(attrs={"placeholder": "O que você precisa?"}),
    )

    # Ordenação (nome usado no template: 'ordenar')
    ordenar = df.ChoiceFilter(
        choices=ALLOWED_ORDER,
        method="filter_ordenar",
        label="",
        empty_label=None,
        widget=forms.Select(),
    )

    # Campos simples
    status = df.ChoiceFilter(
        field_name="status",
        choices=(("A", "Ativo"), ("I", "Inativo")),
        label="Status",
    )
    categoria = df.CharFilter(
        field_name="categoria",
        lookup_expr="icontains",
        label="Categoria",
    )

    # Faixa de preço
    preco_min = df.NumberFilter(field_name="preco", lookup_expr="gte", label="Preço mín.")
    preco_max = df.NumberFilter(field_name="preco", lookup_expr="lte", label="Preço máx.")

    # Tempo máximo (min)
    tempo_max = df.NumberFilter(field_name="tempo_estimado", lookup_expr="lte", label="Tempo máx. (min)")

    # Nota média (usa a annotation avg_rating já existente no queryset base)
    nota_min = df.NumberFilter(method="filter_nota_min", label="Nota mínima")

    # JSONField: atendimento.{presencial, remoto}
    presencial = df.BooleanFilter(method="filter_presencial", label="Presencial")
    remoto = df.BooleanFilter(method="filter_remoto", label="Remoto")

    # Cancelamento (bool normal no modelo)
    cancelamento = df.BooleanFilter(field_name="cancelamento", label="Cancelamento")

    class Meta:
        model = Servico
        fields = []  # vamos controlar tudo por métodos acima

    # ----------------------
    # Métodos de filtro
    # ----------------------
    def filter_q(self, qs, name, value: str):
        if not value:
            return qs
        return qs.filter(
            Q(titulo__icontains=value)
            | Q(descricao__icontains=value)
            | Q(categoria__icontains=value)
        )

    def filter_ordenar(self, qs, name, value: str):
        # Valida contra ALLOWED_ORDER
        allowed = {k for k, _ in ALLOWED_ORDER}
        if value in allowed:
            return qs.order_by(value)
        # fallback
        return qs.order_by("-data_criacao")

    def filter_nota_min(self, qs, name, value):
        # só filtra se vier número
        try:
            v = float(value)
        except (TypeError, ValueError):
            return qs
        return qs.filter(avg_rating__gte=v)

    def filter_presencial(self, qs, name, value: bool):
        # BooleanFilter envia True/False quando marcado/desmarcado
        if value:
            return qs.filter(atendimento__presencial=True)
        return qs

    def filter_remoto(self, qs, name, value: bool):
        if value:
            return qs.filter(atendimento__remoto=True)
        return qs
