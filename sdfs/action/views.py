from oscar.views.generic import ObjectLookupView
from sdfs.action.forms import SduEstimateForm
from oscar.core.loading import get_model
from django.views import generic

SdfSdu = get_model('sdfs', 'SdfSdu')


class SduEstimatorView(generic.ListView):
    model = SdfSdu
    form_class = SduEstimateForm
    template_name = "sdfs/action/sdf_sdu_estimator.html"

