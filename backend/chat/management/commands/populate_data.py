from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date
from chat.models import Profile, Transaction, Balance


class Command(BaseCommand):
    help = 'Populate the database with initial finance data'

    def handle(self, *args, **options):
        self.stdout.write('Populating database with initial data...')
        
        # Create or update profile
        profile, created = Profile.objects.get_or_create(
            id=1,
            defaults={
                'name': 'Alex Doe',
                'address': '1 High Street, London',
                'email': 'alex@example.com'
            }
        )
        if created:
            self.stdout.write(f'Created profile: {profile.name}')
        else:
            self.stdout.write(f'Profile already exists: {profile.name}')
        
        # Create or update balance
        balance, created = Balance.objects.get_or_create(
            id=1,
            defaults={'amount_minor': 120000}
        )
        if created:
            self.stdout.write(f'Created balance: {balance.amount_minor} minor units')
        else:
            self.stdout.write(f'Balance already exists: {balance.amount_minor} minor units')
        
        # Create transactions if they don't exist
        transactions_data = [
            {'date': '2025-07-01', 'description': 'Coffee Shop', 'amount_minor': -350},
            {'date': '2025-07-02', 'description': 'Grocery Store', 'amount_minor': -4525},
            {'date': '2025-07-03', 'description': 'Salary', 'amount_minor': 250000},
            {'date': '2025-07-05', 'description': 'Gym Membership', 'amount_minor': -2999},
            {'date': '2025-07-07', 'description': 'Electricity Bill', 'amount_minor': -6400},
            {'date': '2025-07-09', 'description': 'Restaurant', 'amount_minor': -5800},
        ]
        
        created_count = 0
        for trans_data in transactions_data:
            transaction, created = Transaction.objects.get_or_create(
                date=trans_data['date'],
                description=trans_data['description'],
                amount_minor=trans_data['amount_minor']
            )
            if created:
                created_count += 1
        
        self.stdout.write(f'Created {created_count} new transactions')
        self.stdout.write(self.style.SUCCESS('Database population completed successfully!'))
