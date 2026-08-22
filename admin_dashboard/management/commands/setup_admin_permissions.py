from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):

    help = "Create and configure KaamSetu Admin permission groups."

    def handle(self, *args, **options):

        # =====================================================
        # GROUP DEFINITIONS
        # =====================================================

        group_permissions = {

            "Operations Manager": [

                # Workers
                "view_worker",
                "change_worker",

                # Bookings
                "view_booking",
                "change_booking",

            ],

            "Finance Manager": [

                # Worker Ledger
                "view_workerledger",
                "change_workerledger",

            ],

            "Content Manager": [

                # Workers
                "view_worker",
                "change_worker",

            ],

            "Support Manager": [

                # Customers
                "view_user",

                # Bookings
                "view_booking",
                "change_booking",

            ],

            "Reports Manager": [

                # Read-only operational access
                "view_worker",
                "view_booking",
                "view_workerledger",
                "view_user",

            ],
        }


        # =====================================================
        # CREATE / UPDATE GROUPS
        # =====================================================

        for group_name, permission_codenames in group_permissions.items():

            group, created = Group.objects.get_or_create(
                name=group_name
            )


            # Clear existing permissions so that
            # this command always produces the
            # expected final permission set.

            group.permissions.clear()


            added_permissions = 0


            # =================================================
            # ADD PERMISSIONS
            # =================================================

            for codename in permission_codenames:

                permission = Permission.objects.filter(
                    codename=codename
                ).first()


                if permission:

                    group.permissions.add(
                        permission
                    )

                    added_permissions += 1

                else:

                    self.stdout.write(
                        self.style.WARNING(
                            f"Permission not found: {codename}"
                        )
                    )


            # =================================================
            # RESULT
            # =================================================

            if created:

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created group: {group_name}"
                    )
                )

            else:

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Updated group: {group_name}"
                    )
                )


            self.stdout.write(
                f"  Permissions assigned: {added_permissions}"
            )


        # =====================================================
        # COMPLETE
        # =====================================================

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "KaamSetu Admin permission setup completed."
            )
        )