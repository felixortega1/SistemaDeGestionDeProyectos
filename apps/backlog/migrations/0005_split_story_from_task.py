"""Separa las historias de las tareas en dos tablas.

Antes una historia era una fila de `Task` con kind="story". Ahora hay `Story` y `Task` (sin kind ni parent).
Los datos existentes se migran: cada historia pasa a `Story` (con su épica, prioridad, solicitante y fechas),
sus actividades quedan enlazadas con `Task.story`, y los criterios y comentarios pasan a la historia.
La migración hacia atrás deshace el esquema pero NO restaura los datos de historias.
"""

import django.db.models.deletion
from django.db import migrations, models


def split_stories(apps, schema_editor):
    Task = apps.get_model("backlog", "Task")
    Story = apps.get_model("backlog", "Story")
    Criterion = apps.get_model("backlog", "AcceptanceCriterion")
    Comment = apps.get_model("backlog", "Comment")

    mapping = {}
    for old in Task.objects.filter(kind="story").order_by("id"):
        story = Story.objects.create(
            project_id=old.project_id,
            epic_id=old.epic_id,
            title=old.title,
            description=old.description,
            stakeholder=old.stakeholder,
            priority=old.priority,
            estimate_points=old.estimate_points,
        )
        # auto_now_add / auto_now ponen la fecha actual al crear: se conservan las originales.
        Story.objects.filter(pk=story.pk).update(created_at=old.created_at, updated_at=old.updated_at)
        mapping[old.pk] = story.pk

    for old_id, story_id in mapping.items():
        Task.objects.filter(parent_id=old_id).update(story_id=story_id)
        Criterion.objects.filter(task_id=old_id).update(story_id=story_id)
        Comment.objects.filter(task_id=old_id).update(story_id=story_id, task_id=None)
    # Las hijas dejan de apuntar a la fila-historia para poder borrarla (parent es PROTECT).
    Task.objects.filter(parent_id__in=list(mapping)).update(parent=None)


def delete_story_rows(apps, schema_editor):
    Task = apps.get_model("backlog", "Task")
    Task.objects.filter(kind="story").delete()


class Migration(migrations.Migration):

    dependencies = [
        ('backlog', '0004_epic_criteria_priority'),
        ('projects', '0003_project_manager_role'),
    ]

    operations = [
        migrations.CreateModel(
            name='Story',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('stakeholder', models.CharField(blank=True, help_text='Quién pidió esta historia.', max_length=200)),
                ('priority', models.CharField(choices=[('high', 'Alta'), ('medium', 'Media'), ('low', 'Baja')], default='medium', max_length=10)),
                ('estimate_points', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('epic', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='stories', to='backlog.epic')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='stories', to='projects.project')),
            ],
        ),
        migrations.AddField(
            model_name='task',
            name='story',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='tasks', to='backlog.story'),
        ),
        migrations.AddField(
            model_name='acceptancecriterion',
            name='story',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='criteria', to='backlog.story'),
        ),
        migrations.AddField(
            model_name='comment',
            name='story',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='backlog.story'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='task',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='backlog.task'),
        ),
        migrations.RunPython(split_stories, migrations.RunPython.noop),
        # `task` pasa a admitir nulos antes de quitarlo: así la migración hacia atrás puede volver a crearlo.
        migrations.AlterField(
            model_name='acceptancecriterion',
            name='task',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='criteria', to='backlog.task'),
        ),
        migrations.RemoveField(
            model_name='acceptancecriterion',
            name='task',
        ),
        migrations.AlterField(
            model_name='acceptancecriterion',
            name='story',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='criteria', to='backlog.story'),
        ),
        migrations.RunPython(delete_story_rows, migrations.RunPython.noop),
        migrations.RemoveConstraint(
            model_name='task',
            name='task_kind_valid',
        ),
        migrations.RemoveConstraint(
            model_name='task',
            name='task_priority_valid',
        ),
        migrations.RemoveConstraint(
            model_name='task',
            name='task_epic_only_on_stories',
        ),
        migrations.RemoveConstraint(
            model_name='task',
            name='task_story_has_no_planning',
        ),
        migrations.RemoveField(
            model_name='task',
            name='parent',
        ),
        migrations.RemoveField(
            model_name='task',
            name='kind',
        ),
        migrations.RemoveField(
            model_name='task',
            name='stakeholder',
        ),
        migrations.RemoveField(
            model_name='task',
            name='epic',
        ),
        migrations.RemoveField(
            model_name='task',
            name='priority',
        ),
        migrations.AddConstraint(
            model_name='story',
            constraint=models.CheckConstraint(condition=models.Q(('priority__in', ['high', 'medium', 'low'])), name='story_priority_valid'),
        ),
        migrations.AddConstraint(
            model_name='comment',
            constraint=models.CheckConstraint(condition=models.Q(models.Q(('story__isnull', False), ('task__isnull', True)), models.Q(('story__isnull', True), ('task__isnull', False)), _connector='OR'), name='comment_story_xor_task'),
        ),
    ]
