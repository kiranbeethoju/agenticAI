"""
Cassandra Database Module
Replaces TinyDB with Cassandra for persistent storage
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from cassandra.auth import PlainTextAuthProvider


class CassandraDB:
    def __init__(self, contact_points=['localhost'], port=9042, username='cassandra', password='cassandra', keyspace='agent_system'):
        self.contact_points = contact_points
        self.port = port
        self.username = username
        self.password = password
        self.keyspace = keyspace
        self.cluster = None
        self.session = None
        self.connect()
        self.create_keyspace()
        self.create_tables()
    
    def connect(self):
        """Connect to Cassandra cluster"""
        try:
            auth_provider = PlainTextAuthProvider(username=self.username, password=self.password)
            self.cluster = Cluster(
                contact_points=self.contact_points,
                port=self.port,
                auth_provider=auth_provider
            )
            self.session = self.cluster.connect()
            print(f"Connected to Cassandra at {self.contact_points}:{self.port}")
        except Exception as e:
            print(f"Failed to connect to Cassandra: {e}")
            raise
    
    def create_keyspace(self):
        """Create keyspace if it doesn't exist"""
        try:
            query = f"""
            CREATE KEYSPACE IF NOT EXISTS {self.keyspace}
            WITH REPLICATION = {{ 'class' : 'SimpleStrategy', 'replication_factor' : 1 }}
            """
            self.session.execute(query)
            self.session.set_keyspace(self.keyspace)
            print(f"Keyspace '{self.keyspace}' ready")
        except Exception as e:
            print(f"Failed to create keyspace: {e}")
            raise
    
    def create_tables(self):
        """Create all necessary tables"""
        # Flows table
        flows_query = """
        CREATE TABLE IF NOT EXISTS flows (
            flow_id text PRIMARY KEY,
            name text,
            steps text,
            config text,
            updated_at timestamp
        )
        """
        self.session.execute(flows_query)
        
        # Logs table
        logs_query = """
        CREATE TABLE IF NOT EXISTS logs (
            id uuid PRIMARY KEY,
            timestamp timestamp,
            session_id text,
            type text,
            message text,
            response text,
            full_context text,
            workflow_id text,
            run_id text,
            step_index int,
            step_name text,
            model text,
            latency float,
            input_preview text,
            output_preview text
        )
        """
        self.session.execute(logs_query)
        
        # Workflow runs table
        runs_query = """
        CREATE TABLE IF NOT EXISTS workflow_runs (
            run_id text PRIMARY KEY,
            workflow_id text,
            flow_name text,
            input_column text,
            status text,
            started_at timestamp,
            completed_at timestamp,
            results text,
            count int,
            error text
        )
        """
        self.session.execute(runs_query)
        
        # Telemetry table
        telemetry_query = """
        CREATE TABLE IF NOT EXISTS telemetry (
            id uuid PRIMARY KEY,
            timestamp timestamp,
            session_id text,
            type text,
            workflow_id text,
            run_id text,
            step_index int,
            step_name text,
            model text,
            latency float,
            input_preview text,
            output_preview text
        )
        """
        self.session.execute(telemetry_query)
        
        # Create indexes for better query performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_logs_session_id ON logs (session_id)",
            "CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs (timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_logs_workflow_id ON logs (workflow_id)",
            "CREATE INDEX IF NOT EXISTS idx_logs_run_id ON logs (run_id)",
            "CREATE INDEX IF NOT EXISTS idx_runs_workflow_id ON workflow_runs (workflow_id)",
            "CREATE INDEX IF NOT EXISTS idx_telemetry_session_id ON telemetry (session_id)",
            "CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry (timestamp)"
        ]
        
        for index_query in indexes:
            self.session.execute(index_query)
        
        print("All tables created successfully")
    
    def table(self, table_name):
        """Return a table handler object"""
        return TableHandler(self.session, table_name)
    
    def close(self):
        """Close Cassandra connection"""
        if self.cluster:
            self.cluster.shutdown()


class TableHandler:
    """Handler for individual table operations"""
    
    def __init__(self, session, table_name):
        self.session = session
        self.table_name = table_name
    
    def insert(self, data: Dict[str, Any]) -> str:
        """Insert a record into the table"""
        if self.table_name == 'flows':
            return self._insert_flow(data)
        elif self.table_name == 'logs':
            return self._insert_log(data)
        elif self.table_name == 'workflow_runs':
            return self._insert_run(data)
        elif self.table_name == 'telemetry':
            return self._insert_telemetry(data)
        else:
            raise ValueError(f"Unknown table: {self.table_name}")
    
    def _insert_flow(self, data: Dict[str, Any]) -> str:
        """Insert flow record"""
        flow_id = data.get('flow_id')
        query = """
        INSERT INTO flows (flow_id, name, steps, config, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """
        prepared = self.session.prepare(query)
        self.session.execute(prepared, [
            flow_id,
            data.get('name', ''),
            json.dumps(data.get('steps', [])),
            json.dumps(data.get('config', {})),
            datetime.now()
        ])
        return flow_id
    
    def _insert_log(self, data: Dict[str, Any]) -> str:
        """Insert log record"""
        record_id = uuid.uuid4()
        query = """
        INSERT INTO logs (id, timestamp, session_id, type, message, response, full_context, 
                         workflow_id, run_id, step_index, step_name, model, latency, 
                         input_preview, output_preview)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        prepared = self.session.prepare(query)
        
        # Handle timestamp - convert string to datetime if needed
        timestamp = data.get('timestamp', datetime.now())
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                timestamp = datetime.now()
        
        self.session.execute(prepared, [
            record_id,
            timestamp,
            data.get('session_id', ''),
            data.get('type', ''),
            data.get('message', ''),
            json.dumps(data.get('response', {})),
            json.dumps(data.get('full_context', {})),
            data.get('workflow_id', ''),
            data.get('run_id', ''),
            data.get('step_index'),
            data.get('step_name', ''),
            data.get('model', ''),
            data.get('latency'),
            data.get('input_preview', ''),
            data.get('output_preview', '')
        ])
        return str(record_id)
    
    def _insert_run(self, data: Dict[str, Any]) -> str:
        """Insert workflow run record"""
        run_id = data.get('run_id')
        query = """
        INSERT INTO workflow_runs (run_id, workflow_id, flow_name, input_column, status, 
                                  started_at, completed_at, results, count, error)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        prepared = self.session.prepare(query)
        
        # Handle datetime fields
        started_at = data.get('started_at')
        if isinstance(started_at, str):
            try:
                started_at = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            except:
                started_at = datetime.now()
        
        completed_at = data.get('completed_at')
        if isinstance(completed_at, str):
            try:
                completed_at = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
            except:
                completed_at = None
        
        self.session.execute(prepared, [
            run_id,
            data.get('workflow_id', ''),
            data.get('flow_name', ''),
            data.get('input_column', ''),
            data.get('status', ''),
            started_at,
            completed_at,
            json.dumps(data.get('results', [])),
            data.get('count', 0),
            data.get('error', '')
        ])
        return run_id
    
    def _insert_telemetry(self, data: Dict[str, Any]) -> str:
        """Insert telemetry record"""
        record_id = uuid.uuid4()
        query = """
        INSERT INTO telemetry (id, timestamp, session_id, type, workflow_id, run_id, 
                              step_index, step_name, model, latency, input_preview, output_preview)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        prepared = self.session.prepare(query)
        
        # Handle timestamp - convert string to datetime if needed
        timestamp = data.get('timestamp', datetime.now())
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                timestamp = datetime.now()
        
        self.session.execute(prepared, [
            record_id,
            timestamp,
            data.get('session_id', ''),
            data.get('type', ''),
            data.get('workflow_id', ''),
            data.get('run_id', ''),
            data.get('step_index'),
            data.get('step_name', ''),
            data.get('model', ''),
            data.get('latency'),
            data.get('input_preview', ''),
            data.get('output_preview', '')
        ])
        return str(record_id)
    
    def all(self) -> List[Dict[str, Any]]:
        """Get all records from table"""
        if self.table_name == 'flows':
            query = "SELECT * FROM flows"
            rows = self.session.execute(query)
            return [self._convert_flow_row(row) for row in rows]
        elif self.table_name == 'logs':
            # For logs, we'll get recent records without ORDER BY
            query = "SELECT * FROM logs LIMIT 1000"
            rows = self.session.execute(query)
            logs_data = [self._convert_log_row(row) for row in rows]
            # Sort in Python instead of Cassandra
            logs_data.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return logs_data
        elif self.table_name == 'workflow_runs':
            query = "SELECT * FROM workflow_runs"
            rows = self.session.execute(query)
            return [self._convert_run_row(row) for row in rows]
        elif self.table_name == 'telemetry':
            # For telemetry, we'll get recent records without ORDER BY
            query = "SELECT * FROM telemetry LIMIT 1000"
            rows = self.session.execute(query)
            telemetry_data = [self._convert_telemetry_row(row) for row in rows]
            # Sort in Python instead of Cassandra
            telemetry_data.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return telemetry_data
        else:
            return []
    
    def _convert_flow_row(self, row) -> Dict[str, Any]:
        """Convert flow row to dict format compatible with TinyDB"""
        return {
            'flow_id': row.flow_id,
            'name': row.name,
            'steps': json.loads(row.steps) if row.steps else [],
            'config': json.loads(row.config) if row.config else {},
            'updated_at': row.updated_at.isoformat() if row.updated_at else None
        }
    
    def _convert_log_row(self, row) -> Dict[str, Any]:
        """Convert log row to dict format compatible with TinyDB"""
        return {
            'id': str(row.id),
            'timestamp': row.timestamp.isoformat() if row.timestamp else None,
            'session_id': row.session_id,
            'type': row.type,
            'message': row.message,
            'response': json.loads(row.response) if row.response else {},
            'full_context': json.loads(row.full_context) if row.full_context else {},
            'workflow_id': row.workflow_id,
            'run_id': row.run_id,
            'step_index': row.step_index,
            'step_name': row.step_name,
            'model': row.model,
            'latency': row.latency,
            'input_preview': row.input_preview,
            'output_preview': row.output_preview
        }
    
    def _convert_run_row(self, row) -> Dict[str, Any]:
        """Convert run row to dict format compatible with TinyDB"""
        return {
            'run_id': row.run_id,
            'workflow_id': row.workflow_id,
            'flow_name': row.flow_name,
            'input_column': row.input_column,
            'status': row.status,
            'started_at': row.started_at.isoformat() if row.started_at else None,
            'completed_at': row.completed_at.isoformat() if row.completed_at else None,
            'results': json.loads(row.results) if row.results else [],
            'count': row.count,
            'error': row.error
        }
    
    def _convert_telemetry_row(self, row) -> Dict[str, Any]:
        """Convert telemetry row to dict format compatible with TinyDB"""
        return {
            'id': str(row.id),
            'timestamp': row.timestamp.isoformat() if row.timestamp else None,
            'session_id': row.session_id,
            'type': row.type,
            'workflow_id': row.workflow_id,
            'run_id': row.run_id,
            'step_index': row.step_index,
            'step_name': row.step_name,
            'model': row.model,
            'latency': row.latency,
            'input_preview': row.input_preview,
            'output_preview': row.output_preview
        }
    
    def get(self, condition=None) -> Optional[Dict[str, Any]]:
        """Get a single record matching condition"""
        # This is a simplified version - in production you'd want better query handling
        if self.table_name == 'workflow_runs' and condition and 'run_id' in str(condition):
            # Extract run_id from condition
            run_id = str(condition).split('==')[1].strip().strip("'\"")
            query = "SELECT * FROM workflow_runs WHERE run_id = ? LIMIT 1"
            prepared = self.session.prepare(query)
            rows = self.session.execute(prepared, [run_id])
            for row in rows:
                return self._convert_run_row(row)
        return None
    
    def upsert(self, data: Dict[str, Any]) -> str:
        """Insert or update a record"""
        if self.table_name == 'flows':
            return self._insert_flow(data)  # Cassandra INSERT is upsert by default
        else:
            return self.insert(data)
    
    def remove(self, condition=None):
        """Remove records matching condition"""
        if self.table_name == 'flows' and condition and 'flow_id' in str(condition):
            # Extract flow_id from condition
            flow_id = str(condition).split('==')[1].strip().strip("'\"")
            query = "DELETE FROM flows WHERE flow_id = ?"
            prepared = self.session.prepare(query)
            self.session.execute(prepared, [flow_id])


# Global database instance
db = CassandraDB()
flows_table = db.table('flows')
logs_table = db.table('logs')
runs_table = db.table('workflow_runs')
telemetry_table = db.table('telemetry')
