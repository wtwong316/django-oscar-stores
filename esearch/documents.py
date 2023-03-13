from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from oscar.core.loading import get_model
from elasticsearch_dsl import Q
SdfSdu = get_model('sdfs', 'SdfSdu')
Sdf = get_model('sdfs', 'Sdf')


@registry.register_document
class SduDocument(Document):
    sdfId_id = fields.IntegerField()

    class Index:
        name = 'sdus'
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0}

    class Django:
        model = SdfSdu
        fields = [
            'district',
            'building',
            'street',
            'size',
            'rent',
            'has_individual_kitchen',
            'has_individual_bath',
            'has_exterior_window'
        ]

    def get_queryset(self):
        """Not mandatory but to improve performance we can select related in one sql request"""
        sdf = super(SduDocument, self).get_queryset().select_related('sdfId')
        return sdf


def search_sdus(district, min_sdu_size, max_rent, has_individual_kitchen, has_individual_bath):
    query_str = []
    query_str.append(Q('term', district=district))
    if max_rent > 0:
        query_str.append(Q('range', rent={'lte': max_rent}))
    if min_sdu_size > 0:
        query_str.append(Q('range', size={'gte': min_sdu_size}))
    if has_individual_kitchen:
        query_str.append(Q('term', has_individual_kitchen=True))
    if has_individual_bath:
        query_str.append(Q('term', has_individual_bath=True))

    q = Q('bool', must=query_str)
    result = SduDocument.search().query(q).execute()
    return result
