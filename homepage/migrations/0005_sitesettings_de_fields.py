from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('homepage', '0004_contactsubmission_cta_btn_primary_de_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='hero_eyebrow_de',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='hero_headline_line1_de',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='hero_headline_line2_de',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='hero_headline_line3_de',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='hero_subtext_de',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='hero_cta_primary_de',
            field=models.CharField(blank=True, max_length=60),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='hero_cta_secondary_de',
            field=models.CharField(blank=True, max_length=60),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='hero_badge_text_de',
            field=models.CharField(blank=True, max_length=60),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='cta_label_de',
            field=models.CharField(blank=True, max_length=60),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='cta_headline_line1_de',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='cta_headline_line2_de',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='cta_subtext_de',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
                    model_name='sitesettings',
                    name='cta_btn_primary_de',
                    field=models.CharField(blank=True, max_length=60),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='cta_btn_secondary_de',
            field=models.CharField(blank=True, max_length=60),
        ),
    ]