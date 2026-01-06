tools = [
    {
        "type": "function",
        "name": "funcion_llamada_db2",
        "description": "Consulta la base de datos DB2 para obtener información sobre incidentes, alertas, tickets, estados de servicios o cualquier dato del NOC/SOC. Usa esta función cuando necesites buscar información específica del sistema.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "La consulta o búsqueda a realizar en la base de datos"
                }
            },
            "required": ["query"]
        }
    }
]


def funcion_llamada_db2(query: str) -> str:
    return "This is a test response"


available_functions = {
    "funcion_llamada_db2": funcion_llamada_db2
}