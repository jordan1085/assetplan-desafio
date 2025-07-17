VENV_DIR := .venv

.PHONY: setup scrape clean test_scraper

setup:
	@echo "Creando entorno virtual con uv..."
	uv venv $(VENV_DIR)
	@echo "Instalando dependencias con uv en .venv..."
	uv pip install -r requirements.txt --python $(VENV_DIR)/bin/python
	@echo "Setup completado. Ejecuta 'make scrape' para iniciar."

scrape:
	@echo "Iniciando el scraping de Assetplan..."
	$(VENV_DIR)/bin/python main.py
	@echo "Proceso completado."

clean:
	@echo "Eliminando el entorno virtual..."
	rm -rf $(VENV_DIR)

test_scraper:
	@echo "Instalando/actualizando dependencias..."
	@uv venv $(VENV_DIR)
	@uv pip install -r requirements.txt --python $(VENV_DIR)/bin/python
	@echo "Ejecutando pruebas con pytest..."
	$(VENV_DIR)/bin/python -m pytest -s