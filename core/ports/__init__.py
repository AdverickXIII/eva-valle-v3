"""
Puertos (interfaces abstractas) del proyecto eva-valle-v3.0.

Los puertos definen los contratos entre el nucleo de dominio y el mundo
exterior. El nucleo solo conoce estos contratos; las implementaciones
concretas (adaptadores) viven fuera del nucleo.

Arquitectura Hexagonal:
    - ports/in/   → Puertos de entrada (UI/API invoca al nucleo)
    - ports/out/  → Puertos de salida (nucleo necesita infraestructura)
"""
