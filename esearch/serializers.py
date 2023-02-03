from esearch.documents import SduDocument
from django_elasticsearch_dsl_drf.serializers import DocumentSerializer


class SduDocumentSerializer(DocumentSerializer):
    class Meta:
        document = SduDocument

        fields = (
            'size',
            'household_size',
            'rent',
        )