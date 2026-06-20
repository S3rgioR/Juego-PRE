"""
Paquete View — Capa visual del patrón MVP.

Contiene toda la lógica de representación gráfica (pygame),
gestión de entrada de usuario, cámara y sprites.

API pública
-----------
Todos los módulos externos (main.py, presenter.py) deben importar
exclusivamente desde este paquete, nunca desde submódulos internos:

    from view import PygameView
    from view import AudioManager
    from view import FinDeJuegoSequence

Los submódulos internos (PortalView, CheckpointView, etc.) son detalles
de implementación de la Vista y no forman parte de la interfaz pública
hacia el Presenter ni hacia main.
"""

from .view               import PygameView
from .AudioManager       import AudioManager
from .FinDeJuegoSequence import FinDeJuegoSequence

__all__ = [
    "PygameView",
    "AudioManager",
    "FinDeJuegoSequence",
]
