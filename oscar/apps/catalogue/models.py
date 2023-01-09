"""
Vanilla sdu models
"""
from oscar.apps.catalogue.abstract_models import *  # noqa
from oscar.core.loading import is_model_registered

__all__ = ['SduAttributesContainer']


if not is_model_registered('catalogue', 'SduClass'):
    class SduClass(AbstractSduClass):
        pass

    __all__.append('SduClass')


if not is_model_registered('catalogue', 'Category'):
    class Category(AbstractCategory):
        pass

    __all__.append('Category')


if not is_model_registered('catalogue', 'SduCategory'):
    class SduCategory(AbstractSduCategory):
        pass

    __all__.append('SduCategory')


if not is_model_registered('catalogue', 'Sdu'):
    class Sdu(AbstractSdu):
        pass

    __all__.append('Sdu')


if not is_model_registered('catalogue', 'SduRecommendation'):
    class SduRecommendation(AbstractSduRecommendation):
        pass

    __all__.append('SduRecommendation')


if not is_model_registered('catalogue', 'SduAttribute'):
    class SduAttribute(AbstractSduAttribute):
        pass

    __all__.append('SduAttribute')


if not is_model_registered('catalogue', 'SduAttributeValue'):
    class SduAttributeValue(AbstractSduAttributeValue):
        pass

    __all__.append('SduAttributeValue')


if not is_model_registered('catalogue', 'AttributeOptionGroup'):
    class AttributeOptionGroup(AbstractAttributeOptionGroup):
        pass

    __all__.append('AttributeOptionGroup')


if not is_model_registered('catalogue', 'AttributeOption'):
    class AttributeOption(AbstractAttributeOption):
        pass

    __all__.append('AttributeOption')


if not is_model_registered('catalogue', 'Option'):
    class Option(AbstractOption):
        pass

    __all__.append('Option')


if not is_model_registered('catalogue', 'SduImage'):
    class SduImage(AbstractSduImage):
        pass

    __all__.append('SduImage')
