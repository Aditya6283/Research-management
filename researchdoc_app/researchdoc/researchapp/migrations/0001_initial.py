import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ComparisonTable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='ComparisonRow',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=100)),
                ('order', models.PositiveIntegerField(default=0)),
                ('table', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rows', to='researchapp.comparisontable')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='ComparisonColumn',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('order', models.PositiveIntegerField(default=0)),
                ('table', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='columns', to='researchapp.comparisontable')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='ResearchProject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('is_archived', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='projects', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.AddField(
            model_name='comparisontable',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comparisons', to='researchapp.researchproject'),
        ),
        migrations.CreateModel(
            name='ResearchSummary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=300)),
                ('content', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='summaries', to='researchapp.researchproject')),
            ],
            options={
                'verbose_name_plural': 'Research summaries',
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=300)),
                ('description', models.TextField(blank=True)),
                ('resource_type', models.CharField(choices=[('paper', 'Paper'), ('link', 'Link')], max_length=10)),
                ('file', models.FileField(blank=True, null=True, upload_to='papers/')),
                ('url', models.URLField(blank=True)),
                ('extracted_text', models.TextField(blank=True)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='resources', to='researchapp.researchproject')),
            ],
            options={
                'ordering': ['-uploaded_at'],
            },
        ),
        migrations.CreateModel(
            name='Citation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('citation_text', models.CharField(blank=True, help_text="e.g., 'Chen et al. (2023)'", max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('summary', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='citations', to='researchapp.researchsummary')),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='citations', to='researchapp.resource')),
            ],
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('plan_type', models.CharField(choices=[('free', 'Free'), ('pro', 'Pro'), ('team', 'Team'), ('enterprise', 'Enterprise')], default='free', max_length=20)),
                ('is_active', models.BooleanField(default=True, help_text='False means archived')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddField(
            model_name='researchproject',
            name='subscription',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='projects', to='researchapp.subscription'),
        ),
        migrations.CreateModel(
            name='UserDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('firstname', models.CharField(blank=True, max_length=100)),
                ('surname', models.CharField(blank=True, max_length=100)),
                ('mobile', models.CharField(blank=True, max_length=20)),
                ('bio', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ComparisonCell',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(blank=True, max_length=500)),
                ('column', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='researchapp.comparisoncolumn')),
                ('row', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='researchapp.comparisonrow')),
                ('table', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cells', to='researchapp.comparisontable')),
            ],
            options={
                'unique_together': {('row', 'column')},
            },
        ),
    ]
