"""
Views package for treinamento app.

This package contains all views organized by functionality:
- auth: Authentication views (login, register, logout)
- dashboard: Dashboard and home views with APIs
- registros: Training records management
- perfil: User profile and calendar
- relatorios: Reports and ranking
"""

# Auth views
from .auth import (
    CustomLoginView,
    login_view,
    register_view,
    logout_view,
)

# Dashboard views
from .dashboard import (
    home_view,
    dashboard_view,
    dashboard_data_api,
    sobre_view,
)

# Registros views
from .registros import (
    treinamentos_view,
    registros_view,
)

# Perfil views
from .perfil import (
    perfil_view,
    calendar_view,
    calendar_data_api,
)

# Relatorios views
from .relatorios import (
    relatorios_view,
    ranking_view,
    admin_only_view,
)


# Re-export utility functions for backwards compatibility
from ..utils import (
    is_admin_user,
    calcular_dias_consecutivos,
)

__all__ = [
    # Auth
    'CustomLoginView',
    'login_view',
    'register_view',
    'logout_view',
    # Dashboard
    'home_view',
    'dashboard_view',
    'dashboard_data_api',
    'sobre_view',
    # Registros
    'treinamentos_view',
    'registros_view',
    # Perfil
    'perfil_view',
    'calendar_view',
    'calendar_data_api',
    # Relatorios
    'relatorios_view',
    'ranking_view',
    'admin_only_view',
    # Utils
    'is_admin_user',
    'calcular_dias_consecutivos',
]
