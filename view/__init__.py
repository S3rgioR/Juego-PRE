"""
Paquete View — Capa visual del patrón MVP.

Contiene toda la lógica de representación gráfica (pygame),
gestión de entrada de usuario, cámara y sprites.

Exporta PygameView como punto de acceso principal.
"""

from .view import PygameView
from .PortalView import PortalView
from .PortalFinalView    import PortalFinalView
from .FinDeJuegoSequence import FinDeJuegoSequence

__all__ = ['PygameView']
