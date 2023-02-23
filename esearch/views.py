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
from django.views import generic

SearchSduForm = get_class('esearch.forms', 'SearchSduForm')


class SearchSduView(FormView):
    template_name = 'esearch/search_sdu.html'
    form_class = SearchSduForm
    context_object_name = 'context'
    success_url = "."

    def get(self, request):
        context = {'form': self.form_class()}
        return render(request, self.template_name, context)

    def form_valid(self, form):
        return super().form_valid(form)

    def post(self, request):
        form = SduDocument(request.POST)
        context = self.get_context_data(request.POST.get('district'), request.POST.get('min_sdu_size'),
                                        request.POST.get('max_rent'), request.POST.get('has_individual_kitchen'),
                                        request.POST.get('has_individual_bath'))
        context['form'] = form
        return render(request, self.template_name, context)

    def get_context_data(self, district, min_sdu_size, max_rent, has_individual_kitchen, has_individual_bath):
        sdus = self.get_context_search_results(district, min_sdu_size, max_rent, has_individual_kitchen, has_individual_bath)
        paginator = Paginator(sdus, settings.OSCAR_SDUS_PER_PAGE)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context = {"sdus": sdus, "page_obj": page_obj, "paginator": paginator}
        return context

    def get_context_search_results(self, district, min_sdu_size, max_rent, has_individual_kitchen, has_individual_bath):
        sdus = SduDocument.search().filter("term", district=district, )
        return sdus
