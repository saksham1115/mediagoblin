from sqlalchemy.orm import scoped_session, sessionmaker, object_session


Session = scoped_session(sessionmaker())


def _fix_query_dict(query_dict):
    if '_id' in query_dict:
        query_dict['id'] = query_dict.pop('_id')


class GMGTableBase(object):
    query = Session.query_property()

    @classmethod
    def find(cls, query_dict={}):
        _fix_query_dict(query_dict)
        return cls.query.filter_by(**query_dict)

    @classmethod
    def find_one(cls, query_dict={}):
        _fix_query_dict(query_dict)
        return cls.query.filter_by(**query_dict).first()

    @classmethod
    def one(cls, query_dict):
        return cls.find(query_dict).one()

    def get(self, key):
        return getattr(self, key)

    def save(self, validate = True):
        assert validate
        sess = object_session(self)
        if sess is None:
            sess = Session()
        sess.add(self)
        sess.commit()
