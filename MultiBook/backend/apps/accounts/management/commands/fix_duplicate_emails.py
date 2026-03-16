"""
Management command to fix duplicate email addresses (case-sensitive duplicates).

Merges users with the same email address (case-insensitive) by:
1. Normalizing all emails to lowercase
2. Keeping the first user with that email
3. Merging data from duplicate users into the first user
4. Deleting duplicate users
"""
from django.core.management.base import BaseCommand
from django.db.models import Count
from apps.accounts.models import User
from collections import defaultdict


class Command(BaseCommand):
    help = 'Fix duplicate email addresses by normalizing to lowercase and merging duplicates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Find all users with duplicate emails (case-insensitive)
        users_by_email = defaultdict(list)
        
        for user in User.objects.all():
            email_lower = user.email.lower().strip() if user.email else ''
            users_by_email[email_lower].append(user)
        
        duplicates_found = 0
        users_normalized = 0
        users_merged = 0
        users_deleted = 0
        
        for email_lower, users in users_by_email.items():
            if not email_lower:
                continue
            
            # Check if there are duplicates
            if len(users) > 1:
                duplicates_found += 1
                self.stdout.write(f'\nFound {len(users)} users with email: {email_lower}')
                
                # Sort users: keep the oldest one (lowest ID)
                users.sort(key=lambda u: u.id)
                primary_user = users[0]
                duplicate_users = users[1:]
                
                self.stdout.write(f'  Keeping user ID {primary_user.id} ({primary_user.email})')
                
                # Normalize primary user's email to lowercase
                if primary_user.email != email_lower:
                    users_normalized += 1
                    if not dry_run:
                        primary_user.email = email_lower
                        primary_user.save(update_fields=['email'])
                        self.stdout.write(f'  ✓ Normalized email to: {email_lower}')
                    else:
                        self.stdout.write(f'  [DRY RUN] Would normalize email to: {email_lower}')
                
                # Merge data from duplicate users (if needed)
                for dup_user in duplicate_users:
                    self.stdout.write(f'  Merging user ID {dup_user.id} ({dup_user.email})')
                    
                    # Merge profile data if primary doesn't have it
                    if hasattr(primary_user, 'profile') and not primary_user.profile.phone:
                        if hasattr(dup_user, 'profile') and dup_user.profile.phone:
                            if not dry_run:
                                primary_user.profile.phone = dup_user.profile.phone
                                primary_user.profile.save()
                                self.stdout.write(f'    ✓ Merged phone number')
                    
                    # Delete duplicate user
                    users_deleted += 1
                    if not dry_run:
                        dup_user.delete()
                        self.stdout.write(f'    ✓ Deleted duplicate user ID {dup_user.id}')
                    else:
                        self.stdout.write(f'    [DRY RUN] Would delete user ID {dup_user.id}')
                
                users_merged += len(duplicate_users)
            
            elif len(users) == 1:
                # Single user - just normalize email if needed
                user = users[0]
                if user.email and user.email != email_lower:
                    users_normalized += 1
                    if not dry_run:
                        user.email = email_lower
                        user.save(update_fields=['email'])
                    self.stdout.write(f'Normalized email: {user.email} → {email_lower}')
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('SUMMARY:'))
        self.stdout.write(f'  Duplicate email groups found: {duplicates_found}')
        self.stdout.write(f'  Emails normalized: {users_normalized}')
        self.stdout.write(f'  Users merged: {users_merged}')
        self.stdout.write(f'  Duplicate users deleted: {users_deleted}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN - No changes were made'))
            self.stdout.write(self.style.WARNING('Run without --dry-run to apply changes'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✓ All duplicate emails have been fixed!'))
