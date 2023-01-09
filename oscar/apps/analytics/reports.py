from django.utils.translation import gettext_lazy as _

from oscar.core.loading import get_class, get_model

ReportGenerator = get_class('dashboard.reports.reports', 'ReportGenerator')
ReportCSVFormatter = get_class('dashboard.reports.reports',
                               'ReportCSVFormatter')
ReportHTMLFormatter = get_class('dashboard.reports.reports',
                                'ReportHTMLFormatter')
SduRecord = get_model('analytics', 'SduRecord')
UserRecord = get_model('analytics', 'UserRecord')


class SduReportCSVFormatter(ReportCSVFormatter):
    filename_template = 'conditional-offer-performance.csv'

    def generate_csv(self, response, sdus):
        writer = self.get_csv_writer(response)
        header_row = [_('Sdu'),
                      _('Views'),
                      _('Basket additions'),
                      _('Purchases')]
        writer.writerow(header_row)

        for record in sdus:
            row = [record.sdu,
                   record.num_views,
                   record.num_basket_additions,
                   record.num_purchases]
            writer.writerow(row)


class SduReportHTMLFormatter(ReportHTMLFormatter):
    filename_template = 'oscar/dashboard/reports/partials/sdu_report.html'


class SduReportGenerator(ReportGenerator):
    code = 'sdu_analytics'
    description = _('Sdu analytics')
    model_class = SduRecord

    formatters = {
        'CSV_formatter': SduReportCSVFormatter,
        'HTML_formatter': SduReportHTMLFormatter}

    def report_description(self):
        return self.description

    def is_available_to(self, user):
        return user.is_staff


class UserReportCSVFormatter(ReportCSVFormatter):
    filename_template = 'user-analytics.csv'

    def generate_csv(self, response, users):
        writer = self.get_csv_writer(response)
        header_row = [_('Name'),
                      _('Date registered'),
                      _('Sdu views'),
                      _('Basket additions'),
                      _('Orders'),
                      _('Order lines'),
                      _('Order items'),
                      _('Total spent'),
                      _('Date of last order')]
        writer.writerow(header_row)

        for record in users:
            row = [record.user.get_full_name(),
                   self.format_date(record.user.date_joined),
                   record.num_sdu_views,
                   record.num_basket_additions,
                   record.num_orders,
                   record.num_order_lines,
                   record.num_order_items,
                   record.total_spent,
                   self.format_datetime(record.date_last_order)]
            writer.writerow(row)


class UserReportHTMLFormatter(ReportHTMLFormatter):
    filename_template = 'oscar/dashboard/reports/partials/user_report.html'


class UserReportGenerator(ReportGenerator):
    code = 'user_analytics'
    description = _('User analytics')
    queryset = UserRecord._default_manager.select_related().all()

    formatters = {
        'CSV_formatter': UserReportCSVFormatter,
        'HTML_formatter': UserReportHTMLFormatter}

    def is_available_to(self, user):
        return user.is_staff
