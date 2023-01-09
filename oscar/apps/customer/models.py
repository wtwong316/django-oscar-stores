from oscar.apps.customer import abstract_models
from oscar.core.loading import is_model_registered

__all__ = []


if not is_model_registered('customer', 'SduAlert'):
    class SduAlert(abstract_models.AbstractSduAlert):
        pass

    __all__.append('SduAlert')
