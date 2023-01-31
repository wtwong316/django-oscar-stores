from django.contrib.gis.db.models import Manager, PointField
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext as _
from oscar.apps.address.abstract_models import AbstractAddress
from oscar.core.utils import slugify

from sdfs.managers import SdfManager
from sdfs.utils import get_geodetic_srid


# Re-use Oscar's address model
class SdfAddress(AbstractAddress):
    sdf = models.OneToOneField(
        'sdfs.Sdf',
        models.CASCADE,
        verbose_name=_("Sdf"),
        related_name="address"
    )

    class Meta:
        abstract = True
        app_label = 'sdfs'

    @property
    def street(self):
        """
        Summary of the 3 line fields
        """
        return "\n".join(filter(bool, [self.line1, self.line2, self.line3]))


class SdfGroup(models.Model):
    name = models.CharField(_('Name'), max_length=100, unique=True)
    slug = models.SlugField(_('Slug'), max_length=100, unique=True)

    class Meta:
        abstract = True
        app_label = 'sdfs'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class SdfSdu(models.Model):
    name = models.CharField(_('AppId'), max_length=100, unique=True)
    #slug = models.SlugField(_('Slug'), max_length=100, unique=True)
    size = models.DecimalField(_('Size in sqft'), decimal_places=2, max_digits=10, default=0.0, null=True)
    household_size = models.IntegerField(_('Household size'), default=1)
    rent = models.DecimalField(_('Rent'), decimal_places=2, max_digits=10, default=0.0, null=True)
    has_contract = models.BooleanField(_('Has contract'), default=False)
    has_individual_kitchen = models.BooleanField(_('Has individual kitchen'), default=False)
    has_individual_bath = models.BooleanField(_('Has individual bath'), default=False)
    has_exterior_window = models.BooleanField(_('Has exterior windows'), default=False)
    internal_grading = models.IntegerField(_('Internal grading'), default=0)
    is_active = models.BooleanField(_("Is active"), default=True)
    sdfId = models.ForeignKey(
        'sdfs.Sdf',
        related_name='Sdf',
        verbose_name=_("SdfId"),
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    class Meta:
        abstract = True
        verbose_name = _("Sdf Sdu details")
        verbose_name_plural = _("Sdf Sdu details")
        app_label = 'sdfs'

    objects = Manager()

    def save(self, *args, **kwargs):
#        if not self.slug:
#            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Sdf(models.Model):
    name = models.CharField(_('SurveyId'), max_length=100)
    slug = models.SlugField(_('Slug'), max_length=100, null=True)

    # Contact details
    #manager_name = models.CharField(
    #    _('Manager name'), max_length=200, blank=True, null=True)
    #phone = models.CharField(_('Phone'), max_length=64, blank=True, null=True)
    #email = models.CharField(_('Email'), max_length=100, blank=True, null=True)

    #reference = models.CharField(
    #    _("Reference"),
    #    max_length=32,
    #    unique=True,
    #    null=True,
    #    blank=True,
    #    help_text=_("A reference number that uniquely identifies this sdf"))

    image = models.ImageField(
        _("Image"),
        upload_to="uploads/sdf-images",
        blank=True, null=True)
    description = models.CharField(
        _("Description"),
        max_length=2000,
        blank=True, null=True)
    location = PointField(
        _("Location"),
        srid=get_geodetic_srid(),
    )

    group = models.ForeignKey(
        'sdfs.SdfGroup',
        models.PROTECT,
        related_name='sdfs',
        verbose_name=_("Group"),
        null=True,
        blank=True
    )

    #is_pickup_sdf = models.BooleanField(_("Is pickup sdf"), default=True)
    is_active = models.BooleanField(_("Is active"), default=True)

    objects = SdfManager()

    class Meta:
        abstract = True
    #    ordering = ('name',)
        app_label = 'sdfs'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    #def __str__(self):
    #    return self.name

    def get_absolute_url(self):
        return reverse('sdfs:detail', kwargs={'dummyslug': self.slug,
                                                'pk': self.pk})

    #@property
    #def has_contact_details(self):
    #    return any([self.manager_name, self.phone, self.email])

"""
class OpeningPeriod(models.Model):
    PERIOD_FORMAT = _("%(start)s - %(end)s")
    (MONDAY, TUESDAY, WEDNESDAY, THURSDAY,
     FRIDAY, SATURDAY, SUNDAY, PUBLIC_HOLIDAYS) = range(1, 9)
    WEEK_DAYS = {
        MONDAY: _("Monday"),
        TUESDAY: _("Tuesday"),
        WEDNESDAY: _("Wednesday"),
        THURSDAY: _("Thursday"),
        FRIDAY: _("Friday"),
        SATURDAY: _("Saturday"),
        SUNDAY: _("Sunday"),
        PUBLIC_HOLIDAYS: _("Public Holidays")
    }
    sdf = models.ForeignKey('sdfs.Sdf', models.CASCADE, verbose_name=_("Sdf"),
                              related_name='opening_periods')

    weekday_choices = [(k, v) for k, v in WEEK_DAYS.items()]
    weekday = models.PositiveIntegerField(
        _("Weekday"),
        choices=weekday_choices)
    start = models.TimeField(
        _("Start"),
        null=True,
        blank=True,
        help_text=_("Leaving start and end time empty is displayed as 'Closed'"))
    end = models.TimeField(
        _("End"),
        null=True,
        blank=True,
        help_text=_("Leaving start and end time empty is displayed as 'Closed'"))

   def __str__(self):
       return "%s: %s to %s" % (self.weekday, self.start, self.end)

    class Meta:
        abstract = True
        ordering = ['weekday']
        verbose_name = _("Opening period")
        verbose_name_plural = _("Opening periods")
        app_label = 'sdfs'

    def clean(self):
        if self.start and self.end and self.end <= self.start:
            raise ValidationError(_("Start must be before end"))
"""


class SdfStock(models.Model):
    sdf = models.ForeignKey(
        'sdfs.Sdf',
        models.CASCADE,
        verbose_name=_("Sdf"),
        related_name='stock'
    )
    product = models.ForeignKey(
        'catalogue.Product',
        models.CASCADE,
        verbose_name=_("Product"),
        related_name="sdf_stock"
    )

    # Stock level information
    num_in_stock = models.PositiveIntegerField(
        _("Number in stock"),
        default=0,
        blank=True,
        null=True)

    # The amount of stock allocated in sdf but not fed back to the master
    num_allocated = models.IntegerField(
        _("Number allocated"),
        default=0,
        blank=True,
        null=True)

    location = models.CharField(
        _("In sdf location"),
        max_length=50,
        blank=True,
        null=True)

    # Date information
    date_created = models.DateTimeField(
        _("Date created"),
        auto_now_add=True)
    date_updated = models.DateTimeField(
        _("Date updated"),
        auto_now=True,
        db_index=True)

    class Meta:
        abstract = True
        verbose_name = _("Sdf stock record")
        verbose_name_plural = _("Sdf stock records")
        unique_together = ("sdf", "product")
        app_label = 'sdfs'

    objects = Manager()

    def __str__(self):
        if self.sdf and self.product:
            return "%s @ %s" % (self.product.title, self.sdf.name)
        return "Sdf Stock"

    @property
    def is_available_to_buy(self):
        return self.num_in_stock > self.num_allocated

