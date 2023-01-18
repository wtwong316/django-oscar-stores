from django.core.management.base import BaseCommand, CommandError

from oscar.core.loading import get_model

Inquiry = get_model('request', 'Inquiry')
CommunicationEventType = get_model('communication', 'CommunicationEventType')


class Command(BaseCommand):
    help = 'For testing the content of inquiry emails'

    def add_arguments(self, parser):
        parser.add_argument('event_type', help='The CommunicationEventType')
        parser.add_argument('inquiry_number', help='The Inquiry number')

    def handle(self, *args, **options):
        try:
            inquiry = Inquiry.objects.get(number=options['inquiry_number'])
        except Inquiry.DoesNotExist:
            raise CommandError(
                "No inquiry found with number %s" % options['inquiry_number'])

        ctx = {
            'inquiry': inquiry,
            'lines': inquiry.lines.all(),
        }
        messages = CommunicationEventType.objects.get_and_render(
            options['event_type'], ctx)
        print("Subject: %s\nBody:\n\n%s\nBody HTML:\n\n%s" % (
            messages['subject'], messages['body'], messages['html']))
