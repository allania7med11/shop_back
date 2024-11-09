from django.db import models
from django.db.models import Case, DecimalField, F, When


class ProductQuerySet(models.QuerySet):
    def with_current_price(self):
        return self.annotate(
            current_price=Case(
                When(
                    discount__isnull=False,
                    discount__active=True,
                    then=F("price") * (1 - F("discount__percent") / 100),
                ),
                default=F("price"),
                output_field=DecimalField(),
            )
        )


class ProductManager(models.Manager):
    def get_queryset(self):
        return ProductQuerySet(
            model=self.model,
            using=self._db,
        ).with_current_price()
