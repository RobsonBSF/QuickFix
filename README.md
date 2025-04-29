# QuickFix

---

# 📄 Documentação de Execução do Projeto Django - `project_QuickFix`

## 📌 Pré-requisitos

Certifique-se de ter os seguintes softwares instalados:

- Python 3.10 ou superior
- MySQL Server
- pip (gerenciador de pacotes Python)
- virtualenv (recomendado)
- Git (opcional, para versionamento)
- Django 5.2

---

## 🧰 1. Clonando o Projeto (caso esteja no GitHub)

```bash
git clone https://github.com/seu-usuario/project_QuickFix.git
cd project_QuickFix
```

---

## 🐍 2. Criando e ativando o ambiente virtual

```bash
python -m venv venv
# Ativando no Windows:
venv\Scripts\activate
# Ativando no Linux/macOS:
source venv/bin/activate
```

---

## 📦 3. Instalando dependências

Crie um arquivo `requirements.txt` com os pacotes utilizados (ou use o comando abaixo se já estiver criado):

```bash
pip install django==5.2 mysqlclient widget-tweaks
```

Se estiver usando Windows e tiver erro ao instalar `mysqlclient`, instale o conector:

```bash
pip install mysql-connector-python
```

> **Nota:** Recomenda-se usar `mysqlclient` com MySQL/MariaDB para maior desempenho.

---

## 🛠️ 4. Configurando o banco de dados

Crie um banco de dados MySQL com o nome `quick`. Use o seguinte comando no MySQL:

```sql
CREATE DATABASE quick CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Usuário e senha padrão no `settings.py`:

- **Usuário**: `root`
- **Senha**: `1234`
- **Host**: `localhost`
- **Porta**: `3306`

> Altere essas configurações no arquivo `project_QuickFix/settings.py` se necessário.

---

## 🧱 5. Aplicando as migrações

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 👤 6. Criando superusuário

```bash
python manage.py createsuperuser
```

Siga os passos para informar nome, email e senha.

---

## 🚀 7. Rodando o servidor

```bash
python manage.py runserver
```

Acesse no navegador:  
📍 [`http://127.0.0.1:8000`](http://127.0.0.1:8000)

---

## 📧 8. Envio de emails

Para envio de emails (ex: redefinição de senha), as variáveis estão configuradas com o Gmail:

```python
EMAIL_HOST_USER = 'desesperoprojetodespair@gmail.com'
EMAIL_HOST_PASSWORD = 'senha_app'
```

> É necessário usar uma **senha de app** do Gmail (não sua senha normal). Gere ela em:  
> [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)

---

## 📁 9. Estrutura de pastas esperada

```
project_QuickFix/
├── app_QuickFix/
├── static/
├── templates/
├── project_QuickFix/
│   └── settings.py
├── manage.py
```

---

## ✅ Pronto!

Agora o projeto está rodando localmente com autenticação, templates customizados e envio de email habilitado.
