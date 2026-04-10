from db.db2 import get_db2_connection
import ibm_db
from datetime import datetime


def get_db2_active_connections():
    """
    Obtiene el número de conexiones activas a DB2
    Útil para monitorear carga y detectar problemas de conexión
    """
    # Usar SYSIBMADM.APPLICATIONS que es más compatible entre versiones de DB2
    sql = """
    SELECT
        APPL_STATUS,
        COUNT(*) as COUNT_BY_STATUS
    FROM SYSIBMADM.APPLICATIONS
    GROUP BY APPL_STATUS
    """

    conn = get_db2_connection()
    if not conn:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "message": "No se pudo conectar a DB2",
            "voice_ready": "Error de conexión a la base de datos."
        }

    try:
        stmt = ibm_db.exec_immediate(conn, sql)
        if not stmt:
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "message": "Error ejecutando consulta",
                "voice_ready": "No pude obtener información de conexiones."
            }

        connections_by_status = {}
        total = 0

        while True:
            row = ibm_db.fetch_assoc(stmt)
            if not row:
                break
            status = row.get('APPL_STATUS', 'UNKNOWN')
            count = int(row.get('COUNT_BY_STATUS', 0))
            connections_by_status[status] = count
            total += count

        # Generar mensaje de voz descriptivo
        if total == 0:
            voice_text = "No hay conexiones activas a la base de datos."
        elif total == 1:
            voice_text = "Hay una conexión activa a la base de datos."
        else:
            voice_text = f"Hay {total} conexiones activas a la base de datos."

        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "message": f"Total de conexiones activas: {total}",
            "total_connections": total,
            "connections_by_status": connections_by_status,
            "voice_ready": voice_text
        }

    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "message": f"Error: {str(e)}",
            "voice_ready": f"Error consultando conexiones: {str(e)}"
        }
    finally:
        if conn:
            ibm_db.close(conn)

def get_db2_tablespace_usage():
    """
    Obtiene información detallada del uso de tablespaces en DB2
    Formato optimizado para comprensión de modelos de lenguaje
    """
    sql = """
    SELECT 
        TBSP_NAME,
        TBSP_TYPE,
        TBSP_CONTENT_TYPE,
        TBSP_TOTAL_SIZE_KB,
        TBSP_USED_SIZE_KB,
        TBSP_FREE_SIZE_KB,
        TBSP_UTILIZATION_PERCENT,
        CASE 
            WHEN TBSP_UTILIZATION_PERCENT >= 90 THEN 'CRITICAL'
            WHEN TBSP_UTILIZATION_PERCENT >= 80 THEN 'WARNING'
            WHEN TBSP_UTILIZATION_PERCENT >= 70 THEN 'ATTENTION'
            ELSE 'NORMAL'
        END as STATUS_LEVEL,
        CASE 
            WHEN TBSP_UTILIZATION_PERCENT >= 90 THEN 'Tablespace critically full - immediate action required'
            WHEN TBSP_UTILIZATION_PERCENT >= 80 THEN 'Tablespace nearly full - plan capacity expansion'
            WHEN TBSP_UTILIZATION_PERCENT >= 70 THEN 'Tablespace usage high - monitor closely'
            ELSE 'Tablespace usage normal'
        END as RECOMMENDATION
    FROM SYSIBMADM.TBSP_UTILIZATION
    ORDER BY TBSP_UTILIZATION_PERCENT DESC
    """
    
    conn = get_db2_connection()
    if not conn:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "message": "Failed to connect to DB2 database",
            "issues_count": 1,
            "critical_issues": 1,
            "warning_issues": 0,
            "summary": "DATABASE CONNECTION FAILURE: Unable to establish connection to DB2. Check network connectivity and credentials.",
            "recommendations": [
                "Verify DB2 database is running",
                "Check network connectivity to DB2 server",
                "Validate database credentials",
                "Review DB2 instance status"
            ],
            "raw_data": {"columns": [], "data": []}
        }
    
    try:
        stmt = ibm_db.prepare(conn, sql)
        if not stmt:
            error_msg = ibm_db.stmt_errormsg()
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "message": f"Query preparation failed: {error_msg}",
                "issues_count": 1,
                "critical_issues": 1,
                "warning_issues": 0,
                "summary": f"SQL PREPARATION ERROR: {error_msg}",
                "recommendations": ["Check SQL syntax", "Verify database permissions"],
                "raw_data": {"columns": [], "data": []}
            }
        
        if not ibm_db.execute(stmt):
            error_msg = ibm_db.stmt_errormsg()
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "message": f"Query execution failed: {error_msg}",
                "issues_count": 1,
                "critical_issues": 1,
                "warning_issues": 0,
                "summary": f"SQL EXECUTION ERROR: {error_msg}",
                "recommendations": ["Verify table permissions", "Check database availability"],
                "raw_data": {"columns": [], "data": []}
            }
        
        # Obtener resultados
        data = []
        while True:
            row = ibm_db.fetch_tuple(stmt)
            if not row:
                break
            data.append(row)
        
        columns = ["TBSP_NAME", "TBSP_TYPE", "TBSP_CONTENT_TYPE", "TBSP_TOTAL_SIZE_KB", 
                  "TBSP_USED_SIZE_KB", "TBSP_FREE_SIZE_KB", "TBSP_UTILIZATION_PERCENT", 
                  "STATUS_LEVEL", "RECOMMENDATION"]
        
        if not data:
            return {
                "status": "info",
                "timestamp": datetime.now().isoformat(),
                "message": "No tablespaces found in database",
                "issues_count": 0,
                "critical_issues": 0,
                "warning_issues": 0,
                "summary": "NO TABLESPACES DETECTED: Database query returned no tablespace information.",
                "recommendations": ["Verify database contains tablespaces", "Check monitoring permissions"],
                "raw_data": {"columns": columns, "data": []}
            }
        
        # Análisis de datos para el modelo de lenguaje
        critical_tablespaces = []
        warning_tablespaces = []
        attention_tablespaces = []
        normal_tablespaces = []
        
        total_size_gb = 0
        total_used_gb = 0
        
        for row in data:
            tbsp_name = row[0]
            utilization = float(row[6]) if row[6] is not None else 0
            total_size_kb = int(row[3]) if row[3] is not None else 0
            used_size_kb = int(row[4]) if row[4] is not None else 0
            status_level = row[7]
            recommendation = row[8]
            
            total_size_gb += total_size_kb / (1024 * 1024)
            total_used_gb += used_size_kb / (1024 * 1024)
            
            tablespace_info = {
                "name": tbsp_name,
                "utilization_percent": utilization,
                "size_gb": round(total_size_kb / (1024 * 1024), 2),
                "used_gb": round(used_size_kb / (1024 * 1024), 2),
                "free_gb": round((total_size_kb - used_size_kb) / (1024 * 1024), 2),
                "status": status_level,
                "recommendation": recommendation
            }
            
            if status_level == 'CRITICAL':
                critical_tablespaces.append(tablespace_info)
            elif status_level == 'WARNING':
                warning_tablespaces.append(tablespace_info)
            elif status_level == 'ATTENTION':
                attention_tablespaces.append(tablespace_info)
            else:
                normal_tablespaces.append(tablespace_info)
        
        # Generar resumen inteligente para el modelo de lenguaje
        summary_parts = []
        recommendations = []
        
        if critical_tablespaces:
            critical_names = [ts['name'] for ts in critical_tablespaces]
            summary_parts.append(f"CRITICAL ALERT: {len(critical_tablespaces)} tablespace(s) are critically full (≥90% used): {', '.join(critical_names)}")
            recommendations.extend([
                "IMMEDIATE ACTION REQUIRED: Add storage or free up space in critical tablespaces",
                "Consider extending tablespace containers or adding new ones",
                "Review and purge unnecessary data if possible"
            ])
        
        if warning_tablespaces:
            warning_names = [ts['name'] for ts in warning_tablespaces]
            summary_parts.append(f"WARNING: {len(warning_tablespaces)} tablespace(s) need attention (≥80% used): {', '.join(warning_names)}")
            recommendations.extend([
                "Plan capacity expansion for warning tablespaces within next maintenance window",
                "Monitor growth trends and forecast future storage needs"
            ])
        
        if attention_tablespaces:
            attention_names = [ts['name'] for ts in attention_tablespaces]
            summary_parts.append(f"ATTENTION: {len(attention_tablespaces)} tablespace(s) should be monitored (≥70% used): {', '.join(attention_names)}")
            recommendations.append("Continue monitoring tablespaces with high utilization")
        
        if normal_tablespaces:
            summary_parts.append(f"NORMAL: {len(normal_tablespaces)} tablespace(s) are operating within normal parameters")
        
        # Estadísticas generales
        overall_utilization = round((total_used_gb / total_size_gb) * 100, 2) if total_size_gb > 0 else 0
        summary_parts.append(f"OVERALL DATABASE UTILIZATION: {overall_utilization}% ({round(total_used_gb, 2)}GB used of {round(total_size_gb, 2)}GB total)")
        
        # Determinar estado general
        if critical_tablespaces:
            status = "critical"
            message = f"CRITICAL: {len(critical_tablespaces)} tablespace(s) require immediate attention"
        elif warning_tablespaces:
            status = "warning"
            message = f"WARNING: {len(warning_tablespaces)} tablespace(s) need capacity planning"
        elif attention_tablespaces:
            status = "attention"
            message = f"ATTENTION: {len(attention_tablespaces)} tablespace(s) should be monitored closely"
        else:
            status = "ok"
            message = f"All {len(data)} tablespaces are operating normally"
        
        return {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "issues_count": len(critical_tablespaces) + len(warning_tablespaces),
            "critical_issues": len(critical_tablespaces),
            "warning_issues": len(warning_tablespaces),
            "summary": " | ".join(summary_parts),
            "recommendations": recommendations,
            "detailed_analysis": {
                "critical_tablespaces": critical_tablespaces,
                "warning_tablespaces": warning_tablespaces,
                "attention_tablespaces": attention_tablespaces,
                "normal_tablespaces": normal_tablespaces,
                "overall_utilization_percent": overall_utilization,
                "total_size_gb": round(total_size_gb, 2),
                "total_used_gb": round(total_used_gb, 2),
                "total_free_gb": round(total_size_gb - total_used_gb, 2)
            },
            "raw_data": {"columns": columns, "data": data}
        }
        
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "message": f"Error executing tablespace query: {str(e)}",
            "issues_count": 1,
            "critical_issues": 1,
            "warning_issues": 0,
            "summary": f"QUERY EXECUTION ERROR: {str(e)}",
            "recommendations": [
                "Check database connectivity",
                "Verify SQL query syntax",
                "Review database permissions"
            ],
            "raw_data": {"columns": [], "data": []}
        }
    finally:
        if conn:
            ibm_db.close(conn)


def get_db2_tablespace_summary():
    """
    Versión resumida del uso de tablespaces en DB2
    Optimizada para modelos de lenguaje - respuesta concisa y accionable
    """
    sql = """
    SELECT 
        TBSP_NAME,
        TBSP_UTILIZATION_PERCENT,
        TBSP_TOTAL_SIZE_KB,
        TBSP_USED_SIZE_KB,
        CASE 
            WHEN TBSP_UTILIZATION_PERCENT >= 90 THEN 'CRITICAL'
            WHEN TBSP_UTILIZATION_PERCENT >= 80 THEN 'WARNING'
            WHEN TBSP_UTILIZATION_PERCENT >= 70 THEN 'ATTENTION'
            ELSE 'NORMAL'
        END as STATUS_LEVEL
    FROM SYSIBMADM.TBSP_UTILIZATION
    WHERE TBSP_UTILIZATION_PERCENT >= 70 OR TBSP_UTILIZATION_PERCENT = -1
    ORDER BY TBSP_UTILIZATION_PERCENT DESC
    """
    
    conn = get_db2_connection()
    if not conn:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "message": "Cannot connect to DB2",
            "voice_ready": "Database connection failed. Unable to check tablespace status."
        }
    
    try:
        stmt = ibm_db.exec_immediate(conn, sql)
        if not stmt:
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "message": "Query execution failed",
                "voice_ready": "Database query failed. Cannot retrieve tablespace information."
            }
        
        # Obtener resultados
        data = []
        while True:
            row = ibm_db.fetch_tuple(stmt)
            if not row:
                break
            data.append(row)
        
        if not data:
            return {
                "status": "ok",
                "timestamp": datetime.now().isoformat(),
                "message": "All tablespaces are operating normally",
                "voice_ready": "All database tablespaces are operating within normal parameters."
            }
        
        # Análisis simplificado
        critical_issues = []
        warning_issues = []
        attention_issues = []
        
        total_size_gb = 0
        total_used_gb = 0
        
        for row in data:
            tbsp_name = row[0]
            utilization = float(row[1]) if row[1] is not None and row[1] != -1 else 0
            total_size_kb = int(row[2]) if row[2] is not None else 0
            used_size_kb = int(row[3]) if row[3] is not None else 0
            status_level = row[4]
            
            # Solo contar tablespaces con tamaño real (no temporales con -1%)
            if utilization >= 0:
                total_size_gb += total_size_kb / (1024 * 1024)
                total_used_gb += used_size_kb / (1024 * 1024)
            
            if status_level == 'CRITICAL' and utilization >= 0:
                critical_issues.append(f"{tbsp_name} ({utilization}%)")
            elif status_level == 'WARNING' and utilization >= 0:
                warning_issues.append(f"{tbsp_name} ({utilization}%)")
            elif status_level == 'ATTENTION' and utilization >= 0:
                attention_issues.append(f"{tbsp_name} ({utilization}%)")
        
        # Calcular utilización general
        overall_utilization = round((total_used_gb / total_size_gb) * 100, 2) if total_size_gb > 0 else 0
        
        # Generar recomendaciones priorizadas
        immediate_actions = []
        planned_actions = []
        
        if critical_issues:
            critical_names = [issue.split(' (')[0] for issue in critical_issues]
            immediate_actions.extend([
                f"URGENT: Add storage to {', '.join(critical_names)}",
                "Consider extending tablespace containers immediately"
            ])
        
        if warning_issues:
            warning_names = [issue.split(' (')[0] for issue in warning_issues]
            planned_actions.append(f"Plan capacity expansion for {', '.join(warning_names)}")
        
        if attention_issues:
            planned_actions.append("Monitor high-utilization tablespaces closely")
        
        # Determinar estado y mensaje
        if critical_issues:
            status = "critical"
            message = f"CRITICAL: {len(critical_issues)} tablespaces require immediate attention"
            voice_text = f"Database is in critical state. {len(critical_issues)} tablespaces are at critical capacity: {', '.join([issue.split(' (')[0] for issue in critical_issues])}. Immediate storage expansion required."
        elif warning_issues:
            status = "warning"
            message = f"WARNING: {len(warning_issues)} tablespaces need capacity planning"
            voice_text = f"Database shows warning conditions. {len(warning_issues)} tablespaces need attention: {', '.join([issue.split(' (')[0] for issue in warning_issues])}. Plan capacity expansion."
        elif attention_issues:
            status = "attention"
            message = f"ATTENTION: {len(attention_issues)} tablespaces should be monitored"
            voice_text = f"Database requires monitoring attention. {len(attention_issues)} tablespaces have high utilization and should be watched closely."
        else:
            status = "ok"
            message = "All tablespaces are operating normally"
            voice_text = "All database tablespaces are operating within normal parameters."
        
        return {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "critical_issues": critical_issues,
            "warning_issues": warning_issues,
            "attention_issues": attention_issues,
            "overall_utilization": f"{overall_utilization}% ({round(total_used_gb, 1)}GB/{round(total_size_gb, 1)}GB)",
            "immediate_actions": immediate_actions,
            "planned_actions": planned_actions,
            "voice_ready": voice_text
        }
        
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "message": f"Error executing query: {str(e)}",
            "voice_ready": f"Database monitoring error: {str(e)}"
        }
    finally:
        if conn:
            ibm_db.close(conn)


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
            "summary": "DB2 CONNECTION FAILED: Unable to connect to database"
        }
    
    try:
        stmt = ibm_db.exec_immediate(conn, sql)
        if stmt:
            result = ibm_db.fetch_assoc(stmt)
            for key, value in result.items():            
                if isinstance(value, datetime):                     
                    result[key] = value.isoformat()
            return {
                "status": "ok",
                "timestamp": datetime.now().isoformat(),
                "message": "DB2 connection is healthy",
                "connection_healthy": True,
                "summary": f"DB2 CONNECTION HEALTHY: Connected as {result.get('CONNECTED_USER', 'unknown')} to schema {result.get('CURRENT_SCHEMA', 'unknown')}",
                "connection_details": result
            }
        else:
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "message": "Failed to execute health check query",
                "connection_healthy": False,
                "summary": "DB2 CONNECTION UNHEALTHY: Query execution failed"
            }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "message": f"Health check failed: {str(e)}",
            "connection_healthy": False,
            "summary": f"DB2 HEALTH CHECK ERROR: {str(e)}"
        }
    finally:
        if conn:
            ibm_db.close(conn)


def get_db2_database_size():
    """
    Obtiene información del tamaño de la base de datos DB2
    """
    sql = """
    SELECT 
        SUM(TBSP_TOTAL_SIZE_KB) / 1024 / 1024 as TOTAL_SIZE_GB,
        SUM(TBSP_USED_SIZE_KB) / 1024 / 1024 as USED_SIZE_GB,
        SUM(TBSP_FREE_SIZE_KB) / 1024 / 1024 as FREE_SIZE_GB,
        ROUND(AVG(TBSP_UTILIZATION_PERCENT), 2) as AVG_UTILIZATION_PERCENT,
        COUNT(*) as TOTAL_TABLESPACES
    FROM SYSIBMADM.TBSP_UTILIZATION
    """
    
    conn = get_db2_connection()
    if not conn:
        return {
            "status": "error",
            "message": "Cannot connect to DB2",
            "summary": "DATABASE SIZE CHECK FAILED: Connection error"
        }
    
    try:
        stmt = ibm_db.exec_immediate(conn, sql)
        if stmt:
            result = ibm_db.fetch_assoc(stmt)
            total_size = float(result.get('TOTAL_SIZE_GB', 0))
            used_size = float(result.get('USED_SIZE_GB', 0))
            free_size = float(result.get('FREE_SIZE_GB', 0))
            avg_util = float(result.get('AVG_UTILIZATION_PERCENT', 0))
            
            return {
                "status": "ok",
                "timestamp": datetime.now().isoformat(),
                "message": f"Database size: {total_size:.2f}GB total, {used_size:.2f}GB used ({avg_util:.1f}% average utilization)",
                "summary": f"DB2 DATABASE SIZE: {total_size:.2f}GB total capacity, {used_size:.2f}GB used, {free_size:.2f}GB available space, average {avg_util:.1f}% utilization across {result.get('TOTAL_TABLESPACES', 0)} tablespaces",
                "database_metrics": {
                    "total_size_gb": round(total_size, 2),
                    "used_size_gb": round(used_size, 2),
                    "free_size_gb": round(free_size, 2),
                    "average_utilization_percent": round(avg_util, 2),
                    "total_tablespaces": int(result.get('TOTAL_TABLESPACES', 0))
                }
            }
        else:
            return {
                "status": "error",
                "message": "Failed to retrieve database size information",
                "summary": "DATABASE SIZE QUERY FAILED: Unable to execute size query"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error getting database size: {str(e)}",
            "summary": f"DATABASE SIZE ERROR: {str(e)}"
        }
    finally:
        if conn:
            ibm_db.close(conn)

