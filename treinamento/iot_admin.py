from django.contrib import admin
from .iot_models import DispositivoIoT, LeituraIoT, ConfiguracaoDispositivo, AlertaIoT


@admin.register(DispositivoIoT)
class DispositivoIoTAdmin(admin.ModelAdmin):
    list_display = ['device_id', 'nome', 'tipo', 'proprietario', 'status', 'ultimo_ping', 'esta_online']
    list_filter = ['tipo', 'status', 'fabricante']
    search_fields = ['device_id', 'nome', 'mac_address', 'ip_address']
    readonly_fields = ['data_cadastro', 'ultima_atualizacao', 'ultimo_ping']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('device_id', 'nome', 'tipo', 'proprietario')
        }),
        ('Status', {
            'fields': ('status', 'ultimo_ping')
        }),
        ('Informações Técnicas', {
            'fields': ('fabricante', 'modelo', 'firmware_version', 'mac_address', 'ip_address'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('data_cadastro', 'ultima_atualizacao'),
            'classes': ('collapse',)
        }),
    )
    
    def esta_online(self, obj):
        return obj.esta_online()
    esta_online.boolean = True
    esta_online.short_description = 'Online'


@admin.register(LeituraIoT)
class LeituraIoTAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'dispositivo', 'individuo', 'tipo_sensor', 'valor', 'unidade', 'processado', 'qualidade_sinal']
    list_filter = ['tipo_sensor', 'processado', 'qualidade_sinal', 'dispositivo']
    search_fields = ['dispositivo__device_id', 'individuo__nome_completo']
    readonly_fields = ['recebido_em']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('dispositivo', 'individuo', 'timestamp')
        }),
        ('Dados da Leitura', {
            'fields': ('tipo_sensor', 'valor', 'unidade', 'qualidade_sinal', 'nivel_bateria')
        }),
        ('Metadados', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Processamento', {
            'fields': ('processado', 'registro_treinamento', 'recebido_em')
        }),
    )
    
    actions = ['marcar_como_processado', 'criar_registro_treinamento']
    
    def marcar_como_processado(self, request, queryset):
        updated = queryset.update(processado=True)
        self.message_user(request, f'{updated} leituras marcadas como processadas.')
    marcar_como_processado.short_description = 'Marcar como processado'
    
    def criar_registro_treinamento(self, request, queryset):
        from .mqtt_service import mqtt_service
        count = 0
        for leitura in queryset.filter(processado=False):
            mqtt_service._create_training_record(leitura)
            count += 1
        self.message_user(request, f'{count} registros de treinamento criados.')
    criar_registro_treinamento.short_description = 'Criar registro de treinamento'


@admin.register(ConfiguracaoDispositivo)
class ConfiguracaoDispositivoAdmin(admin.ModelAdmin):
    list_display = ['dispositivo', 'intervalo_leitura', 'criar_registro_automatico', 'treinamento_padrao']
    list_filter = ['criar_registro_automatico']
    search_fields = ['dispositivo__device_id', 'dispositivo__nome']
    
    fieldsets = (
        ('Dispositivo', {
            'fields': ('dispositivo',)
        }),
        ('Frequência de Leitura', {
            'fields': ('intervalo_leitura',)
        }),
        ('Alertas', {
            'fields': ('valor_minimo_alerta', 'valor_maximo_alerta'),
        }),
        ('Mapeamento Automático', {
            'fields': ('criar_registro_automatico', 'treinamento_padrao')
        }),
        ('Calibração', {
            'fields': ('fator_calibracao', 'offset_calibracao'),
            'classes': ('collapse',)
        }),
        ('Configurações Extras', {
            'fields': ('configuracoes_extras',),
            'classes': ('collapse',)
        }),
    )


@admin.register(AlertaIoT)
class AlertaIoTAdmin(admin.ModelAdmin):
    list_display = ['criado_em', 'dispositivo', 'individuo', 'tipo', 'severidade', 'visualizado', 'resolvido']
    list_filter = ['tipo', 'severidade', 'visualizado', 'resolvido', 'criado_em']
    search_fields = ['dispositivo__device_id', 'individuo__nome_completo', 'mensagem']
    readonly_fields = ['criado_em', 'visualizado_em', 'resolvido_em']
    date_hierarchy = 'criado_em'
    
    fieldsets = (
        ('Alerta', {
            'fields': ('dispositivo', 'individuo', 'leitura', 'tipo', 'severidade', 'mensagem')
        }),
        ('Status', {
            'fields': ('visualizado', 'visualizado_em', 'resolvido', 'resolvido_em')
        }),
    )
    
    actions = ['marcar_como_visualizado', 'marcar_como_resolvido']
    
    def marcar_como_visualizado(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(visualizado=True, visualizado_em=timezone.now())
        self.message_user(request, f'{updated} alertas marcados como visualizados.')
    marcar_como_visualizado.short_description = 'Marcar como visualizado'
    
    def marcar_como_resolvido(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(resolvido=True, resolvido_em=timezone.now())
        self.message_user(request, f'{updated} alertas marcados como resolvidos.')
    marcar_como_resolvido.short_description = 'Marcar como resolvido'
