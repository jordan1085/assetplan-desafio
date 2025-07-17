import logging
import sys

def setup_logging():
    """Configura el sistema de logging global"""
    
    # Valores por defecto
    log_level = "INFO"
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Intentar importar settings si está disponible
    try:
        from src.config.settings import settings
        log_level = settings.LOG_LEVEL.upper()
        log_format = settings.LOG_FORMAT
    except ImportError:
        # Si no podemos importar settings, usar valores por defecto
        pass
    
    # Configurar el logger root
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    
    # Limpiar handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Crear formatter
    formatter = logging.Formatter(log_format)
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    console_handler.setFormatter(formatter)
    
    # Añadir handler al logger root
    root_logger.addHandler(console_handler)
    
    return logging.getLogger(__name__)

# Logger global
logger = setup_logging()
