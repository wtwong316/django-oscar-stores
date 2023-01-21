from oscar.apps.renter import abstract_models
from oscar.core.loading import is_model_registered

__all__ = []


if not is_model_registered('renter', 'ProductAlert'):
    class ProductAlert(abstract_models.AbstractProductAlert):
        pass

    __all__.append('ProductAlert')
