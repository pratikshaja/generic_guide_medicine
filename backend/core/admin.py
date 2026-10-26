from django.contrib import admin
from .models import Medicine, GenericEquivalent, RestrictedSalt, Analysis

admin.site.register(Medicine)
admin.site.register(GenericEquivalent)
admin.site.register(RestrictedSalt)
admin.site.register(Analysis)