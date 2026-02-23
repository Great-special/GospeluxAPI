# Generated migration file for FCM Notifications app

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DeviceToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(db_index=True, max_length=255, unique=True)),
                ('platform', models.CharField(choices=[('android', 'Android'), ('ios', 'iOS'), ('web', 'Web')], max_length=10)),
                ('device_id', models.CharField(blank=True, max_length=255, null=True)),
                ('device_name', models.CharField(blank=True, max_length=255, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('last_used', models.DateTimeField(default=django.utils.timezone.now)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='device_tokens', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'fcm_device_tokens',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('body', models.TextField()),
                ('notification_type', models.CharField(choices=[('single', 'Single User'), ('bulk', 'Bulk'), ('topic', 'Topic'), ('condition', 'Condition')], default='single', max_length=20)),
                ('topic', models.CharField(blank=True, max_length=255, null=True)),
                ('condition', models.CharField(blank=True, max_length=500, null=True)),
                ('data', models.JSONField(blank=True, default=dict)),
                ('icon', models.URLField(blank=True, null=True)),
                ('image', models.URLField(blank=True, null=True)),
                ('click_action', models.URLField(blank=True, null=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('sent', 'Sent'), ('failed', 'Failed'), ('partial', 'Partially Sent')], default='pending', max_length=20)),
                ('total_tokens', models.IntegerField(default=0)),
                ('successful_sends', models.IntegerField(default=0)),
                ('failed_sends', models.IntegerField(default=0)),
                ('error_message', models.TextField(blank=True, null=True)),
                ('scheduled_at', models.DateTimeField(blank=True, null=True)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notifications_created', to=settings.AUTH_USER_MODEL)),
                ('target_users', models.ManyToManyField(blank=True, related_name='notifications_received', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'fcm_notifications',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='NotificationTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('title', models.CharField(max_length=255)),
                ('body', models.TextField()),
                ('icon', models.URLField(blank=True, null=True)),
                ('image', models.URLField(blank=True, null=True)),
                ('click_action', models.URLField(blank=True, null=True)),
                ('data', models.JSONField(blank=True, default=dict)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'fcm_notification_templates',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='TopicSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('topic', models.CharField(db_index=True, max_length=255)),
                ('is_subscribed', models.BooleanField(default=True)),
                ('subscribed_at', models.DateTimeField(auto_now_add=True)),
                ('unsubscribed_at', models.DateTimeField(blank=True, null=True)),
                ('device_token', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='topic_subscriptions', to='fcm_notifications.devicetoken')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='topic_subscriptions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'fcm_topic_subscriptions',
                'ordering': ['-subscribed_at'],
                'unique_together': {('device_token', 'topic')},
            },
        ),
        migrations.CreateModel(
            name='NotificationLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fcm_message_id', models.CharField(blank=True, max_length=255, null=True)),
                ('status', models.CharField(choices=[('success', 'Success'), ('failed', 'Failed')], max_length=20)),
                ('error_message', models.TextField(blank=True, null=True)),
                ('response_data', models.JSONField(blank=True, default=dict)),
                ('sent_at', models.DateTimeField(auto_now_add=True)),
                ('device_token', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='fcm_notifications.devicetoken')),
                ('notification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='fcm_notifications.notification')),
            ],
            options={
                'db_table': 'fcm_notification_logs',
                'ordering': ['-sent_at'],
            },
        ),
        migrations.AddIndex(
            model_name='topicsubscription',
            index=models.Index(fields=['topic', 'is_subscribed'], name='fcm_topic_s_topic_1f0a94_idx'),
        ),
        migrations.AddIndex(
            model_name='notificationlog',
            index=models.Index(fields=['notification', 'status'], name='fcm_notific_notific_e7d7aa_idx'),
        ),
        migrations.AddIndex(
            model_name='notificationlog',
            index=models.Index(fields=['device_token', '-sent_at'], name='fcm_notific_device__5c7d3e_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['status', '-created_at'], name='fcm_notific_status_5a0e0d_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['notification_type', '-created_at'], name='fcm_notific_notific_7f35a3_idx'),
        ),
        migrations.AddIndex(
            model_name='devicetoken',
            index=models.Index(fields=['user', 'is_active'], name='fcm_device__user_id_5b7f93_idx'),
        ),
        migrations.AddIndex(
            model_name='devicetoken',
            index=models.Index(fields=['platform', 'is_active'], name='fcm_device__platfor_4e3a42_idx'),
        ),
    ]
