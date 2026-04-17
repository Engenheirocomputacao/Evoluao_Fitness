# Controle de Treinamento

Este é um aplicativo web desenvolvido em **Django (Python)** com **SQLite** para o controle e acompanhamento de treinamento de múltiplos indivíduos. O aplicativo consome uma API externa (simulada via DummyJSON) para popular dados de treinamento e apresenta as médias alcançadas em um dashboard interativo.

## 📋 Índice

- [Funcionalidades](#funcionalidades)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Arquitetura do Sistema](#arquitetura-do-sistema)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Modelos de Dados](#modelos-de-dados)
- [APIs e Integrações](#apis-e-integrações)
- [Como Executar o Projeto](#como-executar-o-projeto)
- [Comandos de Gerenciamento](#comandos-de-gerenciamento)
- [Endpoints da API](#endpoints-da-api)
- [Testes](#testes)
- [Deploy e Configuração](#deploy-e-configuração)
- [Contribuição](#contribuição)
- [Licença](#licença)

## Funcionalidades

*   **Autenticação de Usuários:** Sistema de login e registro para múltiplos indivíduos.
*   **Modelagem de Dados:** Modelos para Indivíduo, Treinamento e Registro de Treinamento.
*   **Consumo de API:** Simulação de consumo de API externa para obtenção de dados de treinamento.
*   **Dashboard:** Visualização de médias de desempenho por indivíduo e comparação geral, utilizando gráficos Chart.js.
*   **Administração:** Interface de administração do Django para gerenciamento de usuários, treinamentos e registros.
*   **Relatórios:** Geração de relatórios estatísticos sobre o desempenho dos usuários.
*   **Ranking:** Classificação dos usuários com base em seu desempenho.
*   **Calendário:** Visualização dos registros de treinamento em formato de calendário.
*   **📊 Sistema IoT Completo:** Integração com dispositivos fitness para coleta automática de dados em tempo real através de protocolo MQTT.
*   **📡 Gerenciamento de Dispositivos:** Cadastro, monitoramento e configuração de dispositivos ESP32 e outros sensores.
*   **📈 Dashboard IoT:** Interface dedicada para visualização de dados de sensores em tempo real.
*   **🔔 Sistema de Alertas Inteligente:** Monitoramento automatizado com notificações configuráveis para valores fora dos padrões.
*   **🔄 Processamento Automático:** Conversão automática de leituras de sensores em registros de treino.
*   **🛡️ Segurança IoT:** Autenticação e autorização para dispositivos conectados.

## Tecnologias Utilizadas

*   **Backend:** Python 3.x, Django 5.2+
*   **Frontend:** HTML5, CSS3, Bootstrap 5, JavaScript, Chart.js
*   **Banco de Dados:** SQLite (desenvolvimento), PostgreSQL (produção)
*   **Autenticação:** Django Auth, Session Management
*   **APIs Externas:** DummyJSON (simulação)
*   **IoT:** MQTT Protocol, ESP32 Integration, paho-mqtt
*   **Processamento de Dados:** Serviços de processamento em tempo real
*   **Sistema de Alertas:** Monitoramento inteligente com notificações
*   **Ferramentas de Desenvolvimento:** pip, virtualenv

## Arquitetura do Sistema

O sistema segue o padrão MVC (Model-View-Controller) implementado pelo Django:

1. **Models:** Definem a estrutura de dados e regras de negócio
2. **Views:** Controlam a lógica da aplicação e processam requisições
3. **Templates:** Responsáveis pela apresentação dos dados
4. **URLs:** Mapeiam URLs para views específicas

A aplicação é dividida em módulos funcionais:
* `controle_treinamento/`: Configurações principais do projeto
* `treinamento/`: Aplicação principal de controle de treinamento

## Estrutura do Projeto

```
controle_treinamento/
├── asgi.py
├── settings.py
├── urls.py
└── wsgi.py

treinamento/
├── management/
│   └── commands/
│       ├── populate_data.py
│       ├── create_iot_sample_data.py
│       └── populate_admin.py
├── migrations/
├── services/
│   ├── iot_processor.py
│   └── alert_manager.py
├── templates/
│   ├── registration/
│   ├── treinamento/
│   │   ├── iot/
│   │   │   ├── dashboard.html
│   │   │   ├── device_list.html
│   │   │   ├── device_detail.html
│   │   │   └── alert_list.html
├── templatetags/
├── __init__.py
├── admin.py
├── api_service.py
├── apps.py
├── captcha_utils.py
├── iot_admin.py
├── iot_models.py
├── middleware.py
├── models.py
├── mqtt_service.py
├── signals.py
├── tests.py
├── urls.py
└── views/
    ├── __init__.py
    ├── auth.py
    ├── dashboard.py
    ├── iot.py
    ├── perfil.py
    ├── registros.py
    └── relatorios.py

staticfiles/
templates/
docs/
scripts/
tests/
manage.py
requirements.txt
```

## Modelos de Dados

### Indivíduo
Representa um usuário do sistema.

* `user`: Relacionamento.OneToOne com User do Django
* `nome_completo`: String (255 caracteres)
* `data_nascimento`: Date (opcional)
* `ativo`: Boolean (padrão: True)
* `avatar`: ImageField (opcional)

### Treinamento
Define os tipos de treinamento disponíveis.

* `nome`: String única (100 caracteres)
* `unidade_medida`: Escolha entre min, km, kg, rep, out
* `descricao`: Text (opcional)

### RegistroTreinamento
Registra os resultados dos treinamentos realizados.

* `individuo`: ForeignKey para Indivíduo
* `treinamento`: ForeignKey para Treinamento
* `data`: Date
* `valor_alcançado`: Decimal (10,2)
* `observacoes`: Text (500 caracteres, opcional)

### LetterCaptcha
Modelo para gerenciamento de captchas.

* `session_key`: String (255 caracteres)
* `letters`: String (10 caracteres)
* `created_at`: DateTime
* `is_solved`: Boolean (padrão: False)

### DispositivoIoT
Modelo para gerenciamento de dispositivos IoT.

* `device_id`: String única (100 caracteres)
* `nome`: String (200 caracteres)
* `tipo`: Escolha entre heartrate, steps, weight, reps, gps, temperature, generic
* `proprietario`: ForeignKey para Indivíduo
* `status`: active, inactive, maintenance, offline
* `ultimo_ping`: DateTime (última comunicação)

### LeituraIoT
Registros de dados coletados dos sensores.

* `dispositivo`: ForeignKey para DispositivoIoT
* `individuo`: ForeignKey para Indivíduo
* `timestamp`: DateTime
* `tipo_sensor`: Tipo de sensor
* `valor`: Decimal
* `unidade`: Unidade de medida
* `processado`: Boolean

### ConfiguracaoDispositivo
Configurações específicas para cada dispositivo.

* `dispositivo`: OneToOne com DispositivoIoT
* `intervalo_leitura`: Integer (segundos)
* `criar_registro_automatico`: Boolean
* `valor_minimo_alerta`: Decimal (opcional)
* `valor_maximo_alerta`: Decimal (opcional)

### PesoHistorico
Histórico de evolução de peso do usuário.

* `individuo`: ForeignKey para Indivíduo
* `peso`: Decimal (kg)
* `data_registro`: Date
* `observacoes`: Text

### Funcionalidades Sociais (Em Desenvolvimento)
Modelos para interação social entre usuários.

* **Seguidor**: Relacionamento de "seguir" entre usuários.
* **Kudos**: Sistema de "curtidas" em registros de treinamento.
* **Comentario**: Comentários em registros de treinamento.

## APIs e Integrações

### API Interna
O sistema possui endpoints de API internos para alimentar o dashboard:

* `/api/dashboard-data/`: Retorna dados estatísticos para o dashboard
* `/api/calendar-data/`: Retorna dados para o calendário

### API Externa (Simulada)
Utiliza a API DummyJSON (`https://dummyjson.com/products`) para simular dados de treinamento.
O campo `rating` dos produtos é usado como `valor_alcançado` nos registros.

### API IoT
O sistema oferece endpoints dedicados para comunicação com dispositivos IoT:

* `/iot/api/data-ingest/`: Recebe dados de sensores via POST
* `/iot/api/device-status/<device_id>/`: Retorna status do dispositivo
* `/iot/api/alerts/`: Gerencia alertas do sistema

Formato de dados esperado para ingestão IoT:
```json
{
  "device_id": "ESP32_001",
  "readings": [
    {
      "tipo": "heartrate",
      "valor": 150,
      "timestamp": "2026-01-23T20:00:00Z",
      "unidade": "bpm"
    }
  ]
}
```

## Como Executar o Projeto

### Pré-requisitos

*   Python 3.8+
*   pip (gerenciador de pacotes Python)
*   virtualenv (opcional, mas recomendado)

### Ambiente de Desenvolvimento

1.  **Clonar o Repositório:**
    ```bash
    git clone <url-do-repositorio>
    cd controle_treinamento
    ```

2.  **Criar e Ativar Ambiente Virtual:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    # ou
    venv\Scripts\activate     # Windows
    ```

3.  **Instalar Dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurar Variáveis de Ambiente (opcional):**
    ```bash
    export DJANGO_SECRET_KEY='sua-secret-key-aqui'
    export DEBUG=True
    ```

5.  **Aplicar Migrações:**
    ```bash
    python manage.py migrate
    ```

6.  **Popular o Banco de Dados (Opcional, mas Recomendado):**
    ```bash
    python manage.py populate_data
    ```

7.  **Executar o Servidor de Desenvolvimento:**
    ```bash
    python manage.py runserver 0.0.0.0:8000
    ```

8.  **Acessar o Aplicativo:**
    *   **Aplicação:** `http://localhost:8000/`
    *   **Admin:** `http://localhost:8000/admin/` (usuário: `admin`, senha: `adminpass`)

### Utilizando o Docker Compose

Para uma prova de conceito rápida ou ambiente de desenvolvimento isolado, você pode utilizar o Docker para subir a aplicação, a camada de cache Redis e o Broker MQTT simultaneamente.

**Pré-requisitos:**
* Docker instalado.
* Docker Compose instalado.

**Passo a Passo:**

1.  **Construir e Iniciar os Containers:**
    ```bash
    docker-compose up --build
    ```

2.  **Preparar o Banco de Dados:**
    Em um novo terminal (com os containers rodando), caso utilize um banco de produção, execute as migrações:
    ```bash
    docker-compose exec web python manage.py migrate
    ```

3.  **Popular Dados e Criar Admin:**
    Execute o comando de população padrão para criar o usuário `admin` (senha: `adminpass`) e dados de exemplo:
    ```bash
    docker-compose exec web python manage.py populate_data
    ```
    *(Opcional)* Para testar as funções IoT, popule dados de sensores simulados:
    ```bash
    docker-compose exec web python manage.py create_iot_sample_data
    ```

4.  **Acesso:**
    * Aplicação: `http://localhost:8000/`
    * Dashboard IoT: `http://localhost:8000/iot/`

5.  **Simular Dispositivos IoT:**
    Com o ambiente Docker rodando, você pode executar o simulador localmente para enviar dados ao container MQTT:
    ```bash
    python iot_examples/iot_simulator.py
    ```

### Ambiente de Produção

Para ambiente de produção, considere:

*   Usar um servidor WSGI como Gunicorn
*   Configurar um proxy reverso como Nginx
*   Utilizar PostgreSQL em vez de SQLite
*   Configurar variáveis de ambiente para segurança
*   Habilitar HTTPS

## Comandos de Gerenciamento

### populate_data
Popula o banco de dados com dados iniciais e simulados.

```bash
python manage.py populate_data
```

Este comando:
1. Cria um superusuário admin (senha: adminpass)
2. Cria treinamentos de exemplo
3. Gera 20 indivíduos fictícios
4. Cria registros de treinamento simulados

### create_iot_sample_data
Popula o banco de dados com dispositivos IoT e dados de sensores de exemplo.

```bash
python manage.py create_iot_sample_data
```

Este comando:
1. Cria dispositivos IoT de exemplo (monitores cardíacos, contadores de passos, GPS)
2. Gera leituras de sensores simuladas
3. Configura alertas e parâmetros
4. Demonstra todas as funcionalidades IoT

### Scripts Utilitários
Scripts auxiliares estão localizados na pasta `scripts/`:

* **População de Dados:** `python scripts/populate/executar_populacao.py`
* **Debug:** `python scripts/debug/debug_django.py`

### Outros Comandos Úteis

```bash
# Criar migrações
python manage.py makemigrations

# Aplicar migrações
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Coletar arquivos estáticos
python manage.py collectstatic

# Rodar testes
python manage.py test
```

## Endpoints da API

### Endpoints Públicos

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/` | Página inicial |
| GET/POST | `/accounts/login/` | Autenticação de usuário |
| GET/POST | `/register/` | Registro de novo usuário |
| GET | `/captcha/generate/` | Gera um novo captcha |
| POST | `/captcha/verify/` | Verifica a solução do captcha |

### Endpoints Protegidos

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/dashboard/` | Dashboard do usuário |
| GET | `/api/dashboard-data/` | Dados para o dashboard (JSON) |
| GET | `/api/calendar-data/` | Dados para o calendário (JSON) |
| GET | `/treinamentos/` | Lista de treinamentos |
| GET/POST | `/registros/` | Gerenciamento de registros |
| GET | `/relatorios/` | Relatórios estatísticos |
| GET/POST | `/perfil/` | Perfil do usuário |
| GET | `/ranking/` | Ranking de usuários |
| GET | `/calendar/` | Visualização em calendário |
| GET | `/iot/` | Dashboard IoT principal |
| GET | `/iot/devices/` | Lista de dispositivos IoT |
| GET/POST | `/iot/devices/create/` | Cadastro de novo dispositivo |
| GET | `/iot/devices/<id>/` | Detalhes do dispositivo |
| GET | `/iot/alerts/` | Lista de alertas IoT |
| POST | `/iot/api/data-ingest/` | Ingestão de dados de sensores |
| GET | `/iot/api/device-status/<device_id>/` | Status do dispositivo |

### Parâmetros da API

#### `/api/dashboard-data/`

Parâmetros de query:
* `period`: Filtra por período (7, 30, 90, all)
* `training_type`: Filtra por tipo de treinamento
* `date_from`: Data inicial (formato YYYY-MM-DD)
* `date_to`: Data final (formato YYYY-MM-DD)

Exemplo: `/api/dashboard-data/?period=30&training_type=Corrida`

#### `/api/calendar-data/`

Parâmetros de query:
* `month`: Mês (1-12)
* `year`: Ano

Exemplo: `/api/calendar-data/?month=12&year=2025`

## Testes

O projeto inclui testes automatizados para garantir a qualidade do código.

### Executar Testes

```bash
# Rodar todos os testes
python manage.py test

# Rodar testes de uma app específica
python manage.py test treinamento

# Rodar testes com cobertura
coverage run --source='.' manage.py test
coverage report
```

### Estratégia de Testes

1. **Testes Unitários:** Validam modelos e funções individuais
2. **Testes de Integração:** Verificam a interação entre componentes
3. **Testes de Views:** Asseguram o comportamento correto das páginas
4. **Testes de API:** Validam os endpoints REST

## Deploy e Configuração

### Configuração de Produção

1. **Configurar settings.py para produção:**
   * `DEBUG = False`
   * `ALLOWED_HOSTS` configurado corretamente
   * `SECRET_KEY` protegida por variáveis de ambiente
   * Banco de dados configurado para PostgreSQL

2. **Servidor WSGI (Gunicorn):**
   ```bash
   pip install gunicorn
   gunicorn controle_treinamento.wsgi:application --bind 0.0.0.0:8000
   ```

3. **Proxy Reverso (Nginx):**
   Configure Nginx para servir arquivos estáticos e encaminhar requisições para Gunicorn.

4. **HTTPS:**
   Utilize Let's Encrypt para configurar SSL/TLS.

### Variáveis de Ambiente Importantes

```bash
DJANGO_SECRET_KEY=sua-chave-secreta
DEBUG=False
DATABASE_URL=postgresql://usuario:senha@host:port/banco
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com
```

### Backup e Monitoramento

* Configure backups regulares do banco de dados
* Implemente logging adequado
* Monitore uso de memória e CPU
* Configure alertas para erros críticos

## Contribuição

### Processo de Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

### Padrões de Código

* Siga o PEP 8 para Python
* Utilize docstrings para funções e classes
* Mantenha mensagens de commit claras e descritivas
* Escreva testes para novas funcionalidades

### Reportando Issues

Ao reportar problemas, inclua:
* Versão do Python e Django
* Passos para reproduzir o problema
* Mensagens de erro completas
* Informações do ambiente (SO, navegador, etc.)

## Licença

Este projeto é licenciado e desenvolvido pelos Alunos de Engenharia da Computação - UNIVESP.
