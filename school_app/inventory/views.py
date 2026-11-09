from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Prefetch, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from media.forms import save_images

from .forms import CATEGORY_FORMS, LendForm
from .models import Item, ItemImage, Loan

TABS = ("mine", "borrowed", "catalog")
PER_PAGE = 20


def items_with_loans():
    """Items with what the lists show, without a query per item."""
    return Item.objects.select_related("owner", "book").prefetch_related(
        "images",
        Prefetch(
            "loans",
            queryset=Loan.objects.filter(returned_at__isnull=True).select_related("borrower"),
            to_attr="open_loans",
        ),
    )


def search(items, term):
    if not term:
        return items
    return items.filter(
        Q(title__icontains=term)
        | Q(description__icontains=term)
        | Q(book__author__icontains=term)
        | Q(book__isbn__icontains=term.replace("-", "").replace(" ", ""))
    )


@login_required
def inventory_list(request):
    """My items, items I have borrowed, or everyone's items (the catalogue)."""
    tab = request.GET.get("tab", "mine")
    if tab not in TABS:
        tab = "mine"
    term = request.GET.get("q", "").strip()
    items = items_with_loans()
    if tab == "mine":
        items = items.filter(owner=request.user)
    elif tab == "borrowed":
        items = items.filter(loans__borrower=request.user, loans__returned_at__isnull=True)
    items = search(items, term)
    page = Paginator(items, PER_PAGE).get_page(request.GET.get("page"))
    return render(
        request,
        "inventory.html",
        {
            "tab": tab,
            "search_term": term,
            "items_page": page,
            "counts": {
                "mine": Item.objects.filter(owner=request.user).count(),
                "borrowed": Loan.objects.filter(borrower=request.user, returned_at__isnull=True).count(),
            },
        },
    )


@login_required
def item_detail(request, pk):
    item = get_object_or_404(items_with_loans(), pk=pk)
    is_owner = item.owner == request.user
    context = {
        "item": item,
        "details": item.details,
        "is_owner": is_owner,
        "loan": item.active_loan,
    }
    if is_owner:
        context["lend_form"] = LendForm(owner=request.user)
        context["history"] = item.loans.select_related("borrower").exclude(returned_at__isnull=True)[:10]
    return render(request, "item_detail.html", context)


def category_or_404(category):
    try:
        category = Item.Category(category)
    except ValueError:
        raise Http404
    return category, CATEGORY_FORMS[category]


@login_required
def item_create(request, category=Item.Category.BOOK):
    category, form_class = category_or_404(category)
    form = form_class(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            form.instance.owner = request.user
            item = form.save()
            save_images(ItemImage, form.cleaned_data["images"], item=item)
        messages.success(request, _("Item added to your inventory."))
        return redirect("item_detail", pk=item.pk)
    return render(request, "item_form.html", {"form": form, "category": category})


@login_required
def item_edit(request, pk):
    item = get_object_or_404(Item, pk=pk, owner=request.user)
    details = item.details
    _category, form_class = category_or_404(item.category)
    form = form_class(request.POST or None, request.FILES or None, instance=details)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            form.save()
            save_images(ItemImage, form.cleaned_data["images"], item=item)
        messages.success(request, _("Item saved."))
        return redirect("item_detail", pk=item.pk)
    return render(
        request,
        "item_form.html",
        {"form": form, "category": item.category, "item": item, "images": item.images.all()},
    )


@login_required
@require_POST
def item_delete(request, pk):
    item = get_object_or_404(Item, pk=pk, owner=request.user)
    if not item.is_available:
        messages.error(request, _("This item is lent out. Mark it as returned before deleting it."))
        return redirect("item_detail", pk=item.pk)
    item.delete()
    messages.success(request, _("Item deleted."))
    return redirect("inventory")


@login_required
@require_POST
def item_lend(request, pk):
    item = get_object_or_404(Item, pk=pk, owner=request.user)
    form = LendForm(request.POST, owner=request.user)
    if not item.is_available:
        messages.error(request, _("This item is already lent out."))
    elif form.is_valid():
        try:
            with transaction.atomic():
                Loan.objects.create(
                    item=item, borrower=form.cleaned_data["borrower"], due_date=form.cleaned_data["due_date"]
                )
        except IntegrityError:  # lent at the same moment in another tab
            messages.error(request, _("This item is already lent out."))
        else:
            borrower = form.cleaned_data["borrower"]
            messages.success(
                request,
                _("Lent to %(name)s.") % {"name": borrower.get_full_name() or borrower.username},
            )
    else:
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)
    return redirect("item_detail", pk=item.pk)


@login_required
@require_POST
def item_return(request, pk):
    """The owner confirms the item is back."""
    item = get_object_or_404(Item, pk=pk, owner=request.user)
    updated = Loan.objects.filter(item=item, returned_at__isnull=True).update(returned_at=timezone.now())
    if updated:
        messages.success(request, _("Marked as returned."))
    return redirect("item_detail", pk=item.pk)


@login_required
@require_POST
def item_image_delete(request, pk):
    image = get_object_or_404(ItemImage, pk=pk, item__owner=request.user)
    item_pk = image.item_id
    image.delete()
    messages.success(request, _("Photo deleted."))
    return redirect("item_edit", pk=item_pk)
