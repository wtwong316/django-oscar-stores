from django.utils.translation import gettext_lazy as _

from oscar.core.loading import get_class, get_model

ReportGenerator = get_class('dashboard.reports.reports', 'ReportGenerator')
ReportCSVFormatter = get_class('dashboard.reports.reports',
                               'ReportCSVFormatter')
ReportHTMLFormatter = get_class('dashboard.reports.reports',
                                'ReportHTMLFormatter')
Inquiry = get_model('inquiry', 'Inquiry')


class InquiryReportCSVFormatter(ReportCSVFormatter):
    filename_template = 'inquiries-%s-to-%s.csv'

    def generate_csv(self, response, inquiries):
        writer = self.get_csv_writer(response)
        header_row = [_('Inquiry number'),
                      _('Name'),
                      _('Email'),
                      _('Total incl. tax'),
                      _('Date placed')]
        writer.writerow(header_row)
        for inquiry in inquiries:
            row = [
                inquiry.number,
                '-' if inquiry.is_anonymous else inquiry.user.get_full_name(),
                inquiry.email,
                inquiry.total_incl_tax,
                self.format_datetime(inquiry.date_placed)]
            writer.writerow(row)

    def filename(self, **kwargs):
        return self.filename_template % (
            kwargs['start_date'], kwargs['end_date'])


class InquiryReportHTMLFormatter(ReportHTMLFormatter):
    filename_template = 'oscar/dashboard/reports/partials/inquiry_report.html'


class InquiryReportGenerator(ReportGenerator):
    code = 'inquiry_report'
    description = _("Inquiries placed")
    date_range_field_name = 'date_placed'
    model_class = Inquiry

    formatters = {
        'CSV_formatter': InquiryReportCSVFormatter,
        'HTML_formatter': InquiryReportHTMLFormatter,
    }

    def generate(self):
        additional_data = {
            'start_date': self.start_date,
            'end_date': self.end_date
        }
        return self.formatter.generate_response(self.queryset, **additional_data)

    def is_available_to(self, user):
        return user.is_staff
