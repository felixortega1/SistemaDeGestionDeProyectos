import pytest
from django.core.management import call_command
from django.db import IntegrityError, transaction

from apps.sprints import services
from apps.sprints.models import Sprint


@pytest.mark.django_db(transaction=True)
def test_sprints_and_backlog_migrate_down_and_up():
    call_command("migrate", "sprints", "zero", verbosity=0)
    call_command("migrate", verbosity=0)


@pytest.mark.django_db
def test_no_pending_migrations():
    call_command("makemigrations", "--check", "--dry-run", verbosity=0)


def test_unique_index_rejects_second_active_sprint(project, today):
    a = services.create_sprint(project, "A", start_date=today, end_date=today)
    b = services.create_sprint(project, "B", start_date=today, end_date=today)
    Sprint.objects.filter(pk=a.pk).update(status="active")
    with pytest.raises(IntegrityError), transaction.atomic():
        Sprint.objects.filter(pk=b.pk).update(status="active")
