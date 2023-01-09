from oscar.core.loading import is_model_registered

from . import abstract_models

__all__ = []


if not is_model_registered('sdfs', 'SdfAddress'):
    class SdfAddress(abstract_models.SdfAddress):
        pass

    __all__.append('SdfAddress')


if not is_model_registered('sdfs', 'SdfGroup'):
    class SdfGroup(abstract_models.SdfGroup):
        pass

    __all__.append('SdfGroup')


if not is_model_registered('sdfs', 'Sdf'):
    class Sdf(abstract_models.Sdf):
        pass

    __all__.append('Sdf')


#if not is_model_registered('sdfs', 'OpeningPeriod'):
#    class OpeningPeriod(abstract_models.OpeningPeriod):
#        pass

#    __all__.append('OpeningPeriod')


if not is_model_registered('sdfs', 'SdfStock'):
    class SdfStock(abstract_models.SdfStock):
        pass

    __all__.append('SdfStock')
