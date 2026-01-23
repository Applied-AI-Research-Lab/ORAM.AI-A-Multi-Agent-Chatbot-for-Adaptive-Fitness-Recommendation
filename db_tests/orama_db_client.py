import requests
import json


class OramaDBClient:
    """
    Python client for ORAMA Database Management API
    
    This class provides a convenient interface to interact with the database
    management endpoints without having to manually construct HTTP requests.
    
    Args:
        base_url: The base URL of the API (e.g., 'https://my-orama.my-domain.com')
        secret_key: The secret key for authentication
    
    Example:
        client = OramaDBClient('https://my-orama.my-domain.com', 'orama_db')
        tables = client.list_tables()
        print(tables)
    """
    
    def __init__(self, base_url, secret_key):
        """
        Initialize the database client
        
        Args:
            base_url: Base URL of the API server
            secret_key: Secret key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'X-Secret-Key': secret_key,
            'Content-Type': 'application/json'
        }
    
    def list_tables(self):
        """
        Get a list of all tables in the database
            
        Example:
            tables = client.list_tables()
            print(tables['tables'])
        """
        response = requests.get(
            f"{self.base_url}/api/orama-db/tables",
            headers=self.headers
        )
        return response.json()
    
    def get_table_info(self, table_name):
        """
        Get detailed information about a specific table
        Shows columns, types, and constraints
            
        Example:
            info = client.get_table_info('users')
            print(info['columns'])
        """
        response = requests.get(
            f"{self.base_url}/api/orama-db/table-info",
            params={'table_name': table_name},
            headers=self.headers
        )
        return response.json()
    
    def add_columns(self, table_name, columns):
        """
        Add columns to an existing table if they don't exist
        
        Args:
            table_name: Name of the existing table
            columns: List of column definitions, each column is a dict with:
                - name: Column name (required)
                - type: Data type like INTEGER, TEXT, REAL, TIMESTAMP (required)
                - nullable: True to allow NULL values (optional, default: True)
                - default: Default value for existing rows (optional)
                
        Returns:
            dict: Response with lists of added and skipped columns
            
        Example:
            result = client.add_columns('users', [
                {'name': 'phone', 'type': 'TEXT', 'nullable': True},
                {'name': 'status', 'type': 'TEXT', 'default': 'active'},
                {'name': 'credits', 'type': 'INTEGER', 'default': 0, 'nullable': False}
            ])
            print(f"Added: {result['added']}")
            print(f"Skipped (already exist): {result['skipped']}")
        """
        data = {
            "table_name": table_name,
            "columns": columns
        }
        response = requests.post(
            f"{self.base_url}/api/orama-db/add-columns",
            json=data,
            headers=self.headers
        )
        return response.json()
    
    def create_table(self, table_name, columns):
        """
        Create a new table in the database
        
        Args:
            table_name: Name for the new table
            columns: List of column definitions, each column is a dict with:
                - name: Column name (required)
                - type: Data type like INTEGER, TEXT, REAL, TIMESTAMP (required)
                - primary_key: True if this is the primary key (optional)
                - nullable: False to make it NOT NULL (optional)
                
        Returns:
            dict: Success message
            
        Example:
            result = client.create_table('products', [
                {'name': 'id', 'type': 'INTEGER', 'primary_key': True},
                {'name': 'name', 'type': 'TEXT', 'nullable': False},
                {'name': 'price', 'type': 'REAL'}
            ])
        """
        data = {
            "table_name": table_name,
            "columns": columns
        }
        response = requests.post(
            f"{self.base_url}/api/orama-db/create-table",
            json=data,
            headers=self.headers
        )
        return response.json()
    
    def delete_table(self, table_name, confirm=False):
        """
        Delete (DROP) a table from the database
        SOS: This permanently removes the table and all its data
            
        Example:
            result = client.delete_table('old_table', confirm=True)
        """
        data = {
            "table_name": table_name,
            "confirm": confirm
        }
        response = requests.post(
            f"{self.base_url}/api/orama-db/delete-table",
            json=data,
            headers=self.headers
        )
        return response.json()
    
    def truncate_table(self, table_name, confirm=False):
        """
        Truncate (empty) a table, removing all data but keeping the structure
        This also resets auto-increment counters
            
        Example:
            result = client.truncate_table('temp_data', confirm=True)
        """
        data = {
            "table_name": table_name,
            "confirm": confirm
        }
        response = requests.post(
            f"{self.base_url}/api/orama-db/truncate-table",
            json=data,
            headers=self.headers
        )
        return response.json()
    
    def insert(self, table_name, data):
        """
        Insert a new record into a table
            
        Example:
            result = client.insert('users', {
                'username': 'Konstantinos Roumeliotis',
                'email': 'example@example.gr',
                'age': 30
            })
        """
        request_data = {
            "table_name": table_name,
            "data": data
        }
        response = requests.post(
            f"{self.base_url}/api/orama-db/insert",
            json=request_data,
            headers=self.headers
        )
        return response.json()
    
    def update(self, table_name, data, where):
        """
        Update existing records in a table
            
        Example:
            result = client.update(
                'users',
                data={'age': 37},
                where={'username': 'Konstantinos Roumeliotis'}
            )
        """
        request_data = {
            "table_name": table_name,
            "data": data,
            "where": where
        }
        response = requests.post(
            f"{self.base_url}/api/orama-db/update",
            json=request_data,
            headers=self.headers
        )
        return response.json()
    
    def delete(self, table_name, where, confirm=False):
        """
        Delete records from a table
            
        Example:
            result = client.delete(
                'users',
                where={'username': 'Konstantinos Roumeliotis'},
                confirm=True
            )
        """
        request_data = {
            "table_name": table_name,
            "where": where,
            "confirm": confirm
        }
        response = requests.post(
            f"{self.base_url}/api/orama-db/delete",
            json=request_data,
            headers=self.headers
        )
        return response.json()
    
    def query(self, sql, params=None):
        """
        Execute a custom SQL query
        Supports both SELECT and other SQL statements
        Use :param_name syntax for parameters
        
        Args:
            sql: SQL query string (use :param_name for parameters)
            params: Optional dictionary of parameters
            
        Returns:
            dict: Response with 'results' (for SELECT) or 'rows_affected'
            
        Example:
            # Simple query
            result = client.query("SELECT * FROM users")
            
            # With parameters
            result = client.query(
                "SELECT * FROM users WHERE age > :min_age",
                {"min_age": 18}
            )
        """
        request_data = {
            "sql": sql,
            "params": params or {}
        }
        response = requests.post(
            f"{self.base_url}/api/orama-db/query",
            json=request_data,
            headers=self.headers
        )
        return response.json()
    
    def get_backup(self):
        """
        Get a complete backup of the database
        Includes all tables with their schema and data
        
        Returns:
            dict: Complete database backup with:
                - backup_date: ISO timestamp
                - tables: Dictionary of all tables with schema and data
        """
        response = requests.get(
            f"{self.base_url}/api/orama-db/backup",
            headers=self.headers
        )
        return response.json()