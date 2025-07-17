import requests
import uuid

# URLs de los servicios basadas en la configuración de docker-compose
USER_API_URL = "http://localhost:8010/user"
CHAT_API_URL = "http://localhost:8080/chat/"

def run_chat_test():
    """
    Ejecuta un test que crea un usuario y luego interactúa con el servicio de chat.
    """
    try:
        # 1. Crear un usuario nuevo
        username = f"testuser_{str(uuid.uuid4())[:8]}"
        email = f"{username}@example.com"
        
        print(f"Creando usuario con email: {email}...")
        user_response = requests.post(USER_API_URL, data={"email": email, "username": username})
        user_response.raise_for_status() 
        
        user_data = user_response.json()
        user_id = user_data.get("user_id")
        
        if not user_id:
            print("Error: No se pudo obtener el ID del usuario.")
            return

        print(f"Usuario creado con éxito. ID: {user_id}")

        # 2. Iniciar una conversación de varios turnos con el agente
        messages = [
            "Hola me llamo Juan, estoy buscando recomendaciones de departamentos en Santiago.",
            "Quiero un departamente con 1 habitacion mas economico que tengas disponible.",
            "Gracias por tu ayuda!"
        ]
        
        thread_id = None

        for message in messages:
            print(f"\nEnviando mensaje al chat: '{message}'")
            
            payload = {
                "message": message,
                "user_id": user_id,
            }
            if thread_id:
                payload["thread_id"] = thread_id

            chat_response = requests.post(CHAT_API_URL, data=payload)
            chat_response.raise_for_status()
            
            chat_data = chat_response.json()
            
            # Extraer el thread_id de la primera respuesta para usarlo en las siguientes
            if not thread_id:
                thread_id = chat_data.get("thread_id")
                if thread_id:
                    print(f"Conversación iniciada con thread_id: {thread_id}")

            print("\n--- Respuesta del Agente ---")
            print(chat_data.get("response"))
            print("--------------------------")

    except requests.exceptions.RequestException as e:
        print(f"Error en la comunicación con los servicios: {e}")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

if __name__ == "__main__":
    run_chat_test()
