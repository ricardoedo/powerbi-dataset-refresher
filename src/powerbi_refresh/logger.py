"""
Logging module for Power BI Refresh Script.

This module provides structured logging functionality with support for
console and file output, configurable log levels, and formatted messages.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


class ScriptLogger:
    """Logger configurado para el script de Power BI."""

    @staticmethod
    def setup(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
        """
        Configura el logger con handlers para consola y archivo.

        Args:
            log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR)
            log_file: Ruta opcional al archivo de log

        Returns:
            Logger configurado

        Raises:
            ValueError: Si el nivel de logging es inválido
        """
        # Validar nivel de logging
        numeric_level = getattr(logging, log_level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f"Nivel de logging inválido: {log_level}")

        # Crear logger
        logger = logging.getLogger("powerbi_refresh")
        logger.setLevel(numeric_level)

        # Limpiar handlers existentes para evitar duplicados
        logger.handlers.clear()

        # Formato de logs con timestamp, nivel y mensaje
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")

        # Handler para consola
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Handler para archivo (si se especifica)
        if log_file:
            # Crear directorio si no existe
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        # Evitar propagación a logger raíz
        logger.propagate = False

        return logger
