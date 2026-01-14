import json
from functions.db2_queries import (
    get_db2_tablespace_usage,
    get_db2_tablespace_summary,
    get_db2_connection_health,
    get_db2_database_size
)

# Definición de herramientas (tools) para OpenAI Realtime API
tools = [
    {
        "type": "function",
        "name": "get_db2_tablespace_usage",
        "description": "Obtiene información detallada del uso de tablespaces en DB2. Retorna datos completos sobre cada tablespace incluyendo tamaño, utilización, estado (CRITICAL, WARNING, ATTENTION, NORMAL) y recomendaciones específicas. Usa esta función cuando necesites un análisis exhaustivo de los tablespaces.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "type": "function",
        "name": "get_db2_tablespace_summary",
        "description": "Obtiene un resumen conciso del uso de tablespaces en DB2, solo mostrando aquellos que requieren atención (≥70% de uso). Ideal para consultas rápidas y respuestas por voz. Retorna solo los problemas críticos y advertencias con acciones inmediatas.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "type": "function",
        "name": "get_db2_connection_health",
        "description": "Verifica el estado de salud de la conexión a la base de datos DB2. Comprueba si la conexión está activa, el usuario conectado y el esquema actual. Usa esta función para diagnosticar problemas de conectividad.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "type": "function",
        "name": "get_db2_database_size",
        "description": "Obtiene información del tamaño total de la base de datos DB2, incluyendo tamaño total, espacio usado, espacio libre, utilización promedio y número total de tablespaces. Proporciona una vista general de la capacidad del sistema.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "type": "function",
        "name": "set_bot_muted",
        "description": "Controla si el bot debe hablar o quedarse en silencio durante la llamada. IMPORTANTE: SOLO usa esta función cuando escuches comandos que EMPIECEN con 'OPTI' seguido de 'silencio', 'haz silencio', 'habla', 'vuelve a hablar', o 'actívate'. Si alguien dice 'silencio' o 'habla' sin mencionar 'OPTI', NO llames esta función.",
        "parameters": {
            "type": "object",
            "properties": {
                "muted": {
                    "type": "boolean",
                    "description": "true para silenciar el bot cuando escuches 'OPTI HAZ SILENCIO' o 'OPTI SILENCIO'. false para reactivarlo cuando escuches 'OPTI VUELVE A HABLAR' o 'OPTI HABLA'."
                }
            },
            "required": ["muted"]
        }
    }
]


# Funciones wrapper que retornan strings JSON para OpenAI
def call_get_db2_tablespace_usage():
    """Wrapper para get_db2_tablespace_usage que retorna JSON string"""
    result = get_db2_tablespace_usage()
    return json.dumps(result, ensure_ascii=False, indent=2)


def call_get_db2_tablespace_summary():
    """Wrapper para get_db2_tablespace_summary que retorna JSON string"""
    result = get_db2_tablespace_summary()
    return json.dumps(result, ensure_ascii=False, indent=2)


def call_get_db2_connection_health():
    """Wrapper para get_db2_connection_health que retorna JSON string"""
    result = get_db2_connection_health()
    return json.dumps(result, ensure_ascii=False, indent=2)


def call_get_db2_database_size():
    """Wrapper para get_db2_database_size que retorna JSON string"""
    result = get_db2_database_size()
    return json.dumps(result, ensure_ascii=False, indent=2)


# Mapeo de nombres de funciones a las funciones reales
available_functions = {
    "get_db2_tablespace_usage": call_get_db2_tablespace_usage,
    "get_db2_tablespace_summary": call_get_db2_tablespace_summary,
    "get_db2_connection_health": call_get_db2_connection_health,
    "get_db2_database_size": call_get_db2_database_size
}


def execute_function(function_name: str, arguments: dict = None):
    """
    Ejecuta una función por su nombre con argumentos opcionales.

    Args:
        function_name: Nombre de la función a ejecutar
        arguments: Diccionario con argumentos (opcional, por ahora no usado)

    Returns:
        str: Resultado de la función en formato JSON string
    """
    if function_name not in available_functions:
        return json.dumps({
            "error": f"Función '{function_name}' no encontrada",
            "available_functions": list(available_functions.keys())
        })

    try:
        # Ejecutar la función
        result = available_functions[function_name]()
        return result
    except Exception as e:
        return json.dumps({
            "error": f"Error ejecutando función '{function_name}': {str(e)}",
            "function_name": function_name
        })
