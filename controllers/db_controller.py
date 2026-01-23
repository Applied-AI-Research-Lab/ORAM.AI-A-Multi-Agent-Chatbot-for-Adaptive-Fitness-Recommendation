from flask import request, jsonify
from models import Base
from sqlalchemy import inspect, text
import os


class DatabaseController:
    """
    ### DatabaseController (`db_controller.py`)
    Database Management Controller - Handles database administration endpoints
    Provides full database management capabilities:
    - **POST /api/orama-db/create-table** - Create new database tables
    - **POST /api/orama-db/delete-table** - Delete existing tables
    - **POST /api/orama-db/insert** - Insert new records
    - **POST /api/orama-db/update** - Update existing records
    - **POST /api/orama-db/delete** - Delete records
    - **POST /api/orama-db/query** - Execute custom SQL queries
    - **GET /api/orama-db/tables** - List all tables
    - **GET /api/orama-db/table-info** - Get table structure information
    
    SECURITY: All endpoints require a valid secret key in the X-Secret-Key header
    """
    
    # Secret key for database administration
    # WARNING: Change this in production and store in environment variables
    SECRET_KEY = os.getenv('DB_ADMIN_SECRET_KEY', 'orama_db')
    
    def __init__(self, db):
        """
        Initialize database controller with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.engine = db.get_bind()
    
    def _validate_secret_key(self):
        """
        Validate that the request contains the correct secret key.
        
        Returns:
            tuple: (is_valid: bool, error_response: tuple or None)
        """
        secret_key = request.headers.get('X-Secret-Key')
        
        if not secret_key:
            return False, (jsonify({'error': 'Missing X-Secret-Key header'}), 401)
        
        if secret_key != self.SECRET_KEY:
            return False, (jsonify({'error': 'Invalid secret key'}), 403)
        
        return True, None
    
    def create_table(self):
        """
        Create a new database table.
        
        Request:
            POST /api/orama-db/create-table
            Headers: X-Secret-Key: {secret_key}
            Body: {
                "table_name": str,           # Name of the table to create
                "columns": [                 # List of column definitions
                    {
                        "name": str,         # Column name
                        "type": str,         # Column type (INTEGER, TEXT, VARCHAR, DATETIME, etc.)
                        "primary_key": bool, # Optional: Is this a primary key?
                        "nullable": bool,    # Optional: Can this be NULL?
                        "unique": bool       # Optional: Must values be unique?
                    },
                    ...
                ]
            }
        
        Response:
            200: {"message": "Table created successfully", "table_name": str}
            400: {"error": str}  # Invalid request
            401: {"error": str}  # Missing secret key
            403: {"error": str}  # Invalid secret key
            500: {"error": str}  # Server error
        """
        is_valid, error_response = self._validate_secret_key()
        if not is_valid:
            return error_response
        
        try:
            data = request.get_json()
            table_name = data.get('table_name')
            columns = data.get('columns')
            
            if not table_name or not columns:
                return jsonify({'error': 'Missing table_name or columns'}), 400
            
            # Build CREATE TABLE SQL statement
            column_defs = []
            for col in columns:
                col_name = col.get('name')
                col_type = col.get('type', 'TEXT')
                
                # For PostgreSQL, use SERIAL for auto-incrementing integer primary keys
                if col.get('primary_key') and col_type.upper() == 'INTEGER':
                    col_def = f"{col_name} SERIAL PRIMARY KEY"
                else:
                    col_def = f"{col_name} {col_type}"
                    
                    if col.get('primary_key'):
                        col_def += " PRIMARY KEY"
                    
                    if col.get('unique'):
                        col_def += " UNIQUE"
                    
                    if not col.get('nullable', True) and not col.get('primary_key'):
                        col_def += " NOT NULL"
                
                column_defs.append(col_def)
            
            create_sql = f"CREATE TABLE {table_name} ({', '.join(column_defs)})"
            
            # Execute the CREATE TABLE statement
            with self.engine.connect() as conn:
                conn.execute(text(create_sql))
                conn.commit()
            
            return jsonify({
                'message': 'Table created successfully',
                'table_name': table_name,
                'sql': create_sql
            }), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def truncate_table(self):
        """
        Empty a table by removing all records (TRUNCATE).
        This keeps the table structure but deletes all data.
        
        Request:
            POST /api/orama-db/truncate-table
            Headers: X-Secret-Key: {secret_key}
            Body: {
                "table_name": str,      # Name of the table to empty
                "confirm": bool         # Must be true to confirm truncation
            }
        
        Response:
            200: {"message": "Table truncated successfully", "table_name": str}
            400: {"error": str}  # Invalid request
            401: {"error": str}  # Missing secret key
            403: {"error": str}  # Invalid secret key
            500: {"error": str}  # Server error
        """
        is_valid, error_response = self._validate_secret_key()
        if not is_valid:
            return error_response
        
        try:
            data = request.get_json()
            table_name = data.get('table_name')
            confirm = data.get('confirm')
            
            if not table_name:
                return jsonify({'error': 'Missing table_name'}), 400
            
            if not confirm:
                return jsonify({'error': 'Must set confirm=true to truncate table'}), 400
            
            # Execute the TRUNCATE TABLE statement
            # RESTART IDENTITY resets auto-increment counters
            # CASCADE handles foreign key constraints
            truncate_sql = f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE"
            with self.engine.connect() as conn:
                conn.execute(text(truncate_sql))
                conn.commit()
            
            return jsonify({
                'message': 'Table truncated successfully',
                'table_name': table_name
            }), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def delete_table(self):
        """
        Delete an existing database table.
        
        Request:
            POST /api/orama-db/delete-table
            Headers: X-Secret-Key: {secret_key}
            Body: {
                "table_name": str,      # Name of the table to delete
                "confirm": bool         # Must be true to confirm deletion
            }
        
        Response:
            200: {"message": "Table deleted successfully", "table_name": str}
            400: {"error": str}  # Invalid request
            401: {"error": str}  # Missing secret key
            403: {"error": str}  # Invalid secret key
            500: {"error": str}  # Server error
        """
        is_valid, error_response = self._validate_secret_key()
        if not is_valid:
            return error_response
        
        try:
            data = request.get_json()
            table_name = data.get('table_name')
            confirm = data.get('confirm')
            
            if not table_name:
                return jsonify({'error': 'Missing table_name'}), 400
            
            if not confirm:
                return jsonify({'error': 'Must set confirm=true to delete table'}), 400
            
            # Execute the DROP TABLE statement
            drop_sql = f"DROP TABLE IF EXISTS {table_name}"
            with self.engine.connect() as conn:
                conn.execute(text(drop_sql))
                conn.commit()
            
            return jsonify({
                'message': 'Table deleted successfully',
                'table_name': table_name
            }), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def insert_record(self):
        """
        Insert a new record into a table.
        
        Request:
            POST /api/orama-db/insert
            Headers: X-Secret-Key: {secret_key}
            Body: {
                "table_name": str,           # Target table name
                "data": {                    # Column-value pairs
                    "column1": value1,
                    "column2": value2,
                    ...
                }
            }
        
        Response:
            200: {"message": "Record inserted successfully", "rows_affected": int}
            400: {"error": str}  # Invalid request
            401: {"error": str}  # Missing secret key
            403: {"error": str}  # Invalid secret key
            500: {"error": str}  # Server error
        """
        is_valid, error_response = self._validate_secret_key()
        if not is_valid:
            return error_response
        
        try:
            request_data = request.get_json()
            table_name = request_data.get('table_name')
            data = request_data.get('data')
            
            if not table_name or not data:
                return jsonify({'error': 'Missing table_name or data'}), 400
            
            # Build INSERT statement
            columns = ', '.join(data.keys())
            placeholders = ', '.join([f":{key}" for key in data.keys()])
            insert_sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            
            # Execute the INSERT statement
            with self.engine.connect() as conn:
                result = conn.execute(text(insert_sql), data)
                conn.commit()
            
            return jsonify({
                'message': 'Record inserted successfully',
                'rows_affected': result.rowcount
            }), 200
            
        except Exception as e:
            self.db.rollback()
            return jsonify({'error': str(e)}), 500
    
    def update_record(self):
        """
        Update existing records in a table.
        
        Request:
            POST /api/orama-db/update
            Headers: X-Secret-Key: {secret_key}
            Body: {
                "table_name": str,           # Target table name
                "data": {                    # Column-value pairs to update
                    "column1": value1,
                    "column2": value2,
                    ...
                },
                "where": {                   # WHERE clause conditions
                    "column": value,
                    ...
                }
            }
        
        Response:
            200: {"message": "Records updated successfully", "rows_affected": int}
            400: {"error": str}  # Invalid request
            401: {"error": str}  # Missing secret key
            403: {"error": str}  # Invalid secret key
            500: {"error": str}  # Server error
        """
        is_valid, error_response = self._validate_secret_key()
        if not is_valid:
            return error_response
        
        try:
            request_data = request.get_json()
            table_name = request_data.get('table_name')
            data = request_data.get('data')
            where = request_data.get('where')
            
            if not table_name or not data or not where:
                return jsonify({'error': 'Missing table_name, data, or where clause'}), 400
            
            # Build UPDATE statement
            set_clause = ', '.join([f"{key} = :set_{key}" for key in data.keys()])
            where_clause = ' AND '.join([f"{key} = :where_{key}" for key in where.keys()])
            update_sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
            
            # Prepare parameters with prefixes to avoid conflicts
            params = {}
            for key, value in data.items():
                params[f'set_{key}'] = value
            for key, value in where.items():
                params[f'where_{key}'] = value
            
            # Execute the UPDATE statement
            with self.engine.connect() as conn:
                result = conn.execute(text(update_sql), params)
                conn.commit()
            
            return jsonify({
                'message': 'Records updated successfully',
                'rows_affected': result.rowcount
            }), 200
            
        except Exception as e:
            self.db.rollback()
            return jsonify({'error': str(e)}), 500
    
    def delete_record(self):
        """
        Delete records from a table.
        
        Request:
            POST /api/orama-db/delete
            Headers: X-Secret-Key: {secret_key}
            Body: {
                "table_name": str,           # Target table name
                "where": {                   # WHERE clause conditions
                    "column": value,
                    ...
                },
                "confirm": bool              # Must be true to confirm deletion
            }
        
        Response:
            200: {"message": "Records deleted successfully", "rows_affected": int}
            400: {"error": str}  # Invalid request
            401: {"error": str}  # Missing secret key
            403: {"error": str}  # Invalid secret key
            500: {"error": str}  # Server error
        """
        is_valid, error_response = self._validate_secret_key()
        if not is_valid:
            return error_response
        
        try:
            request_data = request.get_json()
            table_name = request_data.get('table_name')
            where = request_data.get('where')
            confirm = request_data.get('confirm')
            
            if not table_name or not where:
                return jsonify({'error': 'Missing table_name or where clause'}), 400
            
            if not confirm:
                return jsonify({'error': 'Must set confirm=true to delete records'}), 400
            
            # Build DELETE statement
            where_clause = ' AND '.join([f"{key} = :{key}" for key in where.keys()])
            delete_sql = f"DELETE FROM {table_name} WHERE {where_clause}"
            
            # Execute the DELETE statement
            with self.engine.connect() as conn:
                result = conn.execute(text(delete_sql), where)
                conn.commit()
            
            return jsonify({
                'message': 'Records deleted successfully',
                'rows_affected': result.rowcount
            }), 200
            
        except Exception as e:
            self.db.rollback()
            return jsonify({'error': str(e)}), 500
    
    def execute_query(self):
        """
        Execute a custom SQL query (SELECT statements).
        
        Request:
            POST /api/orama-db/query
            Headers: X-Secret-Key: {secret_key}
            Body: {
                "sql": str,              # SQL query to execute
                "params": dict           # Optional: Query parameters
            }
        
        Response:
            200: {"results": [...], "row_count": int}
            400: {"error": str}  # Invalid request
            401: {"error": str}  # Missing secret key
            403: {"error": str}  # Invalid secret key
            500: {"error": str}  # Server error
        """
        is_valid, error_response = self._validate_secret_key()
        if not is_valid:
            return error_response
        
        try:
            data = request.get_json()
            sql = data.get('sql')
            params = data.get('params', {})
            
            if not sql:
                return jsonify({'error': 'Missing sql query'}), 400
            
            # Execute the query
            with self.engine.connect() as conn:
                result = conn.execute(text(sql), params)
                
                # Fetch results if it's a SELECT query
                if result.returns_rows:
                    rows = result.fetchall()
                    columns = result.keys()
                    
                    # Convert rows to list of dictionaries
                    results = []
                    for row in rows:
                        results.append(dict(zip(columns, row)))
                    
                    return jsonify({
                        'results': results,
                        'row_count': len(results)
                    }), 200
                else:
                    conn.commit()
                    return jsonify({
                        'message': 'Query executed successfully',
                        'rows_affected': result.rowcount
                    }), 200
            
        except Exception as e:
            self.db.rollback()
            return jsonify({'error': str(e)}), 500
    
    def list_tables(self):
        """
        Get a list of all tables in the database.
        
        Request:
            GET /api/orama-db/tables
            Headers: X-Secret-Key: {secret_key}
        
        Response:
            200: {"tables": [str, ...]}
            401: {"error": str}  # Missing secret key
            403: {"error": str}  # Invalid secret key
            500: {"error": str}  # Server error
        """
        is_valid, error_response = self._validate_secret_key()
        if not is_valid:
            return error_response
        
        try:
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            
            return jsonify({'tables': tables}), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def get_table_info(self):
        """
        Get detailed information about a table's structure.
        
        Request:
            GET /api/orama-db/table-info?table_name={table_name}
            Headers: X-Secret-Key: {secret_key}
        
        Response:
            200: {
                "table_name": str,
                "columns": [
                    {
                        "name": str,
                        "type": str,
                        "nullable": bool,
                        "primary_key": bool
                    },
                    ...
                ]
            }
            400: {"error": str}  # Missing table_name
            401: {"error": str}  # Missing secret key
            403: {"error": str}  # Invalid secret key
            500: {"error": str}  # Server error
        """
        is_valid, error_response = self._validate_secret_key()
        if not is_valid:
            return error_response
        
        try:
            table_name = request.args.get('table_name')
            
            if not table_name:
                return jsonify({'error': 'Missing table_name parameter'}), 400
            
            inspector = inspect(self.engine)
            columns = inspector.get_columns(table_name)
            pk_constraint = inspector.get_pk_constraint(table_name)
            primary_keys = pk_constraint.get('constrained_columns', [])
            
            column_info = []
            for col in columns:
                column_info.append({
                    'name': col['name'],
                    'type': str(col['type']),
                    'nullable': col['nullable'],
                    'primary_key': col['name'] in primary_keys
                })
            
            return jsonify({
                'table_name': table_name,
                'columns': column_info
            }), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def add_columns(self):
        """
        Add columns to an existing table if they don't exist.
        
        Request:
            POST /api/orama-db/add-columns
            Headers: X-Secret-Key: {secret_key}
            Body: {
                "table_name": str,           # Target table name
                "columns": [                 # List of column definitions
                    {
                        "name": str,         # Column name
                        "type": str,         # Column type (INTEGER, TEXT, VARCHAR, DATETIME, etc.)
                        "nullable": bool,    # Optional: Can this be NULL? (default: True)
                        "default": any       # Optional: Default value for existing rows
                    },
                    ...
                ]
            }
        
        Response:
            200: {
                "message": "Columns processed successfully",
                "table_name": str,
                "added": [str, ...],         # List of columns that were added
                "skipped": [str, ...]        # List of columns that already existed
            }
            400: {"error": str}  # Invalid request
            401: {"error": str}  # Missing secret key
            403: {"error": str}  # Invalid secret key
            500: {"error": str}  # Server error
        """
        is_valid, error_response = self._validate_secret_key()
        if not is_valid:
            return error_response
        
        try:
            data = request.get_json()
            table_name = data.get('table_name')
            columns = data.get('columns')
            
            if not table_name or not columns:
                return jsonify({'error': 'Missing table_name or columns'}), 400
            
            # Get existing columns in the table
            inspector = inspect(self.engine)
            existing_columns = {col['name'].lower() for col in inspector.get_columns(table_name)}
            
            added_columns = []
            skipped_columns = []
            
            # Process each column
            for col in columns:
                col_name = col.get('name')
                col_type = col.get('type', 'TEXT')
                col_nullable = col.get('nullable', True)
                col_default = col.get('default')
                
                if not col_name:
                    continue
                
                # Check if column already exists (case-insensitive)
                if col_name.lower() in existing_columns:
                    skipped_columns.append(col_name)
                    continue
                
                # Build ALTER TABLE ADD COLUMN statement
                alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"
                
                # Add DEFAULT clause if provided
                if col_default is not None:
                    if isinstance(col_default, str):
                        alter_sql += f" DEFAULT '{col_default}'"
                    else:
                        alter_sql += f" DEFAULT {col_default}"
                
                # Add NOT NULL constraint if specified
                if not col_nullable:
                    alter_sql += " NOT NULL"
                
                # Execute the ALTER TABLE statement
                with self.engine.connect() as conn:
                    conn.execute(text(alter_sql))
                    conn.commit()
                
                added_columns.append(col_name)
            
            return jsonify({
                'message': 'Columns processed successfully',
                'table_name': table_name,
                'added': added_columns,
                'skipped': skipped_columns
            }), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def get_full_backup(self):
        """
        Get a complete backup of the database with all tables and data.
        
        Request:
            GET /api/orama-db/backup
            Headers: X-Secret-Key: {secret_key}
        
        Response:
            200: {
                "backup_date": str,
                "tables": {
                    "table_name": {
                        "schema": [...],
                        "data": [...]
                    },
                    ...
                }
            }
            401: {"error": str}  # Missing secret key
            403: {"error": str}  # Invalid secret key
            500: {"error": str}  # Server error
        """
        is_valid, error_response = self._validate_secret_key()
        if not is_valid:
            return error_response
        
        try:
            from datetime import datetime
            
            inspector = inspect(self.engine)
            table_names = inspector.get_table_names()
            
            backup = {
                'backup_date': datetime.utcnow().isoformat(),
                'tables': {}
            }
            
            # For each table, get schema and data
            for table_name in table_names:
                # Get table schema
                columns = inspector.get_columns(table_name)
                pk_constraint = inspector.get_pk_constraint(table_name)
                primary_keys = pk_constraint.get('constrained_columns', [])
                
                schema = []
                for col in columns:
                    schema.append({
                        'name': col['name'],
                        'type': str(col['type']),
                        'nullable': col['nullable'],
                        'primary_key': col['name'] in primary_keys
                    })
                
                # Get table data
                with self.engine.connect() as conn:
                    result = conn.execute(text(f"SELECT * FROM {table_name}"))
                    rows = result.fetchall()
                    column_names = result.keys()
                    
                    data = []
                    for row in rows:
                        row_dict = {}
                        for i, col_name in enumerate(column_names):
                            value = row[i]
                            # Convert datetime objects to ISO format strings
                            if hasattr(value, 'isoformat'):
                                value = value.isoformat()
                            row_dict[col_name] = value
                        data.append(row_dict)
                
                backup['tables'][table_name] = {
                    'schema': schema,
                    'data': data,
                    'row_count': len(data)
                }
            
            return jsonify(backup), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
