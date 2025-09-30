

def BD_pull(Tabela):
    bd = list(Tabela.objects.values())  # Já retorna uma lista de dicionários direto do ORM
    print('Tabela:', bd)  # Debug no console
    return bd  # Retorna um array de objetos

