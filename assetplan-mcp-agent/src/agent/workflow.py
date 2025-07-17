from typing import Annotated, Sequence
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_mcp_adapters.client import MultiServerMCPClient
from typing_extensions import TypedDict
from src.config.settings import settings
from src.config.logging import logger


class State(TypedDict):
    """
    El estado del agente.
    - messages: El historial de conversación.
    - user_id: El ID del usuario, pasado al inicio.
    - thread_id: El ID de la sesión/hilo.
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    user_id: str | None = None
    thread_id: str | None = None

class WorkflowBuilder:
    """ 
    Construye el flujo de trabajo del agente para el sistema MCP.
    Esta clase es responsable de crear el flujo de trabajo que manejará
    la conversación entre el usuario y los agentes.
    Inicializa los agentes, define sus prompts y configura la lógica de enrutamiento.
    """

    def __init__(self, memory_saver):
        self.memory_saver = memory_saver
        self.mcp_client = MultiServerMCPClient(settings.MCP_CLIENT_SERVERS)

    def _initialize_llm(self, provider: str, model_name: str, temperature: float, max_tokens: int | None = None) -> BaseChatModel:
        
        if provider == "google":
            return ChatGoogleGenerativeAI(
                model=model_name,
                temperature=temperature,
                max_output_tokens=max_tokens,
                google_api_key=settings.GOOGLE_API_KEY,
            )
        elif provider == "openai":
            return ChatOpenAI(
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                openai_api_key=settings.OPENAI_API_KEY
            )
        else:
            raise ValueError(f"Proveedor de LLM no soportado: {provider}")

    def _create_agent_runnable(self, llm: BaseChatModel, tools: list[BaseTool], system_prompt: str):
        """Crea un ejecutable para un agente, que es la cadena de prompt y LLM."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ])
        if tools:
            return prompt | llm.bind_tools(tools)
        return prompt | llm
    
    async def build_agent_workflow(self):
        logger.info("Iniciando la construcción del workflow del agente...")

        agent_llm = self._initialize_llm(
            provider=settings.AGENT_PROVIDER,
            model_name=settings.AGENT_MODEL,
            temperature=settings.AGENT_TEMPERATURE,
            max_tokens=settings.AGENT_MAX_TOKENS
        )

        tools = await self.mcp_client.get_tools(server_name="assetplan_mcp_server")

        logger.info(f"Herramientas disponibles: {[tool.name for tool in tools]}")

        agent_prompt = (
            "**Rol y Personalidad:**\n"
            "Eres un asesor inmobiliario experto de AssetPlan. Eres amigable, proactivo y tu principal objetivo es ayudar a los usuarios a encontrar el departamento de sus sueños. Tu tono debe ser siempre profesional, pero cercano y servicial.\n\n"
            
            "**Flujo de Conversación y Lógica:**\n"
            "1. **Inicio de la Conversación:** Preséntate cordialmente y pregunta al usuario qué tipo de departamento está buscando. No esperes a que te den toda la información; si es necesario, haz preguntas para entender sus necesidades (ej: '¿En qué comuna te gustaría vivir?', '¿Cuántos dormitorios necesitas?', '¿Tienes algún presupuesto en mente?').\n\n"
            "2. **Uso de Herramientas:** Una vez que tengas suficientes detalles, utiliza la herramienta `chroma_query_documents` para buscar propiedades. Formula la consulta para la herramienta basándote en las preferencias clave del usuario.\n\n"
            "3. **Presentación de Resultados:**\n"
            "   - **Si encuentras propiedades:** Sintetiza la información de la herramienta en un formato claro y fácil de leer. Presenta las opciones como una lista. Para cada propiedad, destaca sus características más importantes (ej: ubicación, precio, número de dormitorios y baños). No muestres simplemente la salida JSON de la herramienta.\n"
            "   - **Si NO encuentras propiedades:** No te limites a decir 'no encontré nada'. Informa amablemente al usuario que no hay propiedades que coincidan con sus criterios exactos y sugiérele ampliar la búsqueda (ej: 'No encontré departamentos con esas características exactas. ¿Te gustaría que buscáramos en otras comunas o con un rango de precios diferente?').\n\n"
            "4. **Conversación General:** Si el usuario te saluda, te hace preguntas sobre ti o la conversación no está relacionada con la búsqueda de propiedades, responde de manera natural y amigable sin usar las herramientas.\n\n"
        )

        agent_runnable = self._create_agent_runnable(agent_llm, tools, agent_prompt)

        async def agent_node(state: State):
            result = await agent_runnable.ainvoke(state)
            return {"messages": [result]}

        tool_node = ToolNode(tools)

        # Crear el flujo de trabajo del agente
        workflow = StateGraph(State)

        # Añadir nodos al workflow
        workflow.add_node("Agent", agent_node)
        workflow.add_node("tools", tool_node)

        # Definir las transiciones del workflow
        workflow.add_edge(START, "Agent")
        workflow.add_conditional_edges(
            "Agent",
            tools_condition,
            {"tools": "tools", END: END},
        )
        workflow.add_edge("tools", "Agent")

        # Compilar el workflow con el checkpointer
        graph = workflow.compile(checkpointer=self.memory_saver)
        
        logger.info("Agente inicializado correctamente.")

        return graph