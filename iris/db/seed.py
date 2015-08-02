import logging
from .base import *

log = logging.getLogger(__name__)

class Seed(BaseModel):
    id = IntegerField(primary_key=True)

    ip = CharField(max_length=15)
    port = IntegerField()

