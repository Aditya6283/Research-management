from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('researchapp', '0002_citation_style_resource_authors_resource_doi_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='renewed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='plan_type',
            field=models.CharField(choices=[('free', 'Free'), ('plus', 'Plus'), ('pro', 'Pro')], default='free', max_length=20),
        ),
    ]
