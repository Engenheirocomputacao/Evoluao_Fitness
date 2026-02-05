# 🚀 Como colocar seu projeto no GitHub

Como o **Git não está instalado** no seu sistema, você precisará seguir estes passos manuais. Não se preocupe, é rapidinho!

## 1. Instalar o Git
Abra seu terminal e rode:
```bash
sudo apt update
sudo apt install git -y
```

## 2. Configurar o Git (Se for a primeira vez)
Configure seu nome e email (os mesmos do GitHub):
```bash
git config --global user.name "Seu Nome"
git config --global user.email "seu.email@exemplo.com"
```

## 3. Inicializar o Projeto
Navegue até a pasta do projeto e rode:

```bash
cd "/home/marco/Downloads/Evolução_Fitness "

# Iniciar repositório
git init

# Adicionar todos os arquivos
git add .

# Criar o primeiro "save" (commit)
git commit -m "Primeira versão do Evolução Fitness"
```

## 4. Criar Repositório no GitHub
1. Acesse [github.new](https://github.new)
2. Nomeie o repositório (ex: `evolucao-fitness`)
3. Clique em **Create repository**

## 5. Conectar e Enviar
Na página do GitHub criada, copie os comandos da seção **"…or push an existing repository from the command line"**.

Geralmente são estes:
```bash
git remote add origin https://github.com/SEU_USUARIO/evolucao-fitness.git
git branch -M main
git push -u origin main
```

Pronto! Seu código estará seguro na nuvem. ☁️
