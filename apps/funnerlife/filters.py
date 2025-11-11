from django.db.models import Count, Q

class FunnerLifeServiceFilter:
    """Encapsulates filtering, sorting, and aggregation logic for FunnerLife services."""

    def __init__(self, queryset, params):
        self.queryset = queryset
        self.params = params

    def filter_queryset(self):
        qs = self.queryset

        # ---- Filter by category ----
        category = self.params.get("category")
        if category:
            qs = qs.filter(category__iexact=category)

        # ---- Search by name ----
        search = self.params.get("search")
        if search:
            qs = qs.filter(name__icontains=search)

        # ---- Sorting ----
        sort = self.params.get("sort", "category")  # default sort by category
        valid_sorts = ["name", "-name", "price", "-price", "category", "-category"]
        if sort in valid_sorts:
            qs = qs.order_by(sort)

        return qs

    def get_category_counts(self):
        """Return total count of services per category."""
        if self.params.get("counts") == "true":
            return (
                self.queryset.values("category")
                .annotate(total=Count("id"))
                .order_by("category")
            )
        return None
