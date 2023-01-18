from django.utils.translation import gettext_lazy as _

from oscar.core.loading import get_class

ReportCSVFormatter = get_class(
    'dashboard.reports.reports', 'ReportCSVFormatter')


class InquiryDiscountCSVFormatter(ReportCSVFormatter):
    filename_template = 'inquiry-discounts-for-offer-%s.csv'

    def generate_csv(self, response, inquiry_discounts):
        writer = self.get_csv_writer(response)
        header_row = [_('Inquiry number'),
                      _('Inquiry date'),
                      _('Inquiry total'),
                      _('Cost')]
        writer.writerow(header_row)
        for inquiry_discount in inquiry_discounts:
            inquiry = inquiry_discount.inquiry
            row = [inquiry.number,
                   self.format_datetime(inquiry.date_placed),
                   inquiry.total_incl_tax,
                   inquiry_discount.amount]
            writer.writerow(row)

    def filename(self, offer):
        return self.filename_template % offer.id
