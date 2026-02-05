# Arquitetura do Sistema

## Visão Geral

O Controle de Treinamento é uma aplicação web desenvolvida com Django (Python) seguindo o padrão MVC (Model-View-Controller). A arquitetura é dividida em camadas bem definidas para facilitar manutenção, testes e escalabilidade.

## Estrutura de Pastas

```
controle_treinamento/
├── controle_treinamento/     # Configurações principais do projeto Django
│   ├── settings.py          # Configurações do projeto
│   ├── urls.py             # URLs principais do projeto
│   └── wsgi.py             # Ponto de entrada WSGI
├── treinamento/             # Aplicação principal
│   ├── management/         # Comandos de gerenciamento personalizados
│   ├── migrations/         # Migrações do banco de dados
│   ├── services/          # Serviços de negócio
│   │   ├── iot_processor.py  # Processamento de dados IoT
│   │   └── alert_manager.py  # Gerenciamento de alertas
│   ├── templates/          # Templates HTML
│   │   ├── treinamento/
│   │   │   ├── iot/       # Templates IoT
│   │   │   │   ├── dashboard.html
│   │   │   │   ├── device_list.html
│   │   │   │   ├── device_detail.html
│   │   │   │   └── alert_list.html
│   ├── templatetags/       # Tags de template personalizadas
│   ├── admin.py            # Configurações do admin do Django
│   ├── api_service.py      # Serviços de consumo de API externa
│   ├── apps.py             # Configurações da aplicação
│   ├── captcha_utils.py    # Utilitários para manipulação de captchas
│   ├── forms.py            # Formulários do Django
│   ├── iot_admin.py        # Administração de modelos IoT
│   ├── iot_models.py       # Modelos de dados IoT
│   ├── middleware.py       # Middleware personalizado
│   ├── models.py           # Modelos de dados principais
│   ├── mqtt_service.py     # Serviço de comunicação MQTT
│   ├── signals.py          # Sinais do Django
│   ├── tests.py            # Testes automatizados
│   ├── urls.py             # URLs da aplicação
│   └── views/              # Views (controladores)
│       ├── __init__.py
│       ├── auth.py         # Views de autenticação
│       ├── dashboard.py    # Views do dashboard
│       ├── iot.py          # Views IoT
│       ├── perfil.py       # Views de perfil
│       ├── registros.py    # Views de registros
│       └── relatorios.py   # Views de relatórios
├── staticfiles/            # Arquivos estáticos coletados
├── templates/              # Templates base
├── manage.py               # Script de gerenciamento do Django
├── requirements.txt        # Dependências do projeto
└── README.md               # Documentação principal
```

## Camadas da Arquitetura

### 1. Camada de Apresentação (Templates)

Responsável pela interface com o usuário:
- Templates HTML com Bootstrap 5
- JavaScript para interatividade
- Integração com Chart.js para gráficos
- Responsividade para dispositivos móveis

### 2. Camada de Aplicação (Views)

Controla a lógica da aplicação:
- Processamento de requisições HTTP
- Validação de dados de entrada
- Coordenação entre modelos e templates
- Implementação de APIs REST

### 3. Camada de Negócio (Services)

Implementa a lógica de negócio:
- `api_service.py`: Consumo e processamento de APIs externas
- Validações complexas de dados
- Cálculos estatísticos e análises
- Regras de negócio específicas

### 4. Camada de Dados (Models)

Representa a estrutura de dados:
- Mapeamento objeto-relacional com Django ORM
- Validações de integridade
- Relacionamentos entre entidades
- Índices e otimizações de consulta

### 5. Camada IoT (Internet das Coisas)

Responsável pela integração com dispositivos conectados:
- **mqtt_service.py**: Comunicação com broker MQTT
- **iot_processor.py**: Processamento de dados de sensores
- **alert_manager.py**: Sistema de alertas inteligentes
- **iot_models.py**: Modelos específicos para dispositivos IoT
- Protocolo de ingestão de dados em tempo real
- Gerenciamento de configurações de dispositivos

## Componentes Principais

### Models

#### Indivíduo
Representa um usuário do sistema com perfil extendido.

#### Treinamento
Define os tipos de treinamento disponíveis com unidades de medida.

#### RegistroTreinamento
Registra os resultados dos treinamentos realizados por cada indivíduo.

#### LetterCaptcha
Gerencia o sistema de captchas para prevenção de bots.

#### DispositivoIoT
Representa dispositivos conectados ao sistema:
- Gerenciamento de dispositivos ESP32 e sensores
- Monitoramento de status e conectividade
- Configurações específicas por dispositivo

#### LeituraIoT
Armazena dados coletados dos sensores:
- Leituras em tempo real de diversos tipos de sensores
- Processamento automático para conversão em registros de treino
- Histórico completo de dados coletados

#### ConfiguracaoDispositivo
Configurações personalizadas para cada dispositivo:
- Intervalos de leitura
- Limites para geração de alertas
- Mapeamento automático para tipos de treinamento

### Views

#### Autenticação
- `CustomLoginView`: Sistema de login com captcha
- `register_view`: Registro de novos usuários
- `logout_view`: Logout de usuários

#### Dashboard
- `dashboard_view`: Página principal com métricas
- `dashboard_data_api`: API para dados do dashboard

#### Gerenciamento
- `treinamentos_view`: Listagem de treinamentos
- `registros_view`: Gerenciamento de registros
- `relatorios_view`: Relatórios estatísticos
- `perfil_view`: Perfil do usuário
- `ranking_view`: Classificação de usuários
- `calendar_view`: Visualização em calendário

#### IoT
- `iot_dashboard`: Dashboard principal de dispositivos IoT
- `device_list`: Listagem e gerenciamento de dispositivos
- `device_detail`: Detalhes específicos de um dispositivo
- `alert_list`: Lista de alertas gerados
- `iot_data_ingest`: Endpoint para recepção de dados de sensores
- `iot_device_status`: Verificação de status de dispositivos

### Services

#### ApiService
- `fetch_and_process_training_data`: Consome API externa e processa dados
- `calculate_average_performance`: Calcula médias de desempenho

#### IoT Services

##### IoTDataProcessor
- `process_reading`: Processa leituras de sensores
- `create_training_record`: Converte dados em registros de treino
- `_calcular_confiabilidade`: Calcula score de confiabilidade dos dados

##### AlertManager
- `check_reading_alerts`: Verifica limites e gera alertas
- `get_active_alerts_for_user`: Retorna alertas ativos por usuário
- `get_critical_alerts_count`: Contagem de alertas críticos

#### CaptchaUtils
- `generate_puzzle_captcha`: Gera novos captchas
- `verify_puzzle_captcha`: Verifica soluções de captchas

### Forms

#### ModelForms
- `IndividuoForm`: Formulário para perfil de usuário
- `TreinamentoForm`: Formulário para cadastro de treinamentos
- `RegistroTreinamentoForm`: Formulário para registros de treinamento

#### AuthenticationForms
- `SimpleCaptchaLoginForm`: Login com captcha simples
- `CaptchaLoginForm`: Login com captcha de letras
- `LetterCaptchaForm`: Formulário para captcha de letras

## Fluxos de Dados

### Autenticação de Usuário
```
Cliente → LoginView → SimpleCaptchaLoginForm → Autenticação Django → Dashboard
```

### Registro de Usuário
```
Cliente → RegisterView → UserCreationForm → Criação de Indivíduo → Dashboard
```

### Consumo de API Externa
```
Management Command → ApiService.fetch_and_process_training_data → DummyJSON API → Processamento → Banco de Dados
```

### Geração de Dashboard
```
Cliente → DashboardView → Consultas no Banco de Dados → Processamento de Dados → Templates com Chart.js
```

### Comunicação IoT
```
Dispositivo ESP32 → MQTT Broker → MqttService → IoTDataProcessor → Banco de Dados → AlertManager
```

### Processamento de Dados de Sensores
```
Leitura IoT → Processamento Automático → Registro de Treinamento → Dashboard em Tempo Real
```

### Sistema de Alertas
```
Valor de Sensor → Verificação de Limites → AlertManager → Notificação ao Usuário
```

## Padrões de Design Utilizados

### MVC (Model-View-Controller)
Separação clara entre:
- **Model**: Models.py (dados)
- **View**: Templates (apresentação)
- **Controller**: Views.py (lógica)

### Repository Pattern
Abstração das operações de banco de dados através dos models do Django.

### Observer Pattern
Utilização de sinais do Django para eventos pós-migração.

### Factory Pattern
Criação de formulários e views especializadas.

## Segurança

### Autenticação
- Django Auth integrado
- Proteção CSRF
- Validação de sessões

### Validação de Dados
- Validações no modelo
- Validações nos formulários
- Sanitização de entradas

### Prevenção de Bots
- Sistema de captchas
- Rate limiting no middleware

## Performance

### Otimizações
- Consultas otimizadas com select_related e prefetch_related
- Indexação de campos de busca
- Cache de consultas frequentes

### Scalability
- Estrutura modular fácil de escalar
- Separação de preocupações
- Pronta para horizontal scaling

## Tecnologias

### Backend
- Python 3.x
- Django 5.2+
- SQLite (desenvolvimento) / PostgreSQL (produção)
- paho-mqtt para comunicação MQTT
- Django REST Framework para APIs

### Frontend
- HTML5
- CSS3/Bootstrap 5
- JavaScript
- Chart.js para gráficos

### IoT
- Protocolo MQTT para comunicação em tempo real
- Suporte a microcontroladores ESP32
- Processamento de dados de sensores em tempo real
- Sistema de alertas inteligentes

### Ferramentas
- pip para gerenciamento de dependências
- Django Admin para interface administrativa
- Comandos de gerenciamento personalizados
- Simuladores de dispositivos para testes