# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/spec/v2.0.0.html).

## [Não publicado]

### Adicionado
- Documentação completa do projeto
- Guia de contribuição
- Código de conduta
- Changelog
- Sistema completo de Internet das Coisas (IoT)
- Integração com protocolo MQTT para comunicação em tempo real
- Modelos de dados para dispositivos IoT e leituras de sensores
- Dashboard IoT dedicado para monitoramento de dispositivos
- Sistema de alertas inteligentes baseado em leituras de sensores
- Processamento automático de dados de sensores para registros de treino
- Suporte a dispositivos ESP32 e diversos tipos de sensores
- Serviços de processamento e gerenciamento de alertas
- Templates e interfaces para gerenciamento de dispositivos IoT
- Comandos de gerenciamento para popular dados IoT de exemplo
- Exemplos e simuladores de dispositivos IoT

### Alterado
- Aprimoramento da documentação existente no README.md
- Atualização da arquitetura do sistema para incluir camada IoT
- Expansão da estrutura de pastas para acomodar componentes IoT
- Melhorias na segurança com autenticação para dispositivos conectados

## [1.0.0] - 2025-12-15

### Adicionado
- Versão inicial do sistema de controle de treinamento
- Autenticação de usuários com Django
- Modelos para Indivíduo, Treinamento e Registro de Treinamento
- Consumo de API externa (simulada via DummyJSON)
- Dashboard interativo com gráficos Chart.js
- Interface de administração do Django
- Sistema de captchas para login
- Relatórios estatísticos
- Ranking de usuários
- Visualização em calendário
- Comandos de gerenciamento para popular dados
- Templates responsivos com Bootstrap 5

### Segurança
- Implementação de validações de formulários
- Proteção contra CSRF
- Validação de datas e valores de entrada