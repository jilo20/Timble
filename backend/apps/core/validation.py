import re

from django.core.exceptions import ValidationError
from django.db import models


def academic_year(value):
    if not re.fullmatch(r"\d{4}-\d{4}", value) or int(value[5:]) - int(value[:4]) != 1:
        raise ValidationError("Use consecutive years: YYYY-YYYY.")


def code(value):
    return " ".join(str(value).strip().upper().split())


class ValidatedModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
