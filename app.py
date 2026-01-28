from flask import Flask, render_template, jsonify, request
import psycopg2
import socket
from datetime import datetime
import os

app = Flask(__name__)

# Default PostgreSQL connection details
DEFAULT_HOST = os.getenv('PG_HOST', 'pg-1e8c0fd-stan-dmitriev-test.h.aivencloud.com')
DEFAULT_PORT = int(os.getenv('PG_PORT', '19030'))
DEFAULT_DATABASE = os.getenv('PG_DATABASE', 'defaultdb')
DEFAULT_USER = os.getenv('PG_USER', 'avnadmin')

@app.route('/')
def index():
    return render_template('index.html', 
                         default_host=DEFAULT_HOST, 
                         default_port=DEFAULT_PORT,
                         default_database=DEFAULT_DATABASE,
                         default_user=DEFAULT_USER)

@app.route('/api/check', methods=['POST'])
def check_connection():
    # Get credentials from request
    data = request.get_json() or {}
    
    pg_host = data.get('host', DEFAULT_HOST)
    try:
        pg_port = int(data.get('port', DEFAULT_PORT))
    except (ValueError, TypeError):
        pg_port = DEFAULT_PORT
    pg_database = data.get('database', DEFAULT_DATABASE)
    pg_user = data.get('user', DEFAULT_USER)
    pg_password = data.get('password', '')
    
    # Validate required fields
    if not pg_host:
        return jsonify({'error': 'Host is required'}), 400
    if not pg_user:
        return jsonify({'error': 'User is required'}), 400
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'host': pg_host,
        'port': pg_port,
        'tests': []
    }
    
    # Test 1: TCP Socket Connection
    socket_test = {
        'name': 'TCP Socket Connection',
        'status': 'unknown',
        'message': '',
        'duration_ms': 0
    }
    try:
        start_time = datetime.now()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((pg_host, pg_port))
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() * 1000
        
        if result == 0:
            socket_test['status'] = 'success'
            socket_test['message'] = f'Port {pg_port} is reachable'
            socket_test['duration_ms'] = round(duration, 2)
            sock.close()
        else:
            socket_test['status'] = 'blocked'
            socket_test['message'] = f'Port {pg_port} is blocked or unreachable (error code: {result})'
            socket_test['duration_ms'] = round(duration, 2)
    except socket.timeout:
        socket_test['status'] = 'blocked'
        socket_test['message'] = f'Connection timeout - port {pg_port} appears to be blocked by firewall'
    except Exception as e:
        socket_test['status'] = 'error'
        socket_test['message'] = f'Error: {str(e)}'
    
    results['tests'].append(socket_test)
    
    # Test 2: PostgreSQL Connection (only if socket test succeeded)
    pg_test = {
        'name': 'PostgreSQL Authentication',
        'status': 'unknown',
        'message': '',
        'duration_ms': 0
    }
    
    if socket_test['status'] == 'success':
        try:
            start_time = datetime.now()
            conn = psycopg2.connect(
                host=pg_host,
                port=pg_port,
                database=pg_database,
                user=pg_user,
                password=pg_password,
                connect_timeout=5
            )
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds() * 1000
            
            # Test query
            cursor = conn.cursor()
            cursor.execute('SELECT version();')
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            pg_test['status'] = 'success'
            pg_test['message'] = f'Successfully connected to PostgreSQL. Version: {version[:50]}...'
            pg_test['duration_ms'] = round(duration, 2)
        except psycopg2.OperationalError as e:
            pg_test['status'] = 'error'
            pg_test['message'] = f'PostgreSQL connection failed: {str(e)}'
        except Exception as e:
            pg_test['status'] = 'error'
            pg_test['message'] = f'Unexpected error: {str(e)}'
    else:
        pg_test['status'] = 'skipped'
        pg_test['message'] = 'Skipped because TCP socket connection failed'
    
    results['tests'].append(pg_test)
    
    # Determine overall status
    if socket_test['status'] == 'blocked':
        results['overall_status'] = 'blocked'
        results['overall_message'] = 'Firewall is blocking the connection'
    elif socket_test['status'] == 'success' and pg_test['status'] == 'success':
        results['overall_status'] = 'success'
        results['overall_message'] = 'Connection successful'
    elif socket_test['status'] == 'success':
        results['overall_status'] = 'partial'
        results['overall_message'] = 'Port is reachable but PostgreSQL connection failed'
    else:
        results['overall_status'] = 'error'
        results['overall_message'] = 'Connection test failed'
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
