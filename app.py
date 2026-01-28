from flask import Flask, render_template, jsonify
import psycopg2
import socket
from datetime import datetime
import os

app = Flask(__name__)

# PostgreSQL connection details
PG_HOST = os.getenv('PG_HOST', 'pg-1e8c0fd-stan-dmitriev-test.h.aivencloud.com')
PG_PORT = int(os.getenv('PG_PORT', '19030'))
PG_DATABASE = os.getenv('PG_DATABASE', 'defaultdb')
PG_USER = os.getenv('PG_USER', 'avnadmin')
PG_PASSWORD = os.getenv('PG_PASSWORD', '')

@app.route('/')
def index():
    return render_template('index.html', host=PG_HOST, port=PG_PORT)

@app.route('/api/check')
def check_connection():
    results = {
        'timestamp': datetime.now().isoformat(),
        'host': PG_HOST,
        'port': PG_PORT,
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
        result = sock.connect_ex((PG_HOST, PG_PORT))
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() * 1000
        
        if result == 0:
            socket_test['status'] = 'success'
            socket_test['message'] = f'Port {PG_PORT} is reachable'
            socket_test['duration_ms'] = round(duration, 2)
            sock.close()
        else:
            socket_test['status'] = 'blocked'
            socket_test['message'] = f'Port {PG_PORT} is blocked or unreachable (error code: {result})'
            socket_test['duration_ms'] = round(duration, 2)
    except socket.timeout:
        socket_test['status'] = 'blocked'
        socket_test['message'] = f'Connection timeout - port {PG_PORT} appears to be blocked by firewall'
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
                host=PG_HOST,
                port=PG_PORT,
                database=PG_DATABASE,
                user=PG_USER,
                password=PG_PASSWORD,
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
