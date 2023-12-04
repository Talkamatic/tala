class AbstractServiceWrapper(object):
    def __init__(self):
        super(AbstractServiceWrapper, self).__init__()
        self._session_data = {}

    def query(self, question, parameters, min_results, max_results, session, context):
        raise NotImplementedError()

    def perform(self, action_name, parameters, session, context):
        raise NotImplementedError()

    def validate(self, validator_name, parameters, session, context):
        raise NotImplementedError()

    @property
    def session_data(self):
        return self._session_data

    @session_data.setter
    def session_data(self, new_session_data):
        self._session_data = new_session_data
