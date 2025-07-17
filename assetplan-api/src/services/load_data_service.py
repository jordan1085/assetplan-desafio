import os
import json
from src.core.config import settings
from src.core.logging import logger
from src.database.mongo_config import get_collection
from src.database.chroma_config import get_chroma_collection

class LoadDataService:
    def __init__(self):
        # --- Conexión a MongoDB ---
        self.collection = get_collection()

        # --- Conexión a ChromaDB ---
        self.chroma_collection_name = settings.CHROMA_COLLECTION_NAME
        self.chroma_collection = get_chroma_collection(self.chroma_collection_name)

    def _generate_property_description(self, prop: dict) -> str:
        """Genera una descripción en lenguaje natural para una propiedad, incluyendo todos los detalles."""
        info = prop.get('informacion_basica', {})
        precio = prop.get('precio', {})
        servicios_especiales = prop.get('servicios_especiales', {})

        # --- Información Básica ---
        titulo = info.get('titulo', 'N/A')
        direccion = info.get('direccion_completa', 'N/A')
        comuna = info.get('comuna', 'N/A')

        # --- Precios ---
        precio_desde_uf = precio.get('precio_desde_uf', 'N/A')
        precio_hasta_uf = precio.get('precio_hasta_uf', 'N/A')
        moneda = precio.get('moneda', 'CLP')

        # --- Características y Servicios ---
        caracteristicas_str = ", ".join(prop.get('caracteristicas', []))
        servicios_str = ", ".join(prop.get('servicios_disponibles', []))

        # --- Construcción de la descripción ---
        description = (
            f"La propiedad '{titulo}', ubicada en {direccion}, comuna de {comuna}, "
            f"ofrece arriendos en {moneda} con precios que van desde los {precio_desde_uf} UF hasta los {precio_hasta_uf} UF. "
            f"Dispone de las siguientes tipologías: {caracteristicas_str}. "
        )

        if servicios_str:
            description += f"Entre sus servicios generales se incluyen: {servicios_str}. "

        # --- Servicios Especiales ---
        servicios_activos = [key for key, value in servicios_especiales.items() if value]
        if servicios_activos:
            servicios_especiales_str = ", ".join(servicios_activos).replace('_', ' ')
            description += f"Además, cuenta con beneficios especiales como: {servicios_especiales_str}. "


        return description.strip()

    async def sync_mongo_to_chroma(self):
        """
        Sincroniza todos los datos de MongoDB a ChromaDB.
        Primero, limpia la colección de Chroma para asegurar consistencia y
        luego carga los datos frescos desde MongoDB.
        """
        # 1. Limpiar la colección en ChromaDB antes de sincronizar
        try:
            existing_ids = self.chroma_collection.get(include=[])['ids']
            if existing_ids:
                logger.info(f"Limpiando {len(existing_ids)} documentos de la colección '{self.chroma_collection_name}'...")
                self.chroma_collection.delete(ids=existing_ids)
                logger.info("Colección de ChromaDB limpiada exitosamente.")
        except Exception as e:
            logger.error(f"No se pudo limpiar la colección de ChromaDB (puede que estuviera vacía): {e}")

        # 2. Cargar datos frescos desde MongoDB
        all_props = list(self.collection.find({}))
        
        if not all_props:
            logger.info("No hay propiedades en MongoDB para sincronizar con ChromaDB.")
            return {"status": "skipped", "message": "No properties to sync."}

        documents, metadatas, ids = [], [], []

        for prop in all_props:
            prop_id = str(prop.get("id"))
            if not prop_id:
                continue

            description = self._generate_property_description(prop)
            documents.append(description)
            
            # Chroma no acepta el '_id' de MongoDB en los metadatos.
            prop.pop('_id', None)
            # Los metadatos en Chroma deben ser str, int, float o bool.
            # Convertimos listas y dicts a JSON strings.
            for key, value in prop.items():
                if isinstance(value, (dict, list)):
                    prop[key] = json.dumps(value)
            
            metadatas.append(prop)
            ids.append(prop_id)

        logger.info(f"Sincronizando {len(documents)} propiedades a ChromaDB en la colección '{self.chroma_collection_name}'...")
        
        # Upsert en lotes para no sobrecargar la memoria o la red
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            self.chroma_collection.upsert(
                ids=ids[i:i+batch_size],
                documents=documents[i:i+batch_size],
                metadatas=metadatas[i:i+batch_size]
            )
        
        logger.info("Sincronización con ChromaDB completada.")
        return {"status": "success", "synced_count": len(documents)}

    async def compare_and_update_prices(self, deptos_data: dict) -> dict:
        """
        Compara los precios de las propiedades entrantes con las existentes en MongoDB
        y actualiza si hay diferencias. Se ejecuta solo si ya hay datos en la colección.

        :param deptos_data: Diccionario que contiene la lista de propiedades.
        :return: Resumen de la operación de actualización de precios.
        """
        if self.collection.count_documents({}) == 0:
            return {
                "status": "skipped",
                "message": "La colección está vacía, no se realizó ninguna comparación de precios."
            }

        if "propiedades" not in deptos_data or not isinstance(deptos_data["propiedades"], list):
            return {"status": "error", "message": "El formato de datos es incorrecto."}

        incoming_properties = deptos_data["propiedades"]
        updated_count = 0
        updated_ids = []

        for prop in incoming_properties:
            prop_id = prop.get("id")
            incoming_price = prop.get("precio")

            if not prop_id or not incoming_price:
                continue

            existing_prop = self.collection.find_one({"id": prop_id})

            if existing_prop:
                existing_price = existing_prop.get("precio", {})
                
                # Comprobar si los precios son diferentes
                if existing_price.get('precio_desde') != incoming_price.get('precio_desde') or \
                   existing_price.get('precio_hasta') != incoming_price.get('precio_hasta'):
                    
                    # Actualizar solo el campo de precio
                    update_result = self.collection.update_one(
                        {"id": prop_id},
                        {"$set": {"precio": incoming_price}}
                    )

                    if update_result.modified_count > 0:
                        updated_count += 1
                        updated_ids.append(prop_id)
        
        return {
            "status": "success",
            "updated_price_count": updated_count,
            "updated_ids": updated_ids
        }

    async def load_deptos(self, deptos_data: dict) -> dict:
        """
        Carga los datos de las propiedades en MongoDB. Primero, actualiza los precios de
        las propiedades existentes y luego inserta solo las propiedades nuevas.
        :param deptos_data: Diccionario que contiene la lista de propiedades.
        :return: Resumen de la operación.
        """
        if "propiedades" not in deptos_data or not isinstance(deptos_data["propiedades"], list):
            return {"status": "error", "message": "El formato de datos es incorrecto. Se esperaba una clave 'propiedades' con una lista."}

        # 1. Comparar y actualizar precios para propiedades existentes
        price_update_summary = await self.compare_and_update_prices(deptos_data)

        # 2. Insertar solo las propiedades nuevas
        properties = deptos_data["propiedades"]
        inserted_count = 0
        inserted_ids = []

        for prop in properties:
            prop_id = prop.get("id")
            if not prop_id:
                continue

            exists = self.collection.count_documents({"id": prop_id}) > 0
            if not exists:
                self.collection.insert_one(prop)
                inserted_count += 1
                inserted_ids.append(prop_id)
        
        # 3. Sincronizar todos los datos con ChromaDB
        chroma_sync_summary = await self.sync_mongo_to_chroma()

        return {
            "status": "success",
            "inserted_count": inserted_count,
            "inserted_ids": inserted_ids,
            "price_update_summary": price_update_summary,
            "chroma_sync_summary": chroma_sync_summary
        }
    
load_data_service = LoadDataService()