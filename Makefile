.PHONY: test_chat

test_chat:
	@echo "Instalando dependencias para el test..."
	python3 -m pip install -r test/requirements.txt
	@echo "Ejecutando el test de chat..."
	python3 test/test_chat.py
	@echo "Test de chat completado."
