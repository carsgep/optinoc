from datetime import datetime

import ibm_db
from db.db2 import get_db2_connection


def get_db2_connection_health():
    """
    Verifica el estado de salud de la conexión DB2
    """
    sql = """
    SELECT
        CURRENT TIMESTAMP as CURRENT_TIME,
        CURRENT USER as CONNECTED_USER,
        CURRENT SCHEMA as CURRENT_SCHEMA
    FROM SYSIBM.SYSDUMMY1
    """

    conn = get_db2_connection()
    if not conn:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "message": "Cannot establish connection to DB2",
            "connection_healthy": False,
            "summary": "DB2 CONNECTION FAILED: Unable to connect to database",
        }

    try:
        stmt = ibm_db.exec_immediate(conn, sql)
        if stmt:
            result = ibm_db.fetch_assoc(stmt)
            return {
                "status": "ok",
                "timestamp": datetime.now().isoformat(),
                "message": "DB2 connection is healthy",
                "connection_healthy": True,
                "summary": f"DB2 CONNECTION HEALTHY: Connected as {result.get('CONNECTED_USER', 'unknown')} to schema {result.get('CURRENT_SCHEMA', 'unknown')}",
                "connection_details": result,
            }
        else:
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "message": "Failed to execute health check query",
                "connection_healthy": False,
                "summary": "DB2 CONNECTION UNHEALTHY: Query execution failed",
            }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "message": f"Health check failed: {str(e)}",
            "connection_healthy": False,
            "summary": f"DB2 HEALTH CHECK ERROR: {str(e)}",
        }
    finally:
        if conn:
            ibm_db.close(conn)


print(get_db2_connection_health())
