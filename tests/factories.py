import factory
from oscar.core.loading import get_model
from oscar.test.factories import CountryFactory


class SdfFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_model('sdfs', 'Sdf')


class SdfAddressFactory(factory.django.DjangoModelFactory):
    country = factory.SubFactory(CountryFactory)

    class Meta:
        model = get_model('sdfs', 'SdfAddress')


class SdfGroupFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = get_model('sdfs', 'SdfGroup')


class SdfStockFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = get_model('sdfs', 'SdfStock')
