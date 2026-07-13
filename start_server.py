"""Ultra API Server startup script."""
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('Ultra')

sys.path.insert(0, 'E:/Prometheus-Ultra/src')

from prometheus_ultra.services.api_server import UltraAPIServer
from prometheus_ultra import Omega

logger.info('Initializing Omega...')
o = Omega()
logger.info('Omega ready: %d nodes, %d edges', o.store.get_node_count(), o.store.get_edge_count())

server = UltraAPIServer(host='0.0.0.0', port=9200)
logger.info('Starting API server on port 9200...')
logger.info('Dashboard: http://localhost:9200/dashboard')
logger.info('API docs: http://localhost:9200/docs')
server.start(omega=o, background=False)
