from django.contrib import admin

from oscar.core.loading import get_model


class SduRecordAdmin(admin.ModelAdmin):
    list_display = ('sdu', 'num_views', 'num_basket_additions',
                    'num_purchases')


class UserSduViewAdmin(admin.ModelAdmin):
    list_display = ('user', 'sdu', 'date_created')


class UserRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'num_sdu_views', 'num_basket_additions',
                    'num_orders', 'total_spent', 'date_last_order')


admin.site.register(get_model('analytics', 'sdurecord'),
                    SduRecordAdmin)
admin.site.register(get_model('analytics', 'userrecord'), UserRecordAdmin)
admin.site.register(get_model('analytics', 'usersearch'))
admin.site.register(get_model('analytics', 'usersduview'),
                    UserSduViewAdmin)
