import chromadb
import uvicorn
import ssl
import os
import argparse
import json

from typing import Dict, List
from chromadb.config import Settings
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from chromadb.utils.embedding_functions import (
    DefaultEmbeddingFunction,
    OpenAIEmbeddingFunction,
    CohereEmbeddingFunction
)
from chromadb.api import EmbeddingFunction

# Initialize FastMCP server
mcp = FastMCP(name="assetplan-mcp-server", json_response=False, stateless_http=False)
app = mcp.streamable_http_app

# Global variables
_chroma_client = None
collection_name = os.getenv('CHROMA_COLLECTION_NAME', 'properties')

def create_parser():
    """Create and return the argument parser."""
    parser = argparse.ArgumentParser(description='FastMCP server for Chroma DB')

    parser.add_argument('--apphost', 
                        type=str, 
                        default=os.getenv('MCP_CHROMA_HOST', '0.0.0.0'),
                        help='Host for the FastMCP server')
    parser.add_argument('--appport',
                        type=int, 
                        default=int(os.getenv('MCP_CHROMA_PORT', 8020)),
                        help='Port for the FastMCP server')
    parser.add_argument('--client-type', 
                       choices=['http', 'cloud'],
                       default=os.getenv('CHROMA_CLIENT_TYPE', 'http'),
                       help='Type of Chroma client to use')
    parser.add_argument('--data-dir',
                       default=os.getenv('CHROMA_DATA_DIR'),
                       help='Directory for persistent client data (only used with persistent client)')
    parser.add_argument('--host', 
                       help='Chroma host (required for http client)', 
                       default=os.getenv('CHROMA_HOST'))
    parser.add_argument('--port', 
                       help='Chroma port (optional for http client)', 
                       default=os.getenv('CHROMA_PORT'))
    parser.add_argument('--custom-auth-credentials',
                       help='Custom auth credentials (optional for http client)', 
                       default=os.getenv('CHROMA_CUSTOM_AUTH_CREDENTIALS'))
    parser.add_argument('--tenant', 
                       help='Chroma tenant (optional for http client)', 
                       default=os.getenv('CHROMA_TENANT'))
    parser.add_argument('--database', 
                       help='Chroma database (required if tenant is provided)', 
                       default=os.getenv('CHROMA_DATABASE'))
    parser.add_argument('--api-key', 
                       help='Chroma API key (required if tenant is provided)', 
                       default=os.getenv('CHROMA_API_KEY'))
    parser.add_argument('--ssl', 
                       help='Use SSL (optional for http client)', 
                       type=lambda x: x.lower() in ['true', 'yes', '1', 't', 'y'],
                       default=os.getenv('CHROMA_SSL', 'true').lower() in ['true', 'yes', '1', 't', 'y'])
    parser.add_argument('--dotenv-path', 
                       help='Path to .env file', 
                       default=os.getenv('CHROMA_DOTENV_PATH', '.chroma_env'))
    return parser

def get_chroma_client(args=None):
    """Get or create the global Chroma client instance."""
    global _chroma_client
    if _chroma_client is None:
        parser = create_parser()
        # Analiza los argumentos conocidos para ignorar los argumentos de uvicorn y obtener la ruta de dotenv.
        temp_args, _ = parser.parse_known_args()
        
        # Carga las variables de entorno desde el fichero .env.
        load_dotenv(dotenv_path=temp_args.dotenv_path)

        # Vuelve a analizar los argumentos ahora que .env está cargado para aplicar las variables de entorno.
        args, _ = parser.parse_known_args()


        if args.client_type == 'http':
            if not args.host:
                raise ValueError("Host must be provided via --host flag or CHROMA_HOST environment variable when using HTTP client")
            
            settings = Settings()
            if args.custom_auth_credentials:
                settings = Settings(
                    chroma_client_auth_provider="chromadb.auth.basic_authn.BasicAuthClientProvider",
                    chroma_client_auth_credentials=args.custom_auth_credentials
                )
            
            # Handle SSL configuration
            try:
                _chroma_client = chromadb.HttpClient(
                    host=args.host,
                    port=args.port if args.port else None,
                    ssl=args.ssl,
                    settings=settings
                )
            except ssl.SSLError as e:
                print(f"SSL connection failed: {str(e)}")
                raise
            except Exception as e:
                print(f"Error connecting to HTTP client: {str(e)}")
                raise
        elif args.client_type == 'cloud':
            if not all([args.tenant, args.database, args.api_key]):
                raise ValueError("Tenant, database, and API key must be provided for cloud client.")
            
            try:
                _chroma_client = chromadb.HttpClient(
                    host="api.trychroma.com",
                    ssl=True,
                    tenant=args.tenant,
                    database=args.database,
                    headers={'x-chroma-token': args.api_key}
                )
            except Exception as e:
                print(f"Error connecting to Chroma Cloud client: {str(e)}")
                raise

    return _chroma_client

def get_embedding_function(name: str) -> EmbeddingFunction:
    """Returns an embedding function instance based on its name."""
    if name == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        model_name = os.getenv("OPENAI_EMBEDDINGS_MODEL", "text-embedding-3-small")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        return OpenAIEmbeddingFunction(api_key=api_key, model_name=model_name)
    elif name == "cohere":
        api_key = os.getenv("COHERE_API_KEY")
        if not api_key:
            raise ValueError("COHERE_API_KEY environment variable not set.")
        return CohereEmbeddingFunction(api_key=api_key)
    elif name == "default":
        return DefaultEmbeddingFunction()
    else:
        raise ValueError(f"Unknown embedding function: '{name}'. Supported: openai, cohere, default.")


@mcp.tool()
def chroma_query_documents(
    query_texts: List[str]
) -> Dict:
    """
    Query documents from the Chroma collection.

    Args:   
        query_texts (List[str]): List of query texts to search for.
    """    
    if not query_texts:
        raise ValueError("The 'query_texts' list cannot be empty.")

    client = get_chroma_client()
    try:
        embedding_function = get_embedding_function("openai")

        collection = client.get_collection(
            name=collection_name,
            embedding_function=embedding_function
        )
        
        return collection.query(
            query_texts=query_texts,
            include=["documents", "metadatas", "distances"]
        )
    except Exception as e:
        raise Exception(f"Failed to query documents from collection '{collection_name}': {str(e)}") from e

def validate_thought_data(input_data: Dict) -> Dict:
    """Validate thought data structure."""
    if not input_data.get("sessionId"):
        raise ValueError("Invalid sessionId: must be provided")
    if not input_data.get("thought") or not isinstance(input_data.get("thought"), str):
        raise ValueError("Invalid thought: must be a string")
    if not input_data.get("thoughtNumber") or not isinstance(input_data.get("thoughtNumber"), int):
            raise ValueError("Invalid thoughtNumber: must be a number")
    if not input_data.get("totalThoughts") or not isinstance(input_data.get("totalThoughts"), int):
        raise ValueError("Invalid totalThoughts: must be a number")
    if not isinstance(input_data.get("nextThoughtNeeded"), bool):
        raise ValueError("Invalid nextThoughtNeeded: must be a boolean")
        
    return {
        "sessionId": input_data.get("sessionId"),
        "thought": input_data.get("thought"),
        "thoughtNumber": input_data.get("thoughtNumber"),
        "totalThoughts": input_data.get("totalThoughts"),
        "nextThoughtNeeded": input_data.get("nextThoughtNeeded"),
        "isRevision": input_data.get("isRevision"),
        "revisesThought": input_data.get("revisesThought"),
        "branchFromThought": input_data.get("branchFromThought"),
        "branchId": input_data.get("branchId"),
        "needsMoreThoughts": input_data.get("needsMoreThoughts"),
    }
    
def process_thought(input_data: Dict) -> Dict:
    """Process a new thought."""
    try:
        # Validate input data
        validated_input = validate_thought_data(input_data)
            
        # Adjust total thoughts if needed
        if validated_input["thoughtNumber"] > validated_input["totalThoughts"]:
            validated_input["totalThoughts"] = validated_input["thoughtNumber"]
            
        # Return response
        return {
            "sessionId": validated_input["sessionId"],
            "thoughtNumber": validated_input["thoughtNumber"],
            "totalThoughts": validated_input["totalThoughts"],
            "nextThoughtNeeded": validated_input["nextThoughtNeeded"],
            }
            
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed"
        }

def main():
    """Entry point for the Chroma MCP server."""
    parser = create_parser()
    args = parser.parse_args()
    
    if args.dotenv_path:
        load_dotenv(dotenv_path=args.dotenv_path)
        # re-parse args to read the updated environment variables
        parser = create_parser()
        args = parser.parse_args()
    
    # Validate required arguments based on client type
    if args.client_type == 'http':
        if not args.host:
            parser.error("Host must be provided via --host flag or CHROMA_HOST environment variable when using HTTP client")
    
    elif args.client_type == 'cloud':
        if not args.tenant:
            parser.error("Tenant must be provided via --tenant flag or CHROMA_TENANT environment variable when using cloud client")
        if not args.database:
            parser.error("Database must be provided via --database flag or CHROMA_DATABASE environment variable when using cloud client")
        if not args.api_key:
            parser.error("API key must be provided via --api-key flag or CHROMA_API_KEY environment variable when using cloud client")
    
    # Initialize client with parsed args
    try:
        get_chroma_client(args)
        print("Successfully initialized Chroma client")
    except Exception as e:
        print(f"Failed to initialize Chroma client: {str(e)}")
        raise
    
    # Initialize and run the server
    print("Starting MCP server")
    uvicorn.run(mcp.streamable_http_app, host=args.apphost, port=args.appport, log_level="debug")
    
if __name__ == "__main__":
    main()
