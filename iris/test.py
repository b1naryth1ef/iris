from common import log
from db.base import init_db
init_db('/tmp/iris-04a089a8069e4011a6c614e24fa6f78e.db')
from db.mesh import Mesh
Mesh.new_mesh()
