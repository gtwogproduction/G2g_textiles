from django.core.management.base import BaseCommand
from django.utils import timezone

from homepage.models import Quote


class Command(BaseCommand):
    help = 'Mark sent quotes as expired when their valid_until date has passed.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show which quotes would be expired without saving.',
        )

    def handle(self, *args, **options):
        today = timezone.now().date()
        qs = Quote.objects.filter(status='sent', valid_until__lt=today)
        count = qs.count()

        if options['dry_run']:
            for q in qs:
                self.stdout.write(f'  Would expire: {q.quote_number} (valid until {q.valid_until})')
            self.stdout.write(self.style.WARNING(f'Dry run — {count} quote(s) would be expired.'))
            return

        qs.update(status='expired')
        self.stdout.write(self.style.SUCCESS(f'Expired {count} quote(s).'))
