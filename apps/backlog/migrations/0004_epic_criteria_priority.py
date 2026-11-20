import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backlog', '0003_remove_epic'),
        ('projects', '0003_project_manager_role'),
    ]

    operations = [
        migrations.CreateModel(
            name='Epic',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('color', models.CharField(default='#EAB308', max_length=7)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='epics', to='projects.project')),
            ],
            options={
                'ordering': ['title', 'id'],
            },
        ),
        migrations.AddField(
            model_name='task',
            name='epic',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='tasks', to='backlog.epic'),
        ),
        migrations.AddField(
            model_name='task',
            name='priority',
            field=models.CharField(choices=[('high', 'Alta'), ('medium', 'Media'), ('low', 'Baja')], default='medium', max_length=10),
        ),
        migrations.AddConstraint(
            model_name='task',
            constraint=models.CheckConstraint(condition=models.Q(('priority__in', ['high', 'medium', 'low'])), name='task_priority_valid'),
        ),
        migrations.AddConstraint(
            model_name='task',
            constraint=models.CheckConstraint(condition=models.Q(('kind', 'story'), ('epic__isnull', True), _connector='OR'), name='task_epic_only_on_stories'),
        ),
        migrations.CreateModel(
            name='AcceptanceCriterion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=500)),
                ('is_done', models.BooleanField(default=False)),
                ('position', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='criteria', to='backlog.task')),
            ],
            options={
                'ordering': ['position', 'id'],
            },
        ),
    ]
