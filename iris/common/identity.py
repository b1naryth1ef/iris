import uuid, hashlib, json, logging
import libnacl.public

log = logging.getLogger(__name__)

class IdentityMixin(object):
    """
    IdentityMixin provides a mixin class that helps with encrypting and
    signing data.
    """

    def from_identity(self, other):
        self.public_key = other.public_key
        self.secret_key = other.secret_key
        self.sign_key = other.sign_key

    def sign(self, data):
        signer = libnacl.sign.Signer(self.secret_key[:32])
        return signer.signature(data)

    def verify(self, sig, data):
        veri = libnacl.sign.Verifier(str(self.sign_key).encode('hex'))
        return veri.verify(str(sig) + data)

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
    def __init__(self, public_key=None, secret_key=None, sign_key=None):
        self.public_key = public_key
        self.secret_key = secret_key
        self.sign_key = sign_key
    
    @classmethod
    def create(cls):
        pk, sk = cls.create_keypair()
        sgnk = libnacl.sign.Signer(sk[:32]).vk
        return cls(pk, sk, sgnk)
