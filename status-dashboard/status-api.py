# location /monitoring/ {
# 	proxy_pass http://127.0.0.1:5000/;
# 	proxy_set_header Host $host;
# 	proxy_set_header X-Real-IP $remote_addr;
# 	proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
# 	proxy_set_header X-Forwarded-Proto $scheme;
# }
from flask import Flask, jsonify, request
import subprocess
import configparser
import os

app = Flask(__name__)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'services.config')

# Read services from config
def read_services():
	config = configparser.ConfigParser()
	config.read(CONFIG_PATH)
	services = []
	for section in config.sections():
		service = dict(config.items(section))
		service['name'] = section
		services.append(service)
	return services


# Enum-like status values
STATUS_RUNNING = 'running'
STATUS_ERROR = 'error'
STATUS_FAILED = 'failed'
STATUS_INACTIVE = 'inactive'
STATUS_WARNING = 'warning'

def get_log_status(service):
	log_path = service.get('path')
	grep = service.get('grep')
	stype = service.get('type', 'log')
	if not log_path or not os.path.exists(log_path):
		return {'status': STATUS_ERROR, 'description': 'Log file not found', 'type': stype}
	try:
		if grep:
			result = subprocess.run(['grep', grep, log_path], capture_output=True, text=True)
			line = result.stdout.strip().split('\n')[-1] if result.stdout else 'No match'
		else:
			with open(log_path, 'r') as f:
				lines = f.readlines()
				line = lines[-1].strip() if lines else 'Log empty'
		status = STATUS_RUNNING if line and line != 'No match' and line != 'Log empty' else STATUS_INACTIVE
		return {'status': status, 'description': line, 'type': stype}
	except Exception as e:
		return {'status': STATUS_ERROR, 'description': str(e), 'type': stype}

def get_systemd_status(service):
	name = service.get('service')
	stype = service.get('type', 'systemd')
	if not name:
		return {'status': STATUS_ERROR, 'description': 'No service name', 'type': stype}
	try:
		result = subprocess.run(['systemctl', 'is-active', name], capture_output=True, text=True)
		status_raw = result.stdout.strip()
		desc_result = subprocess.run(['systemctl', 'status', name, '--no-pager'], capture_output=True, text=True)
		desc = desc_result.stdout.strip().split('\n')[2] if desc_result.stdout else ''
		if status_raw == 'active':
			status = STATUS_RUNNING
		elif status_raw == 'inactive':
			status = STATUS_INACTIVE
		elif status_raw == 'failed':
			status = STATUS_FAILED
		else:
			status = STATUS_ERROR
		return {'status': status, 'description': desc, 'type': stype}
	except Exception as e:
		return {'status': STATUS_ERROR, 'description': str(e), 'type': stype}

def get_docker_status(service):
	name = service.get('container')
	stype = service.get('type', 'docker')
	if not name:
		return {'status': STATUS_ERROR, 'description': 'No container name', 'type': stype}
	try:
		result = subprocess.run(['docker', 'ps', '--filter', f'name={name}', '--format', '{{.Status}}'], capture_output=True, text=True)
		status_raw = result.stdout.strip()
		desc = status_raw if status_raw else 'Not running'
		if status_raw.startswith('Up'):
			status = STATUS_RUNNING
		elif status_raw == '':
			status = STATUS_INACTIVE
		elif 'Exited' in status_raw or 'Dead' in status_raw:
			status = STATUS_FAILED
		else:
			status = STATUS_ERROR
		return {'status': status, 'description': desc, 'type': stype}
	except Exception as e:
		return {'status': STATUS_ERROR, 'description': str(e), 'type': stype}

def get_service_status(service):
	stype = service.get('type')
	if stype == 'log':
		return get_log_status(service)
	elif stype == 'systemd':
		return get_systemd_status(service)
	elif stype == 'docker':
		return get_docker_status(service)
	else:
		return {'status': STATUS_ERROR, 'description': 'Unknown type'}


@app.route('/api/status', methods=['GET'])
def api_status():
	services = read_services()
	result = {}
	for service in services:
		result[service['name']] = get_service_status(service)
	return jsonify(result)

@app.route('/api/status/<service_name>', methods=['GET'])
def api_status_service(service_name):
	services = read_services()
	for service in services:
		if service['name'] == service_name:
			return jsonify({service_name: get_service_status(service)})
	return jsonify({'error': 'Service not found'}), 404

@app.route('/', methods=['GET'])
def api_root():
	return jsonify({'message': 'Welcome to the Service Status API'})

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000)
