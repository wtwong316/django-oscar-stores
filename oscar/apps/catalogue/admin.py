from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from oscar.core.loading import get_model

AttributeOption = get_model('catalogue', 'AttributeOption')
AttributeOptionGroup = get_model('catalogue', 'AttributeOptionGroup')
Category = get_model('catalogue', 'Category')
Option = get_model('catalogue', 'Option')
Sdu = get_model('catalogue', 'Sdu')
SduAttribute = get_model('catalogue', 'SduAttribute')
SduAttributeValue = get_model('catalogue', 'SduAttributeValue')
SduCategory = get_model('catalogue', 'SduCategory')
SduClass = get_model('catalogue', 'SduClass')
SduImage = get_model('catalogue', 'SduImage')
SduRecommendation = get_model('catalogue', 'SduRecommendation')


class AttributeInline(admin.TabularInline):
    model = SduAttributeValue


class SduRecommendationInline(admin.TabularInline):
    model = SduRecommendation
    fk_name = 'primary'
    raw_id_fields = ['primary', 'recommendation']


class CategoryInline(admin.TabularInline):
    model = SduCategory
    extra = 1


class SduAttributeInline(admin.TabularInline):
    model = SduAttribute
    extra = 2


class SduClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'requires_shipping', 'track_stock')
    inlines = [SduAttributeInline]


class SduAdmin(admin.ModelAdmin):
    date_hierarchy = 'date_created'
    list_display = ('get_title', 'upc', 'get_sdu_class', 'structure',
                    'attribute_summary', 'date_created')
    list_filter = ['structure', 'is_discountable']
    raw_id_fields = ['parent']
    inlines = [AttributeInline, CategoryInline, SduRecommendationInline]
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ['upc', 'title']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return (
            qs
            .select_related('sdu_class', 'parent')
            .prefetch_related(
                'attribute_values',
                'attribute_values__attribute'))


class SduAttributeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'sdu_class', 'type')
    prepopulated_fields = {"code": ("name", )}


class OptionAdmin(admin.ModelAdmin):
    pass


class SduAttributeValueAdmin(admin.ModelAdmin):
    list_display = ('sdu', 'attribute', 'value')


class AttributeOptionInline(admin.TabularInline):
    model = AttributeOption


class AttributeOptionGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'option_summary')
    inlines = [AttributeOptionInline, ]


class CategoryAdmin(TreeAdmin):
    form = movenodeform_factory(Category)
    list_display = ('name', 'slug')


admin.site.register(SduClass, SduClassAdmin)
admin.site.register(Sdu, SduAdmin)
admin.site.register(SduAttribute, SduAttributeAdmin)
admin.site.register(SduAttributeValue, SduAttributeValueAdmin)
admin.site.register(AttributeOptionGroup, AttributeOptionGroupAdmin)
admin.site.register(Option, OptionAdmin)
admin.site.register(SduImage)
admin.site.register(Category, CategoryAdmin)
admin.site.register(SduCategory)
