class EventNotificationException(Exception):
    pass


class EventNotification(object):
    STARTED = "started"
    ENDED = "ended"
    SUPPORTED_STATUSES = [STARTED, ENDED]

    def __init__(self, action, status, parameters):
        if status not in self.SUPPORTED_STATUSES:
            raise EventNotificationException(
                "Expected status to be one of %s but got '%s'." % (self.SUPPORTED_STATUSES, status)
            )
        self._action = action
        self._status = status
        self._parameters = parameters

    @property
    def action(self):
        return self._action

    @property
    def status(self):
        return self._status

    @property
    def parameters(self):
        return self._parameters

    def __eq__(self, other):
        return other.action == self.action and other.status == self.status and other.parameters == self.parameters

    def __ne__(self, other):
        return not (self == other)

    def __str__(self):
        return "EventNotification(%r, %r, %r)" % (self._action, self._status, self._parameters)
