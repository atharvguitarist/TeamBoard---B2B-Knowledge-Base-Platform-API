from django.core.management.base import BaseCommand
from api.models import KBEntry


SEED_ENTRIES = [
    {
        'question': 'What is select_related in Django ORM?',
        'answer': 'select_related performs a SQL JOIN and fetches related ForeignKey or OneToOne objects in the same database query.',
        'category': KBEntry.Category.DATABASE,
    },
    {
        'question': 'When should I use prefetch_related in Django?',
        'answer': 'Use prefetch_related for many-to-many and reverse foreign key relationships where Django should run a separate query and join results in Python.',
        'category': KBEntry.Category.DATABASE,
    },
    {
        'question': 'How does transaction.atomic() work?',
        'answer': 'transaction.atomic creates a database transaction block. If any exception occurs, all writes inside the block are rolled back together.',
        'category': KBEntry.Category.DATABASE,
    },
    {
        'question': 'What is a JWT token?',
        'answer': 'A JWT is a signed JSON token used to prove identity to an API without storing server-side session state for every request.',
        'category': KBEntry.Category.API,
    },
    {
        'question': 'How do API keys differ from JWT authentication?',
        'answer': 'API keys identify an external client application, while JWT tokens usually represent an authenticated user session and expire after a configured time.',
        'category': KBEntry.Category.API,
    },
    {
        'question': 'When should I use Q objects in Django?',
        'answer': 'Use Q objects when you need complex ORM filters such as OR conditions, combined AND/OR logic, or dynamic search predicates.',
        'category': KBEntry.Category.FRAMEWORK,
    },
    {
        'question': 'What is Django REST Framework used for?',
        'answer': 'Django REST Framework helps build Web APIs with serializers, authentication, permissions, view classes, and browsable API support.',
        'category': KBEntry.Category.FRAMEWORK,
    },
    {
        'question': 'What is an HTTP 401 response?',
        'answer': 'HTTP 401 means authentication is missing or invalid. The client should provide valid credentials such as a Bearer token.',
        'category': KBEntry.Category.API,
    },
    {
        'question': 'What is an HTTP 403 response?',
        'answer': 'HTTP 403 means the user is authenticated but does not have permission to access the requested resource.',
        'category': KBEntry.Category.API,
    },
    {
        'question': 'What is PostgreSQL commonly used for?',
        'answer': 'PostgreSQL is a relational database used for reliable structured storage, transactions, indexes, constraints, and SQL querying.',
        'category': KBEntry.Category.DATABASE,
    },
    {
        'question': 'What is Docker Compose used for in backend projects?',
        'answer': 'Docker Compose defines and runs multi-container environments, such as a Django API service with a PostgreSQL database.',
        'category': KBEntry.Category.CLOUD,
    },
    {
        'question': 'Why should secrets be stored in environment variables?',
        'answer': 'Environment variables keep database passwords, secret keys, and credentials outside application source code and make deployments safer.',
        'category': KBEntry.Category.GENERAL,
    },
]


class Command(BaseCommand):
    help = 'Seed the TeamBoard knowledge base with sample Q&A entries.'

    def handle(self, *args, **options):
        created = 0
        for item in SEED_ENTRIES:
            _, was_created = KBEntry.objects.get_or_create(
                question=item['question'],
                defaults={
                    'answer': item['answer'],
                    'category': item['category'],
                },
            )
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(f'Seed complete. Created {created} new KB entries.'))
