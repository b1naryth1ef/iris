import uuid, hashlib, json, logging
import libnacl.public

log = logging.getLogger(__name__)

class IdentityMixin(object):
    """
    Adds methods to a class that enable it to encrypt/decrypt data.
    """
    def encrypt(self, data, other):
        box = libnacl.public.Box(str(self.secret_key), str(other.public_key))
        return box.encrypt(data)

    def decrypt(self, data, other):
        box = libnacl.public.Box(str(self.secret_key), str(other.public_key))
        return box.decrypt(data)

    def get_identity_dict(self, private=False):
        base = {
            "pk": self.public_key.encode('hex')
        }

        if private:
            base['sk'] = self.secret_key.encode('hex')

        return base

    @classmethod
    def create_keypair(cls):
        log.debug("Generating new keypair")
        keypair = libnacl.public.SecretKey()
        return keypair.pk, keypair.sk

class Identity(IdentityMixin):
    def __init__(self, public_key=None, secret_key=None):
        self.public_key = public_key
        self.secret_key = secret_key
    
    @classmethod
    def create(cls):
        return cls(*cls.create_keypair())
