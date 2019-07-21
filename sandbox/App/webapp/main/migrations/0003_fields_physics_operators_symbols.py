# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-12-09 19:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_auto_20170702_2301'),
    ]

    operations = [
        migrations.CreateModel(
            name='FIELDS_PHYSICS',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('field', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='OPERATORS',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('operator', models.IntegerField()),
                ('number_of_args', models.IntegerField()),
                ('input_line_count', models.IntegerField()),
                ('output_line_count', models.IntegerField()),
                ('latex_function_desc', models.CharField(max_length=250)),
            ],
        ),
        migrations.CreateModel(
            name='SYMBOLS',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('symbol', models.IntegerField()),
                ('type', models.IntegerField()),
                ('value', models.IntegerField()),
                ('units', models.IntegerField()),
                ('description', models.CharField(max_length=250)),
                ('cas_sympy', models.CharField(max_length=250)),
            ],
        ),
    ]