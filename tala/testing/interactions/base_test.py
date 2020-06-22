class BaseInteractionTest(object):
    @property
    def filename(self):
        raise NotImplementedError("This property needs to be implemented in a subclass")

    @property
    def name(self):
        raise NotImplementedError("This property needs to be implemented in a subclass")

    @property
    def turns(self):
        raise NotImplementedError("This property needs to be implemented in a subclass")
