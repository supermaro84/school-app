from django.contrib import admin

from .models import Book, ItemImage, Loan


class ItemImageInline(admin.TabularInline):
    model = ItemImage
    extra = 0


class LoanInline(admin.TabularInline):
    model = Loan
    extra = 0
    autocomplete_fields = ["borrower"]


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "isbn", "owner"]
    search_fields = ["title", "author", "isbn", "owner__username", "owner__last_name"]
    autocomplete_fields = ["owner"]
    exclude = ["category"]
    inlines = [ItemImageInline, LoanInline]


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ["item", "borrower", "lent_at", "due_date", "returned_at"]
    list_filter = ["returned_at"]
    search_fields = ["item__title", "borrower__username", "borrower__last_name"]
    autocomplete_fields = ["borrower"]
    raw_id_fields = ["item"]
