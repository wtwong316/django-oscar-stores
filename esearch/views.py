from django.shortcuts import render
from django.http import HttpResponse
from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet
from django_elasticsearch_dsl_drf.filter_backends \
    import SearchFilterBackend, FilteringFilterBackend, SuggesterFilterBackend
from django.contrib import messages

from esearch.documents import SduDocument
from esearch.serializers import SduDocumentSerializer
from django.views.generic import FormView
from oscar.core.loading import get_class


SearchSduForm = get_class('esearch.forms', 'SearchSduForm')


# Create your views here.
class SearchSduDocumentView(DocumentViewSet):
    document = SduDocument
    serializer_class = SduDocumentSerializer

    filter_backends = [

    ]

    search_fields = (
    )

    filter_fields = {
        'size', 'household_size', 'rent'
    }

    suggester_fields = {
    }


class SearchSduView(FormView):
    template_name = 'esearch/search_sdu.html'
    form_class = SearchSduForm
    success_url = "."

    def get(self, request):
        context = {}
        form = self.form_class()
        context['form'] = self.form_class()
        return render(request, self.template_name, context)



