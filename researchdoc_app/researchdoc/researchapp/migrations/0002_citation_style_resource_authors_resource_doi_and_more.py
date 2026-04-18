from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('researchapp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='citation',
            name='style',
            field=models.CharField(choices=[('apa', 'APA (7th ed.)'), ('ieee', 'IEEE'), ('mla', 'MLA (9th ed.)'), ('chicago', 'Chicago (Author-Date)'), ('harvard', 'Harvard')], default='apa', max_length=15),
        ),
        migrations.AddField(
            model_name='resource',
            name='authors',
            field=models.CharField(blank=True, help_text="Authors as 'Surname, F.; Surname, F.' (semicolon-separated)", max_length=500),
        ),
        migrations.AddField(
            model_name='resource',
            name='doi',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name='resource',
            name='issue',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='resource',
            name='pages',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='resource',
            name='venue',
            field=models.CharField(blank=True, help_text='Journal, conference, or publisher.', max_length=300),
        ),
        migrations.AddField(
            model_name='resource',
            name='volume',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='resource',
            name='year',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AlterField(
            model_name='citation',
            name='citation_text',
            field=models.CharField(blank=True, help_text='Auto-generated from the resource metadata. Editable.', max_length=1000),
        ),
    ]
