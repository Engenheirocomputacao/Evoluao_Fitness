from django.urls import path
from .views import (
    home_view, dashboard_view, register_view, treinamentos_view,
    registros_view, relatorios_view, perfil_view, ranking_view,
    calendar_view, dashboard_data_api, calendar_data_api, sobre_view
)
from .views.iot import (
    iot_dashboard, device_list, device_detail, device_create, device_edit, device_delete,
    toggle_device_offline,
    alert_list, alert_mark_viewed, alert_mark_resolved,
    iot_data_ingest, iot_device_status
)
from . import captcha_utils

urlpatterns = [
    path('', home_view, name='home'),
    path('', home_view, name='home_view'),  # Alias para manter compatibilidade com templates existentes
    path('dashboard/', dashboard_view, name='dashboard_view'),
    path('register/', register_view, name='register_view'),
    path('treinamentos/', treinamentos_view, name='treinamentos_view'),
    path('registros/', registros_view, name='registros_view'),
    path('relatorios/', relatorios_view, name='relatorios_view'),
    path('perfil/', perfil_view, name='perfil_view'),
    path('ranking/', ranking_view, name='ranking_view'),
    path('calendar/', calendar_view, name='calendar_view'),
    path('api/dashboard-data/', dashboard_data_api, name='dashboard_data_api'),
    path('api/calendar-data/', calendar_data_api, name='calendar_data_api'),
    
    # IoT Management
    path('iot/', iot_dashboard, name='iot_dashboard'),
    path('iot/devices/', device_list, name='device_list'),
    path('iot/devices/create/', device_create, name='device_create'),
    path('iot/devices/<int:device_id>/edit/', device_edit, name='device_edit'),
    path('iot/devices/<int:device_id>/', device_detail, name='device_detail'),
    path('iot/devices/<int:device_id>/delete/', device_delete, name='device_delete'),
    path('iot/devices/<int:device_id>/toggle-offline/', toggle_device_offline, name='toggle_device_offline'),
    
    # IoT Alerts
    path('iot/alerts/', alert_list, name='alert_list'),
    path('iot/alerts/<int:alert_id>/viewed/', alert_mark_viewed, name='alert_mark_viewed'),
    path('iot/alerts/<int:alert_id>/resolved/', alert_mark_resolved, name='alert_mark_resolved'),
    
    # IoT API Endpoints
    path('api/iot/ingest/', iot_data_ingest, name='iot_data_ingest'),
    path('api/iot/status/<str:device_id>/', iot_device_status, name='iot_device_status'),
    
    # Captcha endpoints
    path('captcha/generate/', captcha_utils.generate_puzzle_captcha, name='generate_captcha'),
    path('captcha/verify/', captcha_utils.verify_puzzle_captcha, name='verify_captcha'),
    path('sobre/', sobre_view, name='sobre_view'),
]