from oscar.apps.analytics.abstract_models import (
    AbstractSduRecord, AbstractUserSduView,
    AbstractUserRecord, AbstractUserSearch)
from oscar.core.loading import is_model_registered

__all__ = []


if not is_model_registered('analytics', 'SduRecord'):
    class SduRecord(AbstractSduRecord):
        pass

    __all__.append('SduRecord')


if not is_model_registered('analytics', 'UserRecord'):
    class UserRecord(AbstractUserRecord):
        pass

    __all__.append('UserRecord')


if not is_model_registered('analytics', 'UserSduView'):
    class UserSduView(AbstractUserSduView):
        pass

    __all__.append('UserSduView')


if not is_model_registered('analytics', 'UserSearch'):
    class UserSearch(AbstractUserSearch):
        pass

    __all__.append('UserSearch')
