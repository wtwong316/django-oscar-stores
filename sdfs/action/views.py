from django.shortcuts import render
from sdfs.action.forms import SduEstimateForm
from oscar.core.loading import get_model
from django.views import generic
from django.views.generic import FormView
from oscar.core.loading import get_class
from django.core.paginator import Paginator
from django.conf import settings

SdfSdu = get_model('sdfs', 'SdfSdu')


class SduEstimatorView(generic.ListView):
    form_class = SduEstimateForm
    template_name = "sdfs/action/sdf_sdu_estimator.html"
    success_url = "."

    def get(self, request):
        context = {'form': self.form_class()}
        return render(request, self.template_name, context)

    def form_valid(self, form):
        return super().form_valid(form)

    def post(self, request):
        form = SduEstimateForm(request.POST)
        context = {'form': form}
        return render(request, self.template_name, context)
