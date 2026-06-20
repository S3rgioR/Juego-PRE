"""
Paquete Model — Capa lógica del patrón MVP.

Contiene las reglas de juego, IA de enemigos y sistema de combate.
Sin dependencias de pygame gráfico ni posiciones de pantalla.

Exporta JuegoModel como punto de acceso principal.
"""

from .JuegoModel import JuegoModel


__all__ = ['JuegoModel']
