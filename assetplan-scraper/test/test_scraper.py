import subprocess
import os
import pytest

@pytest.fixture(scope="module")
def setup_environment():
    """
    Configura el entorno ejecutando 'make setup'.
    Se ejecuta una vez por módulo de test.
    """
    print("Configurando el entorno con 'make setup'...")
    try:
        # Ejecutar make setup
        setup_process = subprocess.run(
            ["make", "setup"],
            capture_output=True,
            text=True,
            check=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        print(setup_process.stdout)
        print(setup_process.stderr)
        print("✓ Entorno configurado exitosamente.")
        yield
    except subprocess.CalledProcessError as e:
        print("Error durante 'make setup':")
        print(e.stdout)
        print(e.stderr)
        pytest.fail("La configuración del entorno falló, no se pueden continuar las pruebas.")
    except FileNotFoundError:
        pytest.fail("El comando 'make' no fue encontrado. Asegúrate de que make esté instalado y en el PATH.")

def test_scrape_process(setup_environment):
    """
    Prueba el proceso de scraping ejecutando 'make scrape'.
    """
    print(f"Ejecutando 'make scrape'...")
    try:
        # Ejecutar el scraper
        scrape_process = subprocess.run(
            ["make", "scrape"],
            capture_output=True,
            text=True,
            check=True,
            timeout=300,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        # Imprimir la salida para depuración
        print("Salida del scraper:")
        print(scrape_process.stdout)
        
        if scrape_process.stderr:
            print("Errores del scraper:")
            print(scrape_process.stderr)

        # Verificar que el proceso de scraping fue exitoso
        assert "Proceso completado" in scrape_process.stdout
        assert "Datos guardados exitosamente" in scrape_process.stdout
        
        # Verificar que el archivo JSON fue creado
        json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "propiedades_assetplan.json")
        assert os.path.exists(json_path), f"El archivo JSON no fue encontrado en {json_path}"
        
        print("✓ El proceso de scraping se completó y el archivo JSON fue creado.")

    except subprocess.CalledProcessError as e:
        print("Error durante la ejecución de 'make scrape':")
        print(e.stdout)
        print(e.stderr)
        pytest.fail(f"El scraping falló con el código de salida {e.returncode}.")
    except subprocess.TimeoutExpired:
        pytest.fail("El proceso de scraping excedió el tiempo límite.")
    except Exception as e:
        pytest.fail(f"Ocurrió un error inesperado durante la prueba: {e}")

