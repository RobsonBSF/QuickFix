# **QuickFix**

---

## 📌 Descrição

O **QuickFix** é uma aplicação desenvolvida em **Django** com suporte a **MySQL** e **Docker**, focada em soluções ágeis e escaláveis.
Este repositório contém a configuração de ambiente, dependências e instruções para execução em desenvolvimento.

---

## ⚙️ Instalação e Configuração do Ambiente

### 🔹 Banco de Dados

Você pode utilizar o MySQL via **WorkBench** externo ou rodar via **Docker** com as seguintes configurações:

```yaml
'NAME': 'quickfix',
'USER': 'root',
'PASSWORD': '1234',
'PORT': '3306',
'HOST': 'localhost'
```

---

### 🔹 Ambiente Django (sem Docker)

```bash
# Criar ambiente virtual na raiz do projeto
python -m venv .venv

# Ativar ambiente
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
# Linux/macOS
source .venv/bin/activate

# Atualizar pip
python -m pip install --upgrade pip

# Instalar dependências
pip install -r requirements.txt

# Migrar banco de dados
python manage.py migrate

# Iniciar servidor Django
python manage.py runserver
```

---

### 🔹 Recomendações

* **Windows** → Ambiente de desenvolvimento utilizado
* **PowerShell** → Execução recomendada
* **Python** → Versão atualizada + Pip atualizado
* **VS Code** → IDE sugerida
* **Docker** → Gerenciamento de containers
* **GitHub** → Controle de versão

---

### ⚡ Express Install (com Docker)

1. Clone este repositório:

   ```bash
   git clone https://github.com/SEU_USUARIO/QuickFix.git
   ```
2. Instale o **Docker**.
3. No PowerShell, execute:

   ```bash
   python dist/strat.py p True
   ```

---

## 📖 Documentação

### 🔹 Referências Visuais

* [Figma](https://www.figma.com/design/Y83PcLHzTUz7dkTMUTr4Ky/Quick-fix?node-id=0-1&p=f)

---

## 🛠️ Tecnologias Utilizadas

* **Linguagens:** Python 3.12.2, JavaScript ES6
* **Frontend:** HTML5 semântico, CSS3, Bootstrap
* **Framework:** Django
* **Banco de Dados:** MySQL 9.3.0
* **Ambiente de Desenvolvimento:** Docker, GitHub
* **Comunicação em Tempo Real:** WebSockets (Django Channels), Redis (broker)

---

## 👥 Equipe

* Raphael
* Robson Barbosa
* Roque José Filho

---

