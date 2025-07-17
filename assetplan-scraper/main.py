from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
import time
import json
import re
import traceback
import httpx

class Scraper:
    def __init__(self):
        """
        Inicializa el scraper de AssetPlan en modo headless.
        """
        self.setup_driver()
        self.properties = []
        
    def setup_driver(self):
        """Configura el driver de Chrome para ejecución headless."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 15)
        
    def extract_property_info(self, property_element):
        """
        Extrae información de una propiedad específica
        
        Args:
            property_element: Elemento web de la propiedad
            
        Returns:
            dict: Información de la propiedad
        """
        property_info = {}
        
        try:
            # Extraer todo el texto del elemento
            full_text = property_element.text
            print(f"Texto completo del elemento: {full_text}")
            
            # Dividir el texto en líneas para procesamiento
            lines = [line.strip() for line in full_text.split('\n') if line.strip()]
            
            # Inicializar con valores por defecto
            property_info['titulo'] = "No disponible"
            property_info['link'] = "No disponible"
            
            # Buscar el enlace primero
            try:
                link_elements = property_element.find_elements(By.TAG_NAME, "a")
                for link in link_elements:
                    href = link.get_attribute('href')
                    if href and '/arriendo/departamento/' in href and 'mapa' not in href:
                        property_info['link'] = href
                        break
            except:
                pass
            
            # Buscar el título del edificio
            for line in lines:
                if 'Edificio' in line and line.strip() != 'Edificio' and line.strip() != 'Servicio Pro':
                    # Extraer solo el nombre después de "Edificio"
                    if line.strip().startswith('Edificio '):
                        property_info['titulo'] = line.strip()[9:]  # Remover "Edificio "
                    else:
                        property_info['titulo'] = line.strip()
                    break
        
        except Exception as e:
            print(f"Error extrayendo título: {e}")
            property_info['titulo'] = "No disponible"
            property_info['link'] = "No disponible"
                
        try:
            # Dirección - buscar líneas que contengan direcciones
            lines = [line.strip() for line in property_element.text.split('\n') if line.strip()]
            for line in lines:
                # Buscar patrones de dirección (número + texto + comuna)
                if re.search(r'\d+.*,.*', line) and 'Edificio' not in line and '$' not in line:
                    property_info['direccion'] = line.strip()
                    break
            else:
                property_info['direccion'] = "No disponible"
                
        except Exception as e:
            print(f"Error extrayendo dirección: {e}")
            property_info['direccion'] = "No disponible"
            
        try:
            # Precio - buscar líneas que contengan $
            lines = [line.strip() for line in property_element.text.split('\n') if line.strip()]
            for line in lines:
                if '$' in line and ('desde' in line.lower() or 'hasta' in line.lower() or '-' in line):
                    property_info['precio'] = line.strip()
                    break
            else:
                property_info['precio'] = "No disponible"
                
        except Exception as e:
            print(f"Error extrayendo precio: {e}")
            property_info['precio'] = "No disponible"
            
        try:
            # Servicios - buscar líneas específicas
            lines = [line.strip() for line in property_element.text.split('\n') if line.strip()]
            servicios = []
            service_keywords = ['descuento', 'garantía', 'aval', 'cuotas', 'sin aval', 'servicio']
            
            for line in lines:
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in service_keywords):
                    servicios.append(line.strip())
                    
            property_info['servicios'] = servicios
            
        except Exception as e:
            print(f"Error extrayendo servicios: {e}")
            property_info['servicios'] = []
            
        # Características adicionales
        try:
            lines = [line.strip() for line in property_element.text.split('\n') if line.strip()]
            caracteristicas = []
            for line in lines:
                if any(word in line.lower() for word in ['dormitorio', 'baño', 'm²', 'estacionamiento', 'estudio', 'disponible']):
                    caracteristicas.append(line.strip())
            property_info['caracteristicas'] = caracteristicas
        except Exception as e:
            print(f"Error extrayendo características: {e}")
            property_info['caracteristicas'] = []
            
        # Extraer URLs de las imágenes
        try:
            image_elements = property_element.find_elements(By.TAG_NAME, "img")
            image_urls = [img.get_attribute('src') for img in image_elements if img.get_attribute('src')]
            property_info['imagenes'] = image_urls
        except Exception as e:
            print(f"Error extrayendo imágenes: {e}")
            property_info['imagenes'] = []
            
        # Debug: mostrar lo que se extrajo
        print(f"Título extraído: {property_info['titulo']}")
        print(f"Dirección extraída: {property_info['direccion']}")
        print(f"Precio extraído: {property_info['precio']}")
        
        return property_info
        
    def scrape_page(self, url):
        """
        Extrae información de una página específica
        
        Args:
            url (str): URL de la página a scrapear
            
        Returns:
            list: Lista de propiedades encontradas
        """
        print(f"Scrapeando: {url}")
        self.driver.get(url)
        
        try:
            # Esperar a que se cargue la página
            time.sleep(5)
            
            # Scroll para cargar contenido dinámico
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            exact_selector = "article.building-card" 
            
            property_elements = []
            try:
                print(f"Buscando elementos con el selector exacto: '{exact_selector}'")
                elements = self.driver.find_elements(By.CSS_SELECTOR, exact_selector)
                if elements:
                    print(f"Encontrados {len(elements)} elementos con el selector: '{exact_selector}'")
                    property_elements = elements
            except Exception as e:
                print(f"El selector '{exact_selector}' falló o no encontró elementos: {e}")
            
            page_properties = []

            for i, element in enumerate(property_elements):
                try:
                    print(f"\nProcesando elemento {i+1}:")
                    property_info = self.extract_property_info(element)
                    if property_info['titulo'] != "No disponible":
                        page_properties.append(property_info)
                        print(f"✓ Propiedad agregada: {property_info['titulo']}")
                    else:
                        print("✗ Elemento sin información válida")
                except Exception as e:
                    print(f"✗ Error procesando elemento {i+1}: {e}")
                    continue
                    
            return page_properties
            
        except Exception as e:
            print(f"Error general en scrape_page: {e}")
            return []
            
    def scrape_multiple_pages(self, base_url, target_properties=50):
        """
        Scrapea múltiples páginas hasta obtener el número objetivo de propiedades
        
        Args:
            base_url (str): URL base sin el parámetro de página
            target_properties (int): Número objetivo de propiedades a obtener
        """
        all_properties = []
        page = 1
        max_pages = 10  # Límite máximo de páginas para evitar bucles infinitos
        
        while len(all_properties) < target_properties and page <= max_pages:
            url = f"{base_url}?page={page}"
            page_properties = self.scrape_page(url)
            
            remaining_needed = target_properties - len(all_properties)
            properties_to_add = page_properties[:remaining_needed]
            all_properties.extend(properties_to_add)
            
            print(f"Página {page}: {len(page_properties)} propiedades encontradas")
            print(f"Total acumulado: {len(all_properties)}/{target_properties}")
            
            if len(all_properties) >= target_properties:
                print(f"✓ Objetivo alcanzado: {len(all_properties)} propiedades obtenidas")
                break
            
            page += 1
            # Pausa entre páginas
            time.sleep(3)
            
        self.properties = all_properties
        return all_properties
        
    def save_to_json(self, uf_value, filename="propiedades_assetplan.json"):
        """Guarda los datos en formato JSON bien estructurado, incluyendo precios en UF"""
        if not self.properties:
            print("No hay propiedades para guardar")
            return None, None
            
        # Crear estructura JSON bien organizada
        json_data = {
            "propiedades": []
        }
        
        # Procesar cada propiedad
        for i, prop in enumerate(self.properties):
            # Extraer información adicional del precio
            precio_desde = None
            precio_hasta = None
            if prop['precio'] != "No disponible" and "$" in prop['precio']:
                # Extraer números del precio
                precios = re.findall(r'\$([0-9,.]+)', prop['precio'])
                
                def clean_price(p_str):
                    # Eliminar puntos (separador de miles) y reemplazar coma por punto (decimal)
                    return p_str.replace('.', '').replace(',', '.')

                if len(precios) >= 2:
                    precio_desde = clean_price(precios[0])
                    precio_hasta = clean_price(precios[1])
                elif len(precios) == 1:
                    precio_desde = clean_price(precios[0])
            
            # Calcular precios en UF
            precio_desde_uf = None
            precio_hasta_uf = None
            if uf_value > 0:
                if precio_desde:
                    precio_desde_uf = int(round(float(precio_desde) / uf_value))
                if precio_hasta:
                    precio_hasta_uf = int(round(float(precio_hasta) / uf_value))

            # Extraer comuna de la dirección
            comuna = "No disponible"
            if prop['direccion'] != "No disponible" and "," in prop['direccion']:
                parts = prop['direccion'].split(',')
                if len(parts) >= 2:
                    comuna = parts[-1].strip()
            
            # Extraer el ID desde el link de la propiedad
            prop_id = i + 1  # ID por defecto en caso de que el link falle
            if prop.get('link') and prop['link'] != "No disponible":
                try:
                    # Tomar la última parte de la URL que debería ser el ID
                    id_str = prop['link'].strip('/').split('/')[-1]
                    if id_str.isdigit():
                        prop_id = int(id_str)
                except (ValueError, IndexError):
                    print(f"No se pudo extraer el ID del link: {prop['link']}. Usando ID por defecto.")

            # Estructura de cada propiedad
            propiedad_estructurada = {
                "id": prop_id,
                "informacion_basica": {
                    "titulo": prop['titulo'],
                    "direccion_completa": prop['direccion'],
                    "comuna": comuna,
                    "link_propiedad": prop['link']
                },
                "precio": {
                    "precio_desde": precio_desde,
                    "precio_hasta": precio_hasta,
                    "moneda": "CLP",
                    "precio_desde_uf": precio_desde_uf,
                    "precio_hasta_uf": precio_hasta_uf
                },
                "servicios_disponibles": prop['servicios'],
                "caracteristicas": prop['caracteristicas'],
                "imagenes": prop.get('imagenes', []),
                "servicios_especiales": {
                    "tiene_descuento": any('descuento' in s.lower() for s in prop['servicios']),
                    "garantia_cuotas": any('garantía' in s.lower() or 'cuotas' in s.lower() for s in prop['servicios']),
                    "sin_aval": any('sin aval' in s.lower() for s in prop['servicios']),
                    "servicio_pro": any('servicio pro' in s.lower() for s in prop['servicios'])
                }
            }
            
            json_data["propiedades"].append(propiedad_estructurada)
        
        # Guardar en directorio actual
        import os
        current_dir = os.getcwd()
        filepath = os.path.join(current_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            print(f"Datos guardados exitosamente en: {filepath}")
        except Exception as e:
            print(f"Error al guardar JSON: {e}")
            
        return filepath, json_data
        
    def close(self):
        self.driver.quit()

def main():
    """Función principal para testing"""

    # Configuración
    BASE_URL = "https://www.assetplan.cl/arriendo/departamento"
    TARGET_PROPERTIES = 50  # Objetivo: obtener 50 propiedades
    UF_VALUE = 39

    scraper = Scraper()
    
    try:
        print("Iniciando scraping de AssetPlan...")
        print(f"Objetivo: obtener {TARGET_PROPERTIES} propiedades")
        
        # Scrapear propiedades
        properties = scraper.scrape_multiple_pages(BASE_URL, TARGET_PROPERTIES)
        
        # Guardar datos si se encontraron
        if properties:
            print(f"\n=== GUARDANDO RESULTADOS ===")
            json_path, json_data = scraper.save_to_json(UF_VALUE)

            if json_data:
                try:
                    url = "http://localhost:8010/load-deptos"
                    
                    with httpx.Client(follow_redirects=True) as client:
                        response = client.post(url, json=json_data)
                    
                    if response.status_code == 200:
                        print(f"Datos enviados exitosamente a {url}")
                    else:
                        print(f"Error al enviar datos: {response.status_code}")
                        
                except httpx.RequestError as e:
                    print(f"Error de conexión al enviar datos: {e}")

            if json_path:
                print(f"\n=== RESUMEN FINAL ===")
                print(f"- Propiedades obtenidas: {len(properties)}")

        else:
            print("No se encontraron propiedades para guardar")
        
    except Exception as e:
        print(f"Error durante el scraping: {e}")
        traceback.print_exc()
        
    finally:
        scraper.close()
        print("\nProceso completado.")

if __name__ == "__main__":
    main()