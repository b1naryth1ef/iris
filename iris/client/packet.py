
class PacketWrapper(object):
    def __init__(self, parent, obj, outer):
        for field in obj.DESCRIPTOR.fields:
            setattr(self, field.name, getattr(obj, field.name))
        self.inner = obj
        self.outer = outer
        self.parent = parent

    def respond(self, *args, **kwargs):
        kwargs['ticket'] = self.outer.ticket
        self.parent.send(*args, **kwargs)

