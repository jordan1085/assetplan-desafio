# AssetPlan Scraper

Este proyecto contiene un scraper de Python para extraer datos de propiedades del sitio web de AssetPlan. Utiliza Selenium para la navegación y extracción de datos, y guarda los resultados en un archivo JSON.

## Requisitos Previos

Asegúrate de tener los siguientes programas instalados en tu sistema:

- **Python 3.8+**
- **make**: para ejecutar los comandos del Makefile.
- **uv**: para la gestión de entornos virtuales y paquetes de Python. Si no lo tienes, puedes instalarlo con `pip install uv`.

## Configuración del Proyecto

Para configurar el entorno de desarrollo, clona el repositorio y ejecuta el siguiente comando en la raíz del directorio `assetplan-scraper`:

```bash
make setup
```

Este comando creará un entorno virtual en `.venv` e instalará todas las dependencias necesarias desde `requirements.txt`.

## Cómo Ejecutar el Scraper

Una vez que el entorno esté configurado, puedes iniciar el proceso de scraping con el siguiente comando:

```bash
make scrape
```

El script te pedirá que ingreses el valor actual de la UF. Después de ingresarlo, el scraper comenzará a extraer los datos y los guardará en un archivo llamado `propiedades_assetplan.json`.

## Ejecución de Pruebas

El proyecto incluye pruebas automatizadas para verificar que el scraper funcione correctamente. Para ejecutar las pruebas, primero asegúrate de haber configurado el entorno con `make setup`. Luego, ejecuta el siguiente comando:

```bash
make test
```

Este comando descubrirá y ejecutará automáticamente las pruebas definidas en el directorio `test/`. La prueba automatizada verificará la configuración del entorno y la ejecución del scraper, simulando la entrada del valor de la UF.
