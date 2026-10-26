from django.db import models


class Medicine(models.Model):
    brand_name = models.CharField(max_length=120, db_index=True)
    salt = models.CharField(max_length=200)
    strength = models.CharField(max_length=30)
    form = models.CharField(max_length=30)
    pack_size = models.PositiveIntegerField(default=1)
    manufacturer = models.CharField(max_length=120, blank=True)
    brand_price = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        unique_together = ("brand_name", "strength", "form")

    def __str__(self):
        return f"{self.brand_name} ({self.salt} {self.strength})"


class GenericEquivalent(models.Model):
    salt = models.CharField(max_length=200)
    strength = models.CharField(max_length=30)
    form = models.CharField(max_length=30)
    pack_size = models.PositiveIntegerField(default=1)
    generic_name = models.CharField(max_length=200)
    generic_price = models.DecimalField(max_digits=8, decimal_places=2)
    source = models.CharField(max_length=200, default="sample data")

    class Meta:
        unique_together = ("salt", "strength", "form")

    def __str__(self):
        return self.generic_name


class RestrictedSalt(models.Model):
    salt = models.CharField(max_length=200, unique=True)
    reason = models.CharField(max_length=300)

    def __str__(self):
        return self.salt


class Analysis(models.Model):
    input_text = models.TextField(blank=True)
    extracted_json = models.JSONField(null=True, blank=True)
    result_json = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)