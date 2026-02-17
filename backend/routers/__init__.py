"""
Routers del sistema RCA
"""
from routers.auth import get_current_active_user, verificar_permiso_admin

__all__ = ['get_current_active_user', 'verificar_permiso_admin']
