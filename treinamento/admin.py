from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Individuo, Treinamento, RegistroTreinamento
from .iot_models import DispositivoIoT, LeituraIoT, ConfiguracaoDispositivo, AlertaIoT


@admin.register(Individuo)
class IndividuoAdmin(admin.ModelAdmin):
    list_display = ('nome_completo', 'user', 'data_nascimento', 'ativo')
    search_fields = ('nome_completo', 'user__username')
    list_filter = ('ativo',)


@admin.register(Treinamento)
class TreinamentoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'unidade_medida')
    search_fields = ('nome',)


@admin.register(RegistroTreinamento)
class RegistroTreinamentoAdmin(admin.ModelAdmin):
    list_display = ('individuo', 'treinamento', 'data', 'valor_alcançado', 'fonte_dados')
    list_filter = ('treinamento', 'data', 'fonte_dados', 'esporte')
    search_fields = ('individuo__nome_completo', 'treinamento__nome')
    date_hierarchy = 'data'


# ============= IoT Admin Interfaces =============

class ConfiguracaoDispositivoInline(admin.StackedInline):
    model = ConfiguracaoDispositivo
    extra = 0
    can_delete = False


class LeituraIoTInline(admin.TabularInline):
    model = LeituraIoT
    extra = 0
    readonly_fields = ('timestamp', 'tipo_sensor', 'valor', 'unidade', 'qualidade_sinal', 'recebido_em')
    fields = ('timestamp', 'tipo_sensor', 'valor', 'unidade', 'qualidade_sinal')
    max_num = 10
    ordering = ['-timestamp']
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(DispositivoIoT)
class DispositivoIoTAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'nome', 'tipo', 'proprietario', 'status_badge', 'online_status', 'ultimo_ping')
    list_filter = ('status', 'tipo', 'data_cadastro')
    search_fields = ('device_id', 'nome', 'proprietario__nome_completo', 'mac_address', 'ip_address')
    readonly_fields = ('data_cadastro', 'ultima_atualizacao', 'online_status')
    inlines = [ConfiguracaoDispositivoInline, LeituraIoTInline]
    
    fieldsets = (
        ('Identificação', {
            'fields': ('device_id', 'nome', 'tipo')
        }),
        ('Relacionamentos', {
            'fields': ('proprietario',)
        }),
        ('Status', {
            'fields': ('status', 'ultimo_ping', 'online_status')
        }),
        ('Metadados', {
            'fields': ('fabricante', 'modelo', 'firmware_version'),
            'classes': ('collapse',)
        }),
        ('Dados Técnicos', {
            'fields': ('mac_address', 'ip_address'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('data_cadastro', 'ultima_atualizacao'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['marcar_ativo', 'marcar_inativo', 'marcar_manutencao']
    
    def status_badge(self, obj):
        colors = {
            'active': 'green',
            'inactive': 'gray',
            'maintenance': 'orange',
            'offline': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def online_status(self, obj):
        if obj.esta_online():
            return '<span style="color: green;">● Online</span>'
        return '<span style="color: red;">● Offline</span>'
    online_status.short_description = 'Conexão'
    online_status.allow_tags = True
    
    def marcar_ativo(self, request, queryset):
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} dispositivo(s) marcado(s) como ativo(s).')
    marcar_ativo.short_description = 'Marcar como ativo'
    
    def marcar_inativo(self, request, queryset):
        updated = queryset.update(status='inactive')
        self.message_user(request, f'{updated} dispositivo(s) marcado(s) como inativo(s).')
    marcar_inativo.short_description = 'Marcar como inativo'
    
    def marcar_manutencao(self, request, queryset):
        updated = queryset.update(status='maintenance')
        self.message_user(request, f'{updated} dispositivo(s) marcado(s) em manutenção.')
    marcar_manutencao.short_description = 'Marcar em manutenção'


@admin.register(LeituraIoT)
class LeituraIoTAdmin(admin.ModelAdmin):
    list_display = ('dispositivo', 'individuo', 'tipo_sensor', 'valor_formatado', 'timestamp', 'qualidade_sinal', 'processado_badge')
    list_filter = ('tipo_sensor', 'qualidade_sinal', 'processado', 'timestamp')
    search_fields = ('dispositivo__device_id', 'dispositivo__nome', 'individuo__nome_completo')
    readonly_fields = ('recebido_em',)
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Dispositivo e Usuário', {
            'fields': ('dispositivo', 'individuo')
        }),
        ('Dados da Leitura', {
            'fields': ('timestamp', 'tipo_sensor', 'valor', 'unidade')
        }),
        ('Qualidade', {
            'fields': ('qualidade_sinal', 'nivel_bateria')
        }),
        ('Metadados', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Processamento', {
            'fields': ('processado', 'registro_treinamento'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('recebido_em',),
            'classes': ('collapse',)
        }),
    )
    
    def valor_formatado(self, obj):
        return f"{obj.valor} {obj.unidade}"
    valor_formatado.short_description = 'Valor'
    
    def processado_badge(self, obj):
        if obj.processado:
            return '<span style="color: green;">✓ Sim</span>'
        return '<span style="color: orange;">⏳ Não</span>'
    processado_badge.short_description = 'Processado'
    processado_badge.allow_tags = True


@admin.register(ConfiguracaoDispositivo)
class ConfiguracaoDispositivoAdmin(admin.ModelAdmin):
    list_display = ('dispositivo', 'intervalo_leitura', 'criar_registro_automatico', 'treinamento_padrao')
    list_filter = ('criar_registro_automatico', 'criado_em')
    search_fields = ('dispositivo__device_id', 'dispositivo__nome')
    readonly_fields = ('criado_em', 'atualizado_em')
    
    fieldsets = (
        ('Dispositivo', {
            'fields': ('dispositivo',)
        }),
        ('Frequência de Envio', {
            'fields': ('intervalo_leitura',)
        }),
        ('Limites e Alertas', {
            'fields': ('valor_minimo_alerta', 'valor_maximo_alerta')
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
        ('Timestamps', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AlertaIoT)
class AlertaIoTAdmin(admin.ModelAdmin):
    list_display = ('dispositivo', 'individuo', 'tipo', 'severidade_badge', 'mensagem_curta', 'visualizado_badge', 'resolvido_badge', 'criado_em')
    list_filter = ('tipo', 'severidade', 'visualizado', 'resolvido', 'criado_em')
    search_fields = ('dispositivo__device_id', 'dispositivo__nome', 'individuo__nome_completo', 'mensagem')
    readonly_fields = ('criado_em', 'visualizado_em', 'resolvido_em')
    date_hierarchy = 'criado_em'
    
    fieldsets = (
        ('Relacionamentos', {
            'fields': ('dispositivo', 'individuo', 'leitura')
        }),
        ('Alerta', {
            'fields': ('tipo', 'severidade', 'mensagem')
        }),
        ('Status', {
            'fields': ('visualizado', 'visualizado_em', 'resolvido', 'resolvido_em')
        }),
        ('Timestamps', {
            'fields': ('criado_em',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['marcar_visualizado', 'marcar_resolvido']
    
    def severidade_badge(self, obj):
        colors = {
            'info': '#17a2b8',
            'warning': '#ffc107',
            'critical': '#dc3545',
        }
        color = colors.get(obj.severidade, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_severidade_display()
        )
    severidade_badge.short_description = 'Severidade'
    
    def mensagem_curta(self, obj):
        return obj.mensagem[:50] + '...' if len(obj.mensagem) > 50 else obj.mensagem
    mensagem_curta.short_description = 'Mensagem'
    
    def visualizado_badge(self, obj):
        if obj.visualizado:
            return '<span style="color: green;">✓</span>'
        return '<span style="color: gray;">✗</span>'
    visualizado_badge.short_description = 'Visto'
    visualizado_badge.allow_tags = True
    
    def resolvido_badge(self, obj):
        if obj.resolvido:
            return '<span style="color: green;">✓</span>'
        return '<span style="color: gray;">✗</span>'
    resolvido_badge.short_description = 'Resolvido'
    resolvido_badge.allow_tags = True
    
    def marcar_visualizado(self, request, queryset):
        updated = queryset.filter(visualizado=False).update(visualizado=True, visualizado_em=timezone.now())
        self.message_user(request, f'{updated} alerta(s) marcado(s) como visualizado(s).')
    marcar_visualizado.short_description = 'Marcar como visualizado'
    
    def marcar_resolvido(self, request, queryset):
        updated = queryset.filter(resolvido=False).update(resolvido=True, resolvido_em=timezone.now())
        self.message_user(request, f'{updated} alerta(s) marcado(s) como resolvido(s).')
    marcar_resolvido.short_description = 'Marcar como resolvido'
