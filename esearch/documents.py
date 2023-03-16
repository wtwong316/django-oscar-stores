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

    district = fields.KeywordField()
    street = fields.TextField(
        fields={'raw': fields.KeywordField()}
    )
    building = fields.KeywordField()
    size = fields.IntegerField()
    rent = fields.IntegerField()
    has_individual_kitchen = fields.BooleanField()
    has_individual_bath = fields.BooleanField()
    has_exterior_window = fields.BooleanField()

    class Django:
        model = SdfSdu

    def get_queryset(self):
        """Not mandatory but to improve performance we can select related in one sql request"""
        sdf = super(SduDocument, self).get_queryset().select_related('sdfId')
        return sdf


def search_sdus(district, street, building, min_sdu_size, max_rent, has_individual_bath, has_individual_kitchen,
                has_exterior_window):
    query_str = [Q('term', district=district)]
    if len(street) > 0:
        query_str.append(Q('match', street=street))
    if len(building) > 0:
        query_str.append(Q('term', building=building))
    if max_rent > 0:
        query_str.append(Q('range', rent={'lte': max_rent}))
    if min_sdu_size > 0:
        query_str.append(Q('range', size={'gte': min_sdu_size}))
    if has_individual_kitchen:
        query_str.append(Q('term', has_individual_kitchen=True))
    if has_individual_bath:
        query_str.append(Q('term', has_individual_bath=True))
    if has_exterior_window:
        query_str.append(Q('term', has_exterior_window=True))

    q = Q('bool', must=query_str)
    search_request = SduDocument.search()
    result = search_request.query(q).execute()
    return result
