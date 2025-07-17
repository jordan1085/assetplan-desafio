import logging
import sys
from src.core.config import settings

def setup_logging():
    """Configura el sistema de logging global"""
    
    # Configurar el logger root
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Limpiar handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Crear formatter
    formatter = logging.Formatter(settings.LOG_FORMAT)
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    console_handler.setFormatter(formatter)
    
    # Añadir handler al logger root
    root_logger.addHandler(console_handler)
    
    # Silenciar los logs de DEBUG de pymongo
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)

# Logger global
logger = setup_logging()