from django.shortcuts import render
from esearch.documents import SduDocument
from django.views.generic import FormView
from oscar.core.loading import get_class
from django.core.paginator import Paginator
from django.conf import settings
from django.views import generic
from esearch.documents import search_sdus
from sdfs.utils import find_district

SearchSduForm = get_class('esearch.forms', 'SearchSduForm')


class SearchSduView(generic.ListView):
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
        district = find_district(request.POST.get('district'))
        street = request.POST.get('street')
        building = request.POST.get('building')
        min_sdu_size = int(request.POST.get('min_sdu_size')) if request.POST.get('min_sdu_size') else 0
        max_rent = int(request.POST.get('max_rent')) if request.POST.get('max_rent') else 0
        has_individual_kitchen = bool(request.POST.get('has_individual_kitchen')) \
            if request.POST.get('has_individual_kitchen') else False

        has_individual_bath = bool(request.POST.get('has_individual_bath')) \
            if request.POST.get('has_individual_bath') else False
        has_exterior_window = bool(request.POST.get('has_exterior_window')) \
            if request.POST.get('has_exterior_window') else False
        sdus = search_sdus(district, street, building, min_sdu_size, max_rent, has_individual_bath,
                           has_individual_kitchen, has_exterior_window)
        paginator = Paginator(sdus, settings.OSCAR_SDUS_PER_PAGE)
        page_number = self.request.GET.get('page')
        page_number = 1 if page_number is None else page_number
        page_obj = paginator.get_page(page_number)
        context = {"sdus": sdus, "page_obj": page_obj, "paginator": paginator, 'form': SearchSduForm(request.POST),
                   "len": len(sdus)}
        if len(sdus) == 0:
            context['results'] = False
        else:
            context['results'] = True

        return render(request, self.template_name, context)




