from django.shortcuts import render
from esearch.documents import SduDocument
from django.views.generic import FormView
from oscar.core.loading import get_class
from django.core.paginator import Paginator
from django.conf import settings
from django.views import generic
from esearch.documents import search_sdus

SearchSduForm = get_class('esearch.forms', 'SearchSduForm')
DISTRICTS = {
    "1": "港島中西區",
    "2": "港島東區",
    "3": "港島南區",
    "4": "港島灣仔區",
    "5": "九龍九龍城區",
    "6": "九龍觀塘區",
    "7": "九龍深水埗區",
    "8": "九龍黃大仙區",
    "9": "九龍油尖旺區",
    "10": "新界離島區",
    "11": "新界葵青區",
    "12": "新界北區",
    "13": "新界西貢區",
    "14": "新界沙田區",
    "15": "新界大埔區",
    "16": "新界荃灣區",
    "17": "新界屯門區",
    "18": "新界元朗區"
}


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
        min_sdu_size = int(request.POST.get('min_sdu_size')) if request.POST.get('min_sdu_size') else 0
        max_rent = int(request.POST.get('max_rent')) if request.POST.get('max_rent') else 0
        has_individual_kitchen = bool(request.POST.get('has_individual_kitchen')) \
            if request.POST.get('has_individual_kitchen') else False

        has_individual_bath = bool(request.POST.get('has_individual_bath')) \
            if request.POST.get('has_individual_bath') else False
        sdus = search_sdus(district, min_sdu_size, max_rent, has_individual_bath, has_individual_kitchen)
        paginator = Paginator(sdus, settings.OSCAR_SDUS_PER_PAGE)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number) if page_number is not None else None
        context = {"sdus": sdus, "page_obj": page_obj, "paginator": paginator, 'form': SearchSduForm(request.POST)}
        if len(sdus) == 0:
            context['results'] = False
        else:
            context['results'] = True

        return render(request, self.template_name, context)


def find_district(district_number) :
    return DISTRICTS[district_number]

