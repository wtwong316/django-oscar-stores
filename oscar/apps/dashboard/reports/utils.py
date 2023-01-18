from oscar.core.loading import get_class, get_classes

InquiryReportGenerator = get_class('inquiry.reports', 'InquiryReportGenerator')
SduReportGenerator, UserReportGenerator \
    = get_classes('analytics.reports', ['SduReportGenerator',
                                        'UserReportGenerator'])
OpenBasketReportGenerator, SubmittedBasketReportGenerator \
    = get_classes('basket.reports', ['OpenBasketReportGenerator',
                                     'SubmittedBasketReportGenerator'])
OfferReportGenerator = get_class('offer.reports', 'OfferReportGenerator')
VoucherReportGenerator = get_class('voucher.reports', 'VoucherReportGenerator')


class GeneratorRepository(object):

    generators = [InquiryReportGenerator,
                  SduReportGenerator,
                  UserReportGenerator,
                  OpenBasketReportGenerator,
                  SubmittedBasketReportGenerator,
                  VoucherReportGenerator,
                  OfferReportGenerator]

    def get_report_generators(self):
        return self.generators

    def get_generator(self, code):
        for generator in self.generators:
            if generator.code == code:
                return generator
        return None
