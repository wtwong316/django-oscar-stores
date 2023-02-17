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
from django.core.paginator import Paginator
from django.conf import settings

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
        context = self.get_context_data()
        context['form'] = self.form_class()
        return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_result = self.get_context_search_results()
        sdus = search_result
        paginator = Paginator(sdus, settings.OSCAR_SDUS_PER_PAGE)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context["page_obj"] = page_obj
        context["paginator"] = paginator

        return context

    def form_valid(self, form):
        return super().form_valid(form)

    def search_result(self):
        pass

    def get_context_search_results(self):
        return []


