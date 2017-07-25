t = """
frontend {name}_admin_cluster_frontend_https
        bind 172.16.60.16:{port} ssl crt /etc/ssl/aio/aio.pem
        http-request set-header X-Forwarded-Proto https
        default_backend {name}_admin_cluster_backend

backend {name}_admin_cluster_backend
        server controller1 127.0.0.1:{port} check
"""

services = {
    'ec2': '8773',
    'orchestration': '8004',
    'volumev2': '8776',
    'image': '9292',
    'volume': '8776',
    'cloudformation': '8000',
    'compute': '8774',
    'placement': '8778',
    'network': '9696',
    'compute_legacy': '8774',
    'identity': '5000'
}

# for name, port in services.items():
#     d = {'name': name, 'port': port}
#     print t.format(**d)

ports = []
for name, port in services.items():
    ports.append('dst port {}'.format(port))
print ' or '.join(ports)
