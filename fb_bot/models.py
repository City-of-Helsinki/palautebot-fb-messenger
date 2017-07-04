# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator


class Feedback(models.Model):

    user_id = models.CharField(max_length=2048)
    phase = models.IntegerField(default=0, validators=[
        MaxValueValidator(9),MinValueValidator(0)])
    message = models.CharField(max_length=5000)
    source_created_at = models.DateTimeField(
        default='2017-05-17T09:00:00+0000'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

# vim: tabstop=2 expandtab shiftwidth=2 softtabstop=2
