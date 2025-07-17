import os
import json
import yaml
import re
from typing import List, Dict, Any, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator
from pathlib import Path


class Settings(BaseSettings):
    ASSETPLAN_API_URL: str = "http://assetplan-api:8010"

    POSTGRES_URL: Optional[str] = None

    AGENT_PROVIDER: str = "google"
    AGENT_MODEL: str = "gemini-2.5-flash"
    AGENT_TEMPERATURE: float = 0
    AGENT_MAX_TOKENS: int = 4096

    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8080
    API_TITLE: str = "AssetPlan MCP Agent API"
    
    # --- CORS ---
    CORS_ORIGINS: List[str] = ["*"]
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]
    
    # --- LANGSMITH ---
    LANGSMITH_TRACING: bool = True
    LANGCHAIN_PROJECT: str = "assetplan-agent-scraper"

    # --- Servidores MCP ---
    MCP_CLIENT_SERVERS: Dict[str, Any] = {}
    
    LOG_LEVEL: str = "info"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # --- Carga de Configuración YAML ---
    _yaml_config: Optional[Dict] = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_yaml_config()
        self._apply_yaml_config()
        
    def _load_yaml_config(self):
        """Carga configuración desde agent.config.yaml con interpolación de variables de entorno."""
        yaml_path = Path(__file__).parent.parent.parent / "agent.config.yaml"
        if yaml_path.exists():
            try:
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    yaml_content = f.read()
                processed_content = self._interpolate_env_vars(yaml_content)
                self._yaml_config = yaml.safe_load(processed_content)
            except Exception as e:
                print(f"Error cargando configuración YAML: {e}")
                self._yaml_config = {}
        else:
            print("No se encontró agent.config.yaml, usando configuración por defecto y variables de entorno.")
            self._yaml_config = {}
    
    def _interpolate_env_vars(self, content: str) -> str:
        """Interpola variables de entorno en el contenido YAML. Soporta ${VAR} y ${VAR:-default}."""
        def replace_var(match):
            var_expr = match.group(1)
            if ':-' in var_expr:
                var_name, default_value = var_expr.split(':-', 1)
                return os.environ.get(var_name.strip(), default_value.strip().strip('"').strip("'"))
            else:
                var_name = var_expr.strip()
                return os.environ.get(var_name, match.group(0))
        return re.sub(r'\$\{([^}]+)\}', replace_var, content)
    
    def _apply_yaml_config(self):
        """Aplica la configuración del YAML, respetando los valores ya establecidos por variables de entorno."""
        if not self._yaml_config:
            return

        # Helper para aplicar configuración
        def apply_config(yaml_key_path: str, model_field: str):
            keys = yaml_key_path.split('.')
            value = self._yaml_config
            try:
                for key in keys:
                    value = value[key]
                if model_field not in self.model_fields_set:
                    setattr(self, model_field, value)
            except (KeyError, TypeError):
                pass # La clave no existe en el YAML, no hacemos nada

        # Aplicar configuraciones
        apply_config("agent.provider", "AGENT_PROVIDER")
        apply_config("agent.model", "AGENT_MODEL")
        apply_config("agent.temperature", "AGENT_TEMPERATURE")
        apply_config("agent.max_tokens", "AGENT_MAX_TOKENS")
        
        apply_config("langsmith.tracing", "LANGSMITH_TRACING")
        apply_config("langsmith.langchain_project", "LANGCHAIN_PROJECT")

        apply_config("mcp_servers", "MCP_CLIENT_SERVERS")
        
    @field_validator('MCP_CLIENT_SERVERS', mode='before')
    @classmethod
    def parse_mcp_servers(cls, v):
        if isinstance(v, str):
            try:
                result = json.loads(v)
                return result if isinstance(result, dict) else {}
            except json.JSONDecodeError as e:
                print(f"Error parseando MCP_CLIENT_SERVERS: {e}")
                return {}
        return v or {}
    
    class Config:
        env_file = ".env"

settings = Settings()