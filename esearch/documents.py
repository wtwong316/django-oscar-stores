from django_elasticsearch_dsl import Document, Integer, Float
from django_elasticsearch_dsl.registries import registry
from oscar.core.loading import get_model
from elasticsearch_dsl.connections import connections

SdfSdu = get_model('sdfs', 'SdfSdu')


@registry.register_document
class SduDocument(Document):

    class Index:
        name = 'sdus'
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0}

    class Django:
        model = SdfSdu
        fields = [
#            'district',
            'size',
            'rent',
            'has_individual_kitchen',
            'has_individual_bath',
            'has_exterior_window'
        ]
