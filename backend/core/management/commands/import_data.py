import csv
from decimal import Decimal
from django.conf import settings
from django.core.management.base import BaseCommand
from core.models import Medicine, GenericEquivalent, RestrictedSalt

DATA_DIR = settings.BASE_DIR.parent / "data"

RESTRICTED = [
    ("levothyroxine", "Narrow therapeutic index; dose and brand changes need doctor supervision"),
    ("warfarin", "Narrow therapeutic index; needs INR monitoring"),
    ("levetiracetam", "Antiepileptic; switching needs doctor approval"),
    ("phenytoin", "Antiepileptic; narrow therapeutic index"),
]


def clean(value):
    return value.strip().lower()


class Command(BaseCommand):
    help = "Load medicines, generics and restricted salts from CSV files"

    def handle(self, *args, **options):
        with open(DATA_DIR / "medicines.csv", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                Medicine.objects.update_or_create(
                    brand_name=row["brand_name"].strip(),
                    strength=clean(row["strength"]),
                    form=clean(row["form"]),
                    defaults={
                        "salt": clean(row["salt"]),
                        "pack_size": int(row["pack_size"]),
                        "brand_price": Decimal(row["brand_price"]),
                    },
                )

        with open(DATA_DIR / "generics.csv", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                GenericEquivalent.objects.update_or_create(
                    salt=clean(row["salt"]),
                    strength=clean(row["strength"]),
                    form=clean(row["form"]),
                    defaults={
                        "generic_name": row["generic_name"].strip(),
                        "pack_size": int(row["pack_size"]),
                        "generic_price": Decimal(row["generic_price"]),
                        "source": row.get("source", "sample data").strip(),
                    },
                )

        for salt, reason in RESTRICTED:
            RestrictedSalt.objects.update_or_create(salt=salt, defaults={"reason": reason})

        self.stdout.write(self.style.SUCCESS(
            f"Medicines: {Medicine.objects.count()}, "
            f"Generics: {GenericEquivalent.objects.count()}, "
            f"Restricted: {RestrictedSalt.objects.count()}"
        ))