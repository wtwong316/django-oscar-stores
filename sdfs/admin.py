from django.contrib import admin
from oscar.core.loading import get_model

Sdf = get_model('sdfs', 'Sdf')
SdfGroup = get_model('sdfs', 'SdfGroup')
"""
OpeningPeriod = get_model('sdfs', 'OpeningPeriod')
"""
SdfStock = get_model('sdfs', 'SdfStock')
SdfSdu = get_model('sdfs', 'SdfSdu')

class SdfAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}


admin.site.register(Sdf, SdfAdmin)
admin.site.register(SdfGroup)
"""
admin.site.register(OpeningPeriod)
"""
admin.site.register(SdfStock)
admin.site.register(SdfSdu)
