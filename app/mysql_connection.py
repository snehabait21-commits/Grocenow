import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MySQLConnection:
    """
    MySQL database connection class using mysql-connector-python
    Handles connection, queries, and error management
    """

    def __init__(self):
        """Initialize database connection parameters"""
        self.host = os.getenv('DB_HOST', 'localhost')
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASSWORD', '')
        self.database = os.getenv('DB_NAME', 'groce_now_db')
        self.connection = None

    def connect(self):
        """
        Establish connection to MySQL database

        Step-by-step process:
        1. Try to create connection using credentials
        2. Handle connection errors gracefully
        3. Return connection object or None if failed
        """
        try:
            # Step 1: Create connection object
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                autocommit=False,  # We'll manage transactions manually
                connection_timeout=10  # 10 second timeout
            )

            # Step 2: Verify connection is successful
            if self.connection.is_connected():
                print(f"✅ Successfully connected to MySQL database: {self.database}")
                return self.connection

        except mysql.connector.Error as err:
            # Step 3: Handle specific MySQL errors
            self._handle_connection_error(err)
            return None

        except Exception as err:
            # Step 4: Handle general errors
            print(f"❌ Unexpected error: {err}")
            return None

    def _handle_connection_error(self, err):
        """
        Handle different types of MySQL connection errors
        """
        if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
            print("❌ Access denied: Check your username and password")
        elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            print(f"❌ Database '{self.database}' does not exist")
        elif err.errno == mysql.connector.errorcode.CR_CONN_HOST_ERROR:
            print(f"❌ Cannot connect to host '{self.host}'. Check if MySQL server is running")
        elif err.errno == mysql.connector.errorcode.CR_CONNECTION_ERROR:
            print("❌ Connection failed. Check network connectivity")
        else:
            print(f"❌ MySQL Error [{err.errno}]: {err}")

    def disconnect(self):
        """
        Close database connection safely
        """
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("🔌 Database connection closed")

    def execute_query(self, query, params=None, fetch=True):
        """
        Execute SQL query with proper error handling

        Args:
            query (str): SQL query to execute
            params (tuple): Query parameters for prepared statements
            fetch (bool): Whether to fetch results (for SELECT queries)

        Returns:
            tuple: (success, result/error_message)
        """
        if not self.connection or not self.connection.is_connected():
            return False, "Database not connected"

        cursor = None
        try:
            # Step 1: Create cursor
            cursor = self.connection.cursor(dictionary=True)

            # Step 2: Execute query
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # Step 3: Handle different query types
            if fetch and query.strip().upper().startswith('SELECT'):
                # For SELECT queries, fetch results
                result = cursor.fetchall()
                return True, result
            else:
                # For INSERT, UPDATE, DELETE queries
                self.connection.commit()  # Commit the transaction
                return True, cursor.rowcount  # Return affected rows

        except mysql.connector.Error as err:
            # Step 4: Handle query execution errors
            self._handle_query_error(err)
            # Rollback on error
            if self.connection:
                self.connection.rollback()
            return False, str(err)

        except Exception as err:
            print(f"❌ Unexpected error during query execution: {err}")
            if self.connection:
                self.connection.rollback()
            return False, str(err)

        finally:
            # Step 5: Always close cursor
            if cursor:
                cursor.close()

    def _handle_query_error(self, err):
        """
        Handle different types of query execution errors
        """
        if err.errno == mysql.connector.errorcode.ER_NO_SUCH_TABLE:
            print("❌ Table does not exist")
        elif err.errno == mysql.connector.errorcode.ER_DUP_ENTRY:
            print("❌ Duplicate entry error")
        elif err.errno == mysql.connector.errorcode.ER_PARSE_ERROR:
            print("❌ SQL syntax error")
        elif err.errno == mysql.connector.errorcode.ER_BAD_FIELD_ERROR:
            print("❌ Column/field does not exist")
        else:
            print(f"❌ Query Error [{err.errno}]: {err}")

    def test_connection(self):
        """
        Test database connection and basic functionality
        """
        print("\n🧪 Testing MySQL Connection...")

        # Test 1: Basic connection
        if not self.connect():
            return False

        # Test 2: Simple query
        success, result = self.execute_query("SELECT 1 as test")
        if success:
            print("✅ Basic query test passed")
        else:
            print(f"❌ Query test failed: {result}")

        # Test 3: Check if our tables exist
        success, result = self.execute_query("""
            SHOW TABLES LIKE 'users'
        """)
        if success and result:
            print("✅ Tables exist in database")
        else:
            print("⚠️  Tables may not be created yet")

        self.disconnect()
        return True

# Global connection instance
db_connection = MySQLConnection()

# Utility functions for easy use
def get_db_connection():
    """
    Get database connection instance
    """
    return db_connection

def init_db_connection():
    """
    Initialize database connection
    """
    return db_connection.connect()

def close_db_connection():
    """
    Close database connection
    """
    db_connection.disconnect()


