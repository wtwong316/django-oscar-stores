from django.contrib import admin

from oscar.core.loading import get_model

Inquiry = get_model('inquiry', 'Inquiry')
InquiryNote = get_model('inquiry', 'InquiryNote')
InquiryStatusChange = get_model('inquiry', 'InquiryStatusChange')
CommunicationEvent = get_model('inquiry', 'CommunicationEvent')
BillingAddress = get_model('inquiry', 'BillingAddress')
ShippingAddress = get_model('inquiry', 'ShippingAddress')
Line = get_model('inquiry', 'Line')
LinePrice = get_model('inquiry', 'LinePrice')
ShippingEvent = get_model('inquiry', 'ShippingEvent')
ShippingEventType = get_model('inquiry', 'ShippingEventType')
PaymentEvent = get_model('inquiry', 'PaymentEvent')
PaymentEventType = get_model('inquiry', 'PaymentEventType')
PaymentEventQuantity = get_model('inquiry', 'PaymentEventQuantity')
LineAttribute = get_model('inquiry', 'LineAttribute')
InquiryDiscount = get_model('inquiry', 'InquiryDiscount')
Surcharge = get_model('inquiry', 'Surcharge')


class LineInline(admin.TabularInline):
    model = Line
    extra = 0


class InquiryAdmin(admin.ModelAdmin):
    raw_id_fields = ['user', 'billing_address', 'shipping_address', ]
    list_display = ('number', 'total_incl_tax', 'site', 'user',
                    'billing_address', 'date_placed')
    readonly_fields = ('number', 'basket', 'total_incl_tax', 'total_excl_tax',
                       'shipping_incl_tax', 'shipping_excl_tax')
    inlines = [LineInline]


class LineAdmin(admin.ModelAdmin):
    list_display = ('inquiry', 'product', 'stockrecord', 'quantity')


class LinePriceAdmin(admin.ModelAdmin):
    list_display = ('inquiry', 'line', 'price_incl_tax', 'quantity')


class ShippingEventTypeAdmin(admin.ModelAdmin):
    list_display = ('name', )


class PaymentEventQuantityInline(admin.TabularInline):
    model = PaymentEventQuantity
    extra = 0


class PaymentEventAdmin(admin.ModelAdmin):
    list_display = ('inquiry', 'event_type', 'amount', 'num_affected_lines',
                    'date_created')
    inlines = [PaymentEventQuantityInline]


class PaymentEventTypeAdmin(admin.ModelAdmin):
    pass


class InquiryDiscountAdmin(admin.ModelAdmin):
    readonly_fields = ('inquiry', 'category', 'offer_id', 'offer_name',
                       'voucher_id', 'voucher_code', 'amount')
    list_display = ('inquiry', 'category', 'offer', 'voucher',
                    'voucher_code', 'amount')


class SurchargeAdmin(admin.ModelAdmin):
    raw_id_fields = ("inquiry",)


admin.site.register(Inquiry, InquiryAdmin)
admin.site.register(InquiryNote)
admin.site.register(InquiryStatusChange)
admin.site.register(ShippingAddress)
admin.site.register(Line, LineAdmin)
admin.site.register(LinePrice, LinePriceAdmin)
admin.site.register(ShippingEvent)
admin.site.register(ShippingEventType, ShippingEventTypeAdmin)
admin.site.register(PaymentEvent, PaymentEventAdmin)
admin.site.register(PaymentEventType, PaymentEventTypeAdmin)
admin.site.register(LineAttribute)
admin.site.register(InquiryDiscount, InquiryDiscountAdmin)
admin.site.register(CommunicationEvent)
admin.site.register(BillingAddress)
admin.site.register(Surcharge, SurchargeAdmin)
