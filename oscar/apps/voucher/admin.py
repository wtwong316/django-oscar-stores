from django.contrib import admin

from oscar.core.loading import get_model

Voucher = get_model('voucher', 'Voucher')
VoucherApplication = get_model('voucher', 'VoucherApplication')


class VoucherAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'usage', 'num_basket_additions',
                    'num_inquiries', 'total_discount')
    readonly_fields = ('num_basket_additions', 'num_inquiries', 'total_discount')
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'usage', 'start_datetime',
                       'end_datetime')}),
        ('Benefit', {
            'fields': ('offers',)}),
        ('Usage', {
            'fields': ('num_basket_additions', 'num_inquiries',
                       'total_discount')}),
    )


class VoucherApplicationAdmin(admin.ModelAdmin):
    #list_display = ('voucher', 'user', 'inquiry', 'date_created')
    list_display = ('voucher', 'user', 'date_created')
    #readonly_fields = ('voucher', 'user', 'inquiry')
    readonly_fields = ('voucher', 'user')


admin.site.register(Voucher, VoucherAdmin)
admin.site.register(VoucherApplication, VoucherApplicationAdmin)
