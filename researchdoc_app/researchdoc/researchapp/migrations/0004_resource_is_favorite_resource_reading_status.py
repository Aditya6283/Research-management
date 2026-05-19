from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('researchapp', '0003_subscription_renewed_at_alter_subscription_plan_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='is_favorite',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='resource',
            name='reading_status',
            field=models.CharField(
                choices=[('unread', 'To read'), ('reading', 'Reading'), ('read', 'Read')],
                default='unread',
                max_length=10,
            ),
        ),
    ]
