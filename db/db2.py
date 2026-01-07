import ibm_db
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración de DB2 desde variables de entorno
DB2_USERNAME = os.getenv("DB2_USERNAME")
DB2_PASSWORD = os.getenv("DB2_PASSWORD")
DB2_HOST_URL = os.getenv("DB2_HOST_URL")
DB2_DATABASE = os.getenv("DB2_DATABASE")
DB2_PORT = os.getenv("DB2_PORT", "51000")


def get_db2_connection():
    """
    Establece y retorna una conexión a la base de datos DB2.

    Returns:
        connection: Objeto de conexión ibm_db si es exitoso, None si falla
    """
    try:
        # Construir el connection string para DB2
        conn_str = (
            f"DATABASE={DB2_DATABASE};"
            f"HOSTNAME={DB2_HOST_URL};"
            f"PORT={DB2_PORT};"
            f"PROTOCOL=TCPIP;"
            f"UID={DB2_USERNAME};"
            f"PWD={DB2_PASSWORD};"
        )

        # Intentar conectar
        conn = ibm_db.connect(conn_str, "", "")

        if conn:
            print(f"[DB2] ✓ Conexión exitosa a {DB2_DATABASE} en {DB2_HOST_URL}")
            return conn
        else:
            print(f"[DB2] ✗ Error al conectar: {ibm_db.conn_errormsg()}")
            return None

    except Exception as e:
        print(f"[DB2] ✗ Excepción al conectar: {str(e)}")
        return None


def test_connection():
    """
    Prueba la conexión a DB2 y muestra información básica.
    """
    conn = get_db2_connection()
    if conn:
        try:
            # Consulta simple para verificar la conexión
            sql = "SELECT CURRENT TIMESTAMP, CURRENT USER FROM SYSIBM.SYSDUMMY1"
            stmt = ibm_db.exec_immediate(conn, sql)
            result = ibm_db.fetch_tuple(stmt)

            print(f"[DB2] Timestamp: {result[0]}")
            print(f"[DB2] Usuario: {result[1]}")
            print(f"[DB2] Prueba de conexión exitosa")

            return True
        except Exception as e:
            print(f"[DB2] Error en prueba de conexión: {str(e)}")
            return False
        finally:
            ibm_db.close(conn)
    else:
        print("[DB2] No se pudo establecer conexión para prueba")
        return False


if __name__ == "__main__":
    # Prueba de conexión cuando se ejecuta directamente
    print("="*60)
    print("Probando conexión a DB2...")
    print("="*60)
    test_connection()
