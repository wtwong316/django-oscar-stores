# coding=utf-8
import factory

from oscar.core.loading import get_model

__all__ = [
    'SduClassFactory', 'SduFactory',
    'CategoryFactory', 'SduCategoryFactory',
    'SduAttributeFactory', 'AttributeOptionGroupFactory',
    'OptionFactory', 'AttributeOptionFactory',
    'SduAttributeValueFactory', 'SduReviewFactory',
    'SduImageFactory'
]


class SduClassFactory(factory.django.DjangoModelFactory):
    name = "Books"
    #requires_shipping = True
    #track_stock = True

    class Meta:
        model = get_model('catalogue', 'SduClass')


class SduFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_model('catalogue', 'Sdu')

    structure = Meta.model.STANDALONE
    upc = factory.Sequence(lambda n: '978080213020%d' % n)
    title = "A confederacy of dunces"
    sdu_class = factory.SubFactory(SduClassFactory)

    stockrecords = factory.RelatedFactory(
        'oscar.test.factories.StockRecordFactory', 'sdu')
    categories = factory.RelatedFactory(
        'oscar.test.factories.SduCategoryFactory', 'sdu')


class CategoryFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: 'Category %d' % n)

    # Very naive handling of treebeard node fields. Works though!
    depth = 1
    path = factory.Sequence(lambda n: '%04d' % n)

    class Meta:
        model = get_model('catalogue', 'Category')


class SduCategoryFactory(factory.django.DjangoModelFactory):
    category = factory.SubFactory(CategoryFactory)

    class Meta:
        model = get_model('catalogue', 'SduCategory')


class SduAttributeFactory(factory.django.DjangoModelFactory):
    code = name = 'weight'
    sdu_class = factory.SubFactory(SduClassFactory)
    type = "float"

    class Meta:
        model = get_model('catalogue', 'SduAttribute')


class OptionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_model('catalogue', 'Option')

    name = 'example option'
    code = 'example'
    type = Meta.model.TEXT
    required = False


class AttributeOptionFactory(factory.django.DjangoModelFactory):
    # Ideally we'd get_or_create a AttributeOptionGroup here, but I'm not
    # aware of how to not create a unique option group for each call of the
    # factory

    option = factory.Sequence(lambda n: 'Option %d' % n)

    class Meta:
        model = get_model('catalogue', 'AttributeOption')


class AttributeOptionGroupFactory(factory.django.DjangoModelFactory):
    name = 'Grüppchen'

    class Meta:
        model = get_model('catalogue', 'AttributeOptionGroup')


class SduAttributeValueFactory(factory.django.DjangoModelFactory):
    attribute = factory.SubFactory(SduAttributeFactory)
    sdu = factory.SubFactory(SduFactory)

    class Meta:
        model = get_model('catalogue', 'SduAttributeValue')


class SduReviewFactory(factory.django.DjangoModelFactory):
    score = 5
    sdu = factory.SubFactory(SduFactory, stockrecords=[])

    class Meta:
        model = get_model('reviews', 'SduReview')


class SduImageFactory(factory.django.DjangoModelFactory):
    sdu = factory.SubFactory(SduFactory, stockrecords=[])
    original = factory.django.ImageField(width=100, height=200, filename='test_image.jpg')

    class Meta:
        model = get_model('catalogue', 'SduImage')
