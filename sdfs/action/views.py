from django.shortcuts import render
from sdfs.action.forms import SduEstimateForm
from oscar.core.loading import get_model
from django.views import generic
from sdfs.action.rent_estimator import rent_estimation
from django.views.generic import FormView
from oscar.core.loading import get_class
from django.core.paginator import Paginator
from django.conf import settings

SdfSdu = get_model('sdfs', 'SdfSdu')


class SduEstimatorView(generic.ListView):
    form_class = SduEstimateForm
    template_name = "sdfs/action/sdf_sdu_estimator.html"
    context_object_name = 'context'
    success_url = "."

    def get(self, request):
        context = {'form': self.form_class(), 'results': 0}
        return render(request, self.template_name, context)

    def form_valid(self, form):
        return super().form_valid(form)

    def post(self, request):
        form = SduEstimateForm(request.POST)
        context = {'form': form}
        value = rent_estimation()
        rent = 0
        if len(request.POST.get('rent')) > 0:
            rent = int(request.POST.get('rent'))

        if rent > 0:
            context['results'] = 1
            context['value'] = value
            context['compare'] = 0
            if value > rent:
                context['compare'] = 1
            elif value < rent:
                context['compare'] = -1
        else:
            context['value'] = value
            context['results'] = 2
        return render(request, self.template_name, context)
