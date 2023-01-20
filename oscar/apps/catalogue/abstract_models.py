import logging
import os
from datetime import date, datetime

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles.finders import find
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.files.base import File
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Count, Exists, OuterRef, Sum
from django.db.models.fields import Field
from django.db.models.lookups import StartsWith
from django.template.defaultfilters import striptags
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext, pgettext_lazy
from treebeard.mp_tree import MP_Node

from oscar.core.loading import get_class, get_classes, get_model
from oscar.core.utils import slugify
from oscar.core.validators import non_python_keyword
from oscar.models.fields import AutoSlugField, NullCharField
from oscar.models.fields.slugfield import SlugField
from oscar.utils.models import get_image_upload_path

CategoryQuerySet, SduQuerySet = get_classes(
    'catalogue.managers', ['CategoryQuerySet', 'SduQuerySet'])
SduAttributesContainer = get_class(
    'catalogue.sdu_attributes', 'SduAttributesContainer')


class ReverseStartsWith(StartsWith):
    """
    Adds a new lookup method to the django query language, that allows the
    following syntax::

        henk__rstartswith="koe"

    The regular version of startswith::

        henk__startswith="koe"

     Would be about the same as the python statement::

        henk.startswith("koe")

    ReverseStartsWith will flip the right and left hand side of the expression,
    effectively making this the same query as::

    "koe".startswith(henk)
    """
    def process_rhs(self, compiler, connection):
        return super().process_lhs(compiler, connection)

    def process_lhs(self, compiler, connection, lhs=None):
        if lhs is not None:
            raise Exception("Flipped process_lhs does not accept lhs argument")
        return super().process_rhs(compiler, connection)


Field.register_lookup(ReverseStartsWith, "rstartswith")


class AbstractSduClass(models.Model):
    """
    Used for defining options and attributes for a subset of sdus.
    E.g. Books, DVDs and Toys. A sdu can only belong to one sdu class.

    At least one sdu class must be created when setting up a new
    Oscar deployment.

    Not necessarily equivalent to top-level categories but usually will be.
    """
    name = models.CharField(_('Name'), max_length=128)
    slug = AutoSlugField(_('Slug'), max_length=128, unique=True,
                         populate_from='name')

    #: Some sdu type don't require shipping (e.g. digital sdus) - we use
    #: this field to take some shortcuts in the checkout.
    #requires_shipping = models.BooleanField(_("Requires shipping?"),
    #                                        default=True)

    #: Digital sdus generally don't require their stock levels to be
    #: tracked.
    #track_stock = models.BooleanField(_("Track stock levels?"), default=True)

    #: These are the options (set by the user when they add to basket) for this
    #: item class.  For instance, a sdu class of "SMS message" would always
    #: require a message to be specified before it could be bought.
    #: Note that you can also set options on a per-sdu level.
    options = models.ManyToManyField(
        'catalogue.Option', blank=True, verbose_name=_("Options"))

    class Meta:
        abstract = True
        app_label = 'catalogue'
        ordering = ['name']
        verbose_name = _("Sdu class")
        verbose_name_plural = _("Sdu classes")

    def __str__(self):
        return self.name

    @property
    def has_attributes(self):
        return self.attributes.exists()


class AbstractCategory(MP_Node):
    """
    A sdu category. Merely used for navigational purposes; has no
    effects on business logic.

    Uses :py:mod:`django-treebeard`.
    """
    #: Allow comparison of categories on a limited number of fields by ranges.
    #: When the Category model is overwritten to provide CMS content, defining
    #: this avoids fetching a lot of unneeded extra data from the database.
    COMPARISON_FIELDS = ('pk', 'path', 'depth')

    name = models.CharField(_('Name'), max_length=255, db_index=True)
    description = models.TextField(_('Description'), blank=True)
    meta_title = models.CharField(_('Meta title'), max_length=255, blank=True, null=True)
    meta_description = models.TextField(_('Meta description'), blank=True, null=True)
    image = models.ImageField(_('Image'), upload_to='categories', blank=True,
                              null=True, max_length=255)
    slug = SlugField(_('Slug'), max_length=255, db_index=True)

    is_public = models.BooleanField(
        _('Is public'),
        default=True,
        db_index=True,
        help_text=_("Show this category in search results and catalogue listings."))

    ancestors_are_public = models.BooleanField(
        _('Ancestor categories are public'),
        default=True,
        db_index=True,
        help_text=_("The ancestors of this category are public"))

    _slug_separator = '/'
    _full_name_separator = ' > '

    objects = CategoryQuerySet.as_manager()

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        """
        Returns a string representation of the category and it's ancestors,
        e.g. 'Books > Non-fiction > Essential programming'.

        It's rarely used in Oscar, but used to be stored as a CharField and is
        hence kept for backwards compatibility. It's also sufficiently useful
        to keep around.
        """
        names = [category.name for category in self.get_ancestors_and_self()]
        return self._full_name_separator.join(names)

    def get_full_slug(self, parent_slug=None):
        if self.is_root():
            return self.slug

        cache_key = self.get_url_cache_key()
        full_slug = cache.get(cache_key)
        if full_slug is None:
            parent_slug = parent_slug if parent_slug is not None else self.get_parent().full_slug
            full_slug = "%s%s%s" % (parent_slug, self._slug_separator, self.slug)
            cache.set(cache_key, full_slug)

        return full_slug

    @property
    def full_slug(self):
        """
        Returns a string of this category's slug concatenated with the slugs
        of it's ancestors, e.g. 'books/non-fiction/essential-programming'.

        Oscar used to store this as in the 'slug' model field, but this field
        has been re-purposed to only store this category's slug and to not
        include it's ancestors' slugs.
        """
        return self.get_full_slug()

    def generate_slug(self):
        """
        Generates a slug for a category. This makes no attempt at generating
        a unique slug.
        """
        return slugify(self.name)

    def save(self, *args, **kwargs):
        """
        Oscar traditionally auto-generated slugs from names. As that is
        often convenient, we still do so if a slug is not supplied through
        other means. If you want to control slug creation, just create
        instances with a slug already set, or expose a field on the
        appropriate forms.
        """
        if not self.slug:
            self.slug = self.generate_slug()
        super().save(*args, **kwargs)

    def set_ancestors_are_public(self):
        # Update ancestors_are_public for the sub tree.
        # note: This doesn't trigger a new save for each instance, rather
        # just a SQL update.
        included_in_non_public_subtree = self.__class__.objects.filter(
            is_public=False, path__rstartswith=OuterRef("path"), depth__lt=OuterRef("depth")
        )
        self.get_descendants_and_self().update(
            ancestors_are_public=Exists(
                included_in_non_public_subtree.values("id"), negated=True))

        # Correctly populate ancestors_are_public
        self.refresh_from_db()

    @classmethod
    def fix_tree(cls, destructive=False):
        super().fix_tree(destructive)
        for node in cls.get_root_nodes():
            # ancestors_are_public *must* be True for root nodes, or all trees
            # will become non-public
            if not node.ancestors_are_public:
                node.ancestors_are_public = True
                node.save()
            else:
                node.set_ancestors_are_public()

    def get_meta_title(self):
        return self.meta_title or self.name

    def get_meta_description(self):
        return self.meta_description or striptags(self.description)

    def get_ancestors_and_self(self):
        """
        Gets ancestors and includes itself. Use treebeard's get_ancestors
        if you don't want to include the category itself. It's a separate
        function as it's commonly used in templates.
        """
        if self.is_root():
            return [self]

        return list(self.get_ancestors()) + [self]

    def get_descendants_and_self(self):
        """
        Gets descendants and includes itself. Use treebeard's get_descendants
        if you don't want to include the category itself. It's a separate
        function as it's commonly used in templates.
        """
        return self.get_tree(self)

    def get_url_cache_key(self):
        current_locale = get_language()
        cache_key = 'CATEGORY_URL_%s_%s' % (current_locale, self.pk)
        return cache_key

    def _get_absolute_url(self, parent_slug=None):
        """
        Our URL scheme means we have to look up the category's ancestors. As
        that is a bit more expensive, we cache the generated URL. That is
        safe even for a stale cache, as the default implementation of
        SduCategoryView does the lookup via primary key anyway. But if
        you change that logic, you'll have to reconsider the caching
        approach.
        """
        return reverse('catalogue:category', kwargs={
            'category_slug': self.get_full_slug(parent_slug=parent_slug), 'pk': self.pk
        })

    def get_absolute_url(self):
        return self._get_absolute_url()

    class Meta:
        abstract = True
        app_label = 'catalogue'
        ordering = ['path']
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

    def has_children(self):
        return self.get_num_children() > 0

    def get_num_children(self):
        return self.get_children().count()


class AbstractSduCategory(models.Model):
    """
    Joining model between sdus and categories. Exists to allow customising.
    """
    sdu = models.ForeignKey(
        'catalogue.Sdu',
        on_delete=models.CASCADE,
        verbose_name=_("Sdu"))
    category = models.ForeignKey(
        'catalogue.Category',
        on_delete=models.CASCADE,
        verbose_name=_("Category"))

    class Meta:
        abstract = True
        app_label = 'catalogue'
        ordering = ['sdu', 'category']
        unique_together = ('sdu', 'category')
        verbose_name = _('Sdu category')
        verbose_name_plural = _('Sdu categories')

    def __str__(self):
        return "<sducategory for sdu '%s'>" % self.sdu


class AbstractSdu(models.Model):
    """
    The base sdu object

    There's three kinds of sdus; they're distinguished by the structure
    field.

    - A stand alone sdu. Regular sdu that lives by itself.
    - A child sdu. All child sdus have a parent sdu. They're a
      specific version of the parent.
    - A parent sdu. It essentially represents a set of sdus.

    An example could be a yoga course, which is a parent sdu. The different
    times/locations of the courses would be associated with the child sdus.
    """
    STANDALONE, PARENT, CHILD = 'standalone', 'parent', 'child'
    STRUCTURE_CHOICES = (
        (STANDALONE, _('Stand-alone sdu')),
        (PARENT, _('Parent sdu')),
        (CHILD, _('Child sdu'))
    )
    structure = models.CharField(
        _("Sdu structure"), max_length=10, choices=STRUCTURE_CHOICES,
        default=STANDALONE)

    is_public = models.BooleanField(
        _('Is public'),
        default=True,
        db_index=True,
        help_text=_("Show this sdu in search results and catalogue listings."))

    upc = NullCharField(
        _("UPC"), max_length=64, blank=True, null=True, unique=True,
        help_text=_("Universal Sdu Code (UPC) is an identifier for "
                    "a sdu which is not specific to a particular "
                    " supplier. Eg an ISBN for a book."))

    parent = models.ForeignKey(
        'self',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='children',
        verbose_name=_("Parent sdu"),
        help_text=_("Only choose a parent sdu if you're creating a child "
                    "sdu.  For example if this is a size "
                    "4 of a particular t-shirt.  Leave blank if this is a "
                    "stand-alone sdu (i.e. there is only one version of"
                    " this sdu)."))

    # Title is mandatory for canonical sdus but optional for child sdus
    title = models.CharField(pgettext_lazy('Sdu title', 'Title'),
                             max_length=255, blank=True)
    slug = SlugField(_('Slug'), max_length=255, unique=False)
    description = models.TextField(_('Description'), blank=True)
    meta_title = models.CharField(_('Meta title'), max_length=255, blank=True, null=True)
    meta_description = models.TextField(_('Meta description'), blank=True, null=True)

    #: "Kind" of sdu, e.g. T-Shirt, Book, etc.
    #: None for child sdus, they inherit their parent's sdu class
    sdu_class = models.ForeignKey(
        'catalogue.SduClass',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        verbose_name=_('Sdu type'), related_name="sdus",
        help_text=_("Choose what type of sdu this is"))
    attributes = models.ManyToManyField(
        'catalogue.SduAttribute',
        through='SduAttributeValue',
        verbose_name=_("Attributes"),
        help_text=_("A sdu attribute is something that this sdu may "
                    "have, such as a size, as specified by its class"))
    #: It's possible to have options sdu class-wide, and per sdu.
    sdu_options = models.ManyToManyField(
        'catalogue.Option', blank=True, verbose_name=_("Sdu options"),
        help_text=_("Options are values that can be associated with a item "
                    "when it is added to a renter's basket.  This could be "
                    "something like a personalised message to be printed on "
                    "a T-shirt."))

    recommended_sdus = models.ManyToManyField(
        'catalogue.Sdu', through='SduRecommendation', blank=True,
        verbose_name=_("Recommended sdus"),
        help_text=_("These are sdus that are recommended to accompany the "
                    "main sdu."))

    # Denormalised sdu rating - used by reviews app.
    # Sdu has no ratings if rating is None
    rating = models.FloatField(_('Rating'), null=True, editable=False)

    date_created = models.DateTimeField(
        _("Date created"), auto_now_add=True, db_index=True)

    # This field is used by Haystack to reindex search
    date_updated = models.DateTimeField(
        _("Date updated"), auto_now=True, db_index=True)

    categories = models.ManyToManyField(
        'catalogue.Category', through='SduCategory',
        verbose_name=_("Categories"))

    #: Determines if a sdu may be used in an offer. It is illegal to
    #: discount some types of sdu (e.g. ebooks) and this field helps
    #: merchants from avoiding discounting such sdus
    #: Note that this flag is ignored for child sdus; they inherit from
    #: the parent sdu.
    is_discountable = models.BooleanField(
        _("Is discountable?"), default=True, help_text=_(
            "This flag indicates if this sdu can be used in an offer "
            "or not"))

    objects = SduQuerySet.as_manager()

    class Meta:
        abstract = True
        app_label = 'catalogue'
        ordering = ['-date_created']
        verbose_name = _('Sdu')
        verbose_name_plural = _('Sdus')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attr = SduAttributesContainer(sdu=self)

    def __str__(self):
        if self.title:
            return self.title
        if self.attribute_summary:
            return "%s (%s)" % (self.get_title(), self.attribute_summary)
        else:
            return self.get_title()

    def get_absolute_url(self):
        """
        Return a sdu's absolute URL
        """
        return reverse('catalogue:detail',
                       kwargs={'sdu_slug': self.slug, 'pk': self.id})

    def clean(self):
        """
        Validate a sdu. Those are the rules:

        +---------------+-------------+--------------+--------------+
        |               | stand alone | parent       | child        |
        +---------------+-------------+--------------+--------------+
        | title         | required    | required     | optional     |
        +---------------+-------------+--------------+--------------+
        | sdu class | required    | required     | must be None |
        +---------------+-------------+--------------+--------------+
        | parent        | forbidden   | forbidden    | required     |
        +---------------+-------------+--------------+--------------+
        | stockrecords  | 0 or more   | forbidden    | 0 or more    |
        +---------------+-------------+--------------+--------------+
        | categories    | 1 or more   | 1 or more    | forbidden    |
        +---------------+-------------+--------------+--------------+
        | attributes    | optional    | optional     | optional     |
        +---------------+-------------+--------------+--------------+
        | rec. sdus | optional    | optional     | unsupported  |
        +---------------+-------------+--------------+--------------+
        | options       | optional    | optional     | forbidden    |
        +---------------+-------------+--------------+--------------+

        Because the validation logic is quite complex, validation is delegated
        to the sub method appropriate for the sdu's structure.
        """
        getattr(self, '_clean_%s' % self.structure)()
        if not self.is_parent:
            self.attr.validate_attributes()

    def _clean_standalone(self):
        """
        Validates a stand-alone sdu
        """
        if not self.title:
            raise ValidationError(_("Your sdu must have a title."))
        if not self.sdu_class:
            raise ValidationError(_("Your sdu must have a sdu class."))
        if self.parent_id:
            raise ValidationError(_("Only child sdus can have a parent."))

    def _clean_child(self):
        """
        Validates a child sdu
        """
        if not self.parent_id:
            raise ValidationError(_("A child sdu needs a parent."))
        if self.parent_id and not self.parent.is_parent:
            raise ValidationError(
                _("You can only assign child sdus to parent sdus."))
        if self.sdu_class:
            raise ValidationError(
                _("A child sdu can't have a sdu class."))
        if self.pk and self.categories.exists():
            raise ValidationError(
                _("A child sdu can't have a category assigned."))
        # Note that we only forbid options on sdu level
        if self.pk and self.sdu_options.exists():
            raise ValidationError(
                _("A child sdu can't have options."))

    def _clean_parent(self):
        """
        Validates a parent sdu.
        """
        self._clean_standalone()
        if self.has_stockrecords:
            raise ValidationError(
                _("A parent sdu can't have stockrecords."))

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.get_title())
        super().save(*args, **kwargs)
        self.attr.save()

    # Properties

    @property
    def is_standalone(self):
        return self.structure == self.STANDALONE

    @property
    def is_parent(self):
        return self.structure == self.PARENT

    @property
    def is_child(self):
        return self.structure == self.CHILD

    def can_be_parent(self, give_reason=False):
        """
        Helps decide if a the sdu can be turned into a parent sdu.
        """
        reason = None
        if self.is_child:
            reason = _('The specified parent sdu is a child sdu.')
        if self.has_stockrecords:
            reason = _(
                "One can't add a child sdu to a sdu with stock"
                " records.")
        is_valid = reason is None
        if give_reason:
            return is_valid, reason
        else:
            return is_valid

    @property
    def options(self):
        """
        Returns a set of all valid options for this sdu.
        It's possible to have options sdu class-wide, and per sdu.
        """
        pclass_options = self.get_sdu_class().options.all()
        return pclass_options | self.sdu_options.all()

    @cached_property
    def has_options(self):
        # Extracting annotated value with number of sdu class options
        # from sdu list queryset.
        has_sdu_class_options = getattr(self, 'has_sdu_class_options', None)
        has_sdu_options = getattr(self, 'has_sdu_options', None)
        if has_sdu_class_options is not None and has_sdu_options is not None:
            return has_sdu_class_options or has_sdu_options
        return self.options.exists()

    @property
    def is_shipping_required(self):
        #return self.get_sdu_class().requires_shipping
        return False

    @property
    def has_stockrecords(self):
        """
        Test if this sdu has any stockrecords
        """
        return self.stockrecords.exists()

    @property
    def num_stockrecords(self):
        return self.stockrecords.count()

    @property
    def attribute_summary(self):
        """
        Return a string of all of a sdu's attributes
        """
        attributes = self.get_attribute_values()
        pairs = [attribute.summary() for attribute in attributes]
        return ", ".join(pairs)

    def get_title(self):
        """
        Return a sdu's title or it's parent's title if it has no title
        """
        title = self.title
        if not title and self.parent_id:
            title = self.parent.title
        return title
    get_title.short_description = pgettext_lazy("Sdu title", "Title")

    def get_meta_title(self):
        title = self.meta_title
        if not title and self.is_child:
            title = self.parent.meta_title
        return title or self.get_title()
    get_meta_title.short_description = pgettext_lazy("Sdu meta title", "Meta title")

    def get_meta_description(self):
        meta_description = self.meta_description
        if not meta_description and self.is_child:
            meta_description = self.parent.meta_description
        return meta_description or striptags(self.description)
    get_meta_description.short_description = pgettext_lazy("Sdu meta description", "Meta description")

    def get_sdu_class(self):
        """
        Return a sdu's item class. Child sdus inherit their parent's.
        """
        if self.is_child:
            return self.parent.sdu_class
        else:
            return self.sdu_class
    get_sdu_class.short_description = _("Sdu class")

    def get_is_discountable(self):
        """
        At the moment, :py:attr:`.is_discountable` can't be set individually for child
        sdus; they inherit it from their parent.
        """
        if self.is_child:
            return self.parent.is_discountable
        else:
            return self.is_discountable

    def get_categories(self):
        """
        Return a sdu's public categories or parent's if there is a parent sdu.
        """
        if self.is_child:
            return self.parent.categories.browsable()
        else:
            return self.categories.browsable()
    get_categories.short_description = _("Categories")

    def get_attribute_values(self):
        attribute_values = self.attribute_values.all()
        if self.is_child:
            parent_attribute_values = self.parent.attribute_values.exclude(
                attribute__code__in=attribute_values.values("attribute__code")
            )
            return attribute_values | parent_attribute_values

        return attribute_values

    # Images

    def get_missing_image(self):
        """
        Returns a missing image object.
        """
        # This class should have a 'name' property so it mimics the Django file
        # field.
        return MissingSduImage()

    def get_all_images(self):
        if self.is_child and not self.images.exists() and self.parent_id is not None:
            return self.parent.images.all()
        return self.images.all()

    def primary_image(self):
        """
        Returns the primary image for a sdu. Usually used when one can
        only display one sdu image, e.g. in a list of sdus.
        """
        images = self.get_all_images()
        ordering = self.images.model.Meta.ordering
        if not ordering or ordering[0] != 'display_order':
            # Only apply order_by() if a custom model doesn't use default
            # ordering. Applying order_by() busts the prefetch cache of
            # the SduManager
            images = images.order_by('display_order')
        try:
            return images[0]
        except IndexError:
            # We return a dict with fields that mirror the key properties of
            # the SduImage class so this missing image can be used
            # interchangeably in templates.  Strategy pattern ftw!
            missing_image = self.get_missing_image()
            return {
                'original': missing_image.name,
                'caption': '',
                'is_missing': True}

    # Updating methods

    def update_rating(self):
        """
        Recalculate rating field
        """
        self.rating = self.calculate_rating()
        self.save()
    update_rating.alters_data = True

    def calculate_rating(self):
        """
        Calculate rating value
        """
        result = self.reviews.filter(
            status=self.reviews.model.APPROVED
        ).aggregate(
            sum=Sum('score'), count=Count('id'))
        reviews_sum = result['sum'] or 0
        reviews_count = result['count'] or 0
        rating = None
        if reviews_count > 0:
            rating = float(reviews_sum) / reviews_count
        return rating

    def has_review_by(self, user):
        if user.is_anonymous:
            return False
        return self.reviews.filter(user=user).exists()

    def is_review_permitted(self, user):
        """
        Determines whether a user may add a review on this sdu.

        Default implementation respects OSCAR_ALLOW_ANON_REVIEWS and only
        allows leaving one review per user and sdu.

        Override this if you want to alter the default behaviour; e.g. enforce
        that a user purchased the sdu to be allowed to leave a review.
        """
        if user.is_authenticated or settings.OSCAR_ALLOW_ANON_REVIEWS:
            return not self.has_review_by(user)
        else:
            return False

    @cached_property
    def num_approved_reviews(self):
        return self.reviews.approved().count()

    @property
    def sorted_recommended_sdus(self):
        """Keeping order by recommendation ranking."""
        return [r.recommendation for r in self.primary_recommendations
                                              .select_related('recommendation').all()]


class AbstractSduRecommendation(models.Model):
    """
    'Through' model for sdu recommendations
    """
    primary = models.ForeignKey(
        'catalogue.Sdu',
        on_delete=models.CASCADE,
        related_name='primary_recommendations',
        verbose_name=_("Primary sdu"))
    recommendation = models.ForeignKey(
        'catalogue.Sdu',
        on_delete=models.CASCADE,
        verbose_name=_("Recommended sdu"))
    ranking = models.PositiveSmallIntegerField(
        _('Ranking'), default=0, db_index=True,
        help_text=_('Determines inquiry of the sdus. A sdu with a higher'
                    ' value will appear before one with a lower ranking.'))

    class Meta:
        abstract = True
        app_label = 'catalogue'
        ordering = ['primary', '-ranking']
        unique_together = ('primary', 'recommendation')
        verbose_name = _('Sdu recommendation')
        verbose_name_plural = _('Sdu recomendations')


class AbstractSduAttribute(models.Model):
    """
    Defines an attribute for a sdu class. (For example, number_of_pages for
    a 'book' class)
    """
    sdu_class = models.ForeignKey(
        'catalogue.SduClass',
        blank=True,
        on_delete=models.CASCADE,
        related_name='attributes',
        null=True,
        verbose_name=_("Sdu type"))
    name = models.CharField(_('Name'), max_length=128)
    code = models.SlugField(
        _('Code'), max_length=128,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z_][0-9a-zA-Z_]*$',
                message=_(
                    "Code can only contain the letters a-z, A-Z, digits, "
                    "and underscores, and can't start with a digit.")),
            non_python_keyword
        ])

    # Attribute types
    TEXT = "text"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    FLOAT = "float"
    RICHTEXT = "richtext"
    DATE = "date"
    DATETIME = "datetime"
    OPTION = "option"
    MULTI_OPTION = "multi_option"
    ENTITY = "entity"
    FILE = "file"
    IMAGE = "image"
    TYPE_CHOICES = (
        (TEXT, _("Text")),
        (INTEGER, _("Integer")),
        (BOOLEAN, _("True / False")),
        (FLOAT, _("Float")),
        (RICHTEXT, _("Rich Text")),
        (DATE, _("Date")),
        (DATETIME, _("Datetime")),
        (OPTION, _("Option")),
        (MULTI_OPTION, _("Multi Option")),
        (ENTITY, _("Entity")),
        (FILE, _("File")),
        (IMAGE, _("Image")),
    )
    type = models.CharField(
        choices=TYPE_CHOICES, default=TYPE_CHOICES[0][0],
        max_length=20, verbose_name=_("Type"))

    option_group = models.ForeignKey(
        'catalogue.AttributeOptionGroup',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='sdu_attributes',
        verbose_name=_("Option Group"),
        help_text=_('Select an option group if using type "Option" or "Multi Option"'))
    required = models.BooleanField(_('Required'), default=False)

    class Meta:
        abstract = True
        app_label = 'catalogue'
        ordering = ['code']
        verbose_name = _('Sdu attribute')
        verbose_name_plural = _('Sdu attributes')
        unique_together = ('code', 'sdu_class')

    @property
    def is_option(self):
        return self.type == self.OPTION

    @property
    def is_multi_option(self):
        return self.type == self.MULTI_OPTION

    @property
    def is_file(self):
        return self.type in [self.FILE, self.IMAGE]

    def __str__(self):
        return self.name

    def clean(self):
        if self.type == self.BOOLEAN and self.required:
            raise ValidationError(_("Boolean attribute should not be required."))

    def _save_file(self, value_obj, value):
        # File fields in Django are treated differently, see
        # django.db.models.fields.FileField and method save_form_data
        if value is None:
            # No change
            return
        elif value is False:
            # Delete file
            value_obj.delete()
        else:
            # New uploaded file
            value_obj.value = value
            value_obj.save()

    def _save_multi_option(self, value_obj, value):
        # ManyToMany fields are handled separately
        if value is None:
            value_obj.delete()
            return
        try:
            count = value.count()
        except (AttributeError, TypeError):
            count = len(value)
        if count == 0:
            value_obj.delete()
        else:
            value_obj.value = value
            value_obj.save()

    def _save_value(self, value_obj, value):
        if value is None or value == '':
            value_obj.delete()
            return
        if value != value_obj.value:
            value_obj.value = value
            value_obj.save()

    def save_value(self, sdu, value):   # noqa: C901 too complex
        SduAttributeValue = get_model('catalogue', 'SduAttributeValue')
        try:
            value_obj = sdu.attribute_values.get(attribute=self)
        except SduAttributeValue.DoesNotExist:
            # FileField uses False for announcing deletion of the file
            # not creating a new value
            delete_file = self.is_file and value is False
            if value is None or value == '' or delete_file:
                return
            value_obj = SduAttributeValue.objects.create(
                sdu=sdu, attribute=self)

        if self.is_file:
            self._save_file(value_obj, value)
        elif self.is_multi_option:
            self._save_multi_option(value_obj, value)
        else:
            self._save_value(value_obj, value)

    def validate_value(self, value):
        validator = getattr(self, '_validate_%s' % self.type)
        validator(value)

    # Validators

    def _validate_text(self, value):
        if not isinstance(value, str):
            raise ValidationError(_("Must be str"))
    _validate_richtext = _validate_text

    def _validate_float(self, value):
        try:
            float(value)
        except ValueError:
            raise ValidationError(_("Must be a float"))

    def _validate_integer(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError(_("Must be an integer"))

    def _validate_date(self, value):
        if not (isinstance(value, datetime) or isinstance(value, date)):
            raise ValidationError(_("Must be a date or datetime"))

    def _validate_datetime(self, value):
        if not isinstance(value, datetime):
            raise ValidationError(_("Must be a datetime"))

    def _validate_boolean(self, value):
        if not type(value) == bool:
            raise ValidationError(_("Must be a boolean"))

    def _validate_entity(self, value):
        if not isinstance(value, models.Model):
            raise ValidationError(_("Must be a model instance"))

    def _validate_multi_option(self, value):
        try:
            values = iter(value)
        except TypeError:
            raise ValidationError(
                _("Must be a list or AttributeOption queryset"))
        # Validate each value as if it were an option
        # Pass in valid_values so that the DB isn't hit multiple times per iteration
        valid_values = self.option_group.options.values_list(
            'option', flat=True)
        for value in values:
            self._validate_option(value, valid_values=valid_values)

    def _validate_option(self, value, valid_values=None):
        if not isinstance(value, get_model('catalogue', 'AttributeOption')):
            raise ValidationError(
                _("Must be an AttributeOption model object instance"))
        if not value.pk:
            raise ValidationError(_("AttributeOption has not been saved yet"))
        if valid_values is None:
            valid_values = self.option_group.options.values_list(
                'option', flat=True)
        if value.option not in valid_values:
            raise ValidationError(
                _("%(enum)s is not a valid choice for %(attr)s") %
                {'enum': value, 'attr': self})

    def _validate_file(self, value):
        if value and not isinstance(value, File):
            raise ValidationError(_("Must be a file field"))
    _validate_image = _validate_file


class AbstractSduAttributeValue(models.Model):
    """
    The "through" model for the m2m relationship between :py:class:`Sdu <.AbstractSdu>` and
    :py:class:`SduAttribute <.AbstractSduAttribute>`  This specifies the value of the attribute for
    a particular sdu

    For example: ``number_of_pages = 295``
    """
    attribute = models.ForeignKey(
        'catalogue.SduAttribute',
        on_delete=models.CASCADE,
        verbose_name=_("Attribute"))
    sdu = models.ForeignKey(
        'catalogue.Sdu',
        on_delete=models.CASCADE,
        related_name='attribute_values',
        verbose_name=_("Sdu"))

    value_text = models.TextField(_('Text'), blank=True, null=True)
    value_integer = models.IntegerField(_('Integer'), blank=True, null=True, db_index=True)
    value_boolean = models.BooleanField(_('Boolean'), blank=True, null=True, db_index=True)
    value_float = models.FloatField(_('Float'), blank=True, null=True, db_index=True)
    value_richtext = models.TextField(_('Richtext'), blank=True, null=True)
    value_date = models.DateField(_('Date'), blank=True, null=True, db_index=True)
    value_datetime = models.DateTimeField(_('DateTime'), blank=True, null=True, db_index=True)
    value_multi_option = models.ManyToManyField(
        'catalogue.AttributeOption', blank=True,
        related_name='multi_valued_attribute_values',
        verbose_name=_("Value multi option"))
    value_option = models.ForeignKey(
        'catalogue.AttributeOption',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name=_("Value option"))
    value_file = models.FileField(
        upload_to=get_image_upload_path, max_length=255,
        blank=True, null=True)
    value_image = models.ImageField(
        upload_to=get_image_upload_path, max_length=255,
        blank=True, null=True)
    value_entity = GenericForeignKey(
        'entity_content_type', 'entity_object_id')

    entity_content_type = models.ForeignKey(
        ContentType,
        blank=True,
        editable=False,
        on_delete=models.CASCADE,
        null=True)
    entity_object_id = models.PositiveIntegerField(
        null=True, blank=True, editable=False)

    def _get_value(self):
        value = getattr(self, 'value_%s' % self.attribute.type)
        if hasattr(value, 'all'):
            value = value.all()
        return value

    def _set_value(self, new_value):
        attr_name = 'value_%s' % self.attribute.type

        if self.attribute.is_option and isinstance(new_value, str):
            # Need to look up instance of AttributeOption
            new_value = self.attribute.option_group.options.get(
                option=new_value)
        elif self.attribute.is_multi_option:
            getattr(self, attr_name).set(new_value)
            return

        setattr(self, attr_name, new_value)
        return

    value = property(_get_value, _set_value)

    class Meta:
        abstract = True
        app_label = 'catalogue'
        unique_together = ('attribute', 'sdu')
        verbose_name = _('Sdu attribute value')
        verbose_name_plural = _('Sdu attribute values')

    def __str__(self):
        return self.summary()

    def summary(self):
        """
        Gets a string representation of both the attribute and it's value,
        used e.g in sdu summaries.
        """
        return "%s: %s" % (self.attribute.name, self.value_as_text)

    @property
    def value_as_text(self):
        """
        Returns a string representation of the attribute's value. To customise
        e.g. image attribute values, declare a _image_as_text property and
        return something appropriate.
        """
        property_name = '_%s_as_text' % self.attribute.type
        return getattr(self, property_name, self.value)

    @property
    def _multi_option_as_text(self):
        return ', '.join(str(option) for option in self.value_multi_option.all())

    @property
    def _option_as_text(self):
        return str(self.value_option)

    @property
    def _richtext_as_text(self):
        return strip_tags(self.value)

    @property
    def _entity_as_text(self):
        """
        Returns the unicode representation of the related model. You likely
        want to customise this (and maybe _entity_as_html) if you use entities.
        """
        return str(self.value)

    @property
    def _boolean_as_text(self):
        if self.value:
            return pgettext("Sdu attribute value", "Yes")
        return pgettext("Sdu attribute value", "No")

    @property
    def value_as_html(self):
        """
        Returns a HTML representation of the attribute's value. To customise
        e.g. image attribute values, declare a ``_image_as_html`` property and
        return e.g. an ``<img>`` tag.  Defaults to the ``_as_text``
        representation.
        """
        property_name = '_%s_as_html' % self.attribute.type
        return getattr(self, property_name, self.value_as_text)

    @property
    def _richtext_as_html(self):
        return mark_safe(self.value)


class AbstractAttributeOptionGroup(models.Model):
    """
    Defines a group of options that collectively may be used as an
    attribute type

    For example, Language
    """
    name = models.CharField(_('Name'), max_length=128)

    def __str__(self):
        return self.name

    class Meta:
        abstract = True
        app_label = 'catalogue'
        verbose_name = _('Attribute option group')
        verbose_name_plural = _('Attribute option groups')

    @property
    def option_summary(self):
        options = [o.option for o in self.options.all()]
        return ", ".join(options)


class AbstractAttributeOption(models.Model):
    """
    Provides an option within an option group for an attribute type
    Examples: In a Language group, English, Greek, French
    """
    group = models.ForeignKey(
        'catalogue.AttributeOptionGroup',
        on_delete=models.CASCADE,
        related_name='options',
        verbose_name=_("Group"))
    option = models.CharField(_('Option'), max_length=255)

    def __str__(self):
        return self.option

    class Meta:
        abstract = True
        app_label = 'catalogue'
        unique_together = ('group', 'option')
        verbose_name = _('Attribute option')
        verbose_name_plural = _('Attribute options')


class AbstractOption(models.Model):
    """
    An option that can be selected for a particular item when the sdu
    is added to the basket.

    For example,  a list ID for an SMS message send, or a personalised message
    to print on a T-shirt.

    This is not the same as an 'attribute' as options do not have a fixed value
    for a particular item.  Instead, option need to be specified by a renter
    when they add the item to their basket.

    The `type` of the option determines the form input that will be used to
    collect the information from the renter, and the `required` attribute
    determines whether a value must be supplied in order to add the item to the basket.
    """

    # Option types
    TEXT = "text"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"

    SELECT = "select"
    RADIO = "radio"
    MULTI_SELECT = "multi_select"
    CHECKBOX = "checkbox"

    TYPE_CHOICES = (
        (TEXT, _("Text")),
        (INTEGER, _("Integer")),
        (BOOLEAN, _("True / False")),
        (FLOAT, _("Float")),
        (DATE, _("Date")),
        (SELECT, _("Select")),
        (RADIO, _("Radio")),
        (MULTI_SELECT, _("Multi select")),
        (CHECKBOX, _("Checkbox")),
    )

    empty_label = "------"
    empty_radio_label = _("Skip this option")

    name = models.CharField(_("Name"), max_length=128, db_index=True)
    code = AutoSlugField(_("Code"), max_length=128, unique=True, populate_from='name')
    type = models.CharField(_("Type"), max_length=255, default=TEXT, choices=TYPE_CHOICES)
    required = models.BooleanField(_("Is this option required?"), default=False)
    option_group = models.ForeignKey(
        "catalogue.AttributeOptionGroup",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="sdu_options",
        verbose_name=_("Option Group"),
        help_text=_('Select an option group if using type "Option" or "Multi Option"'),
    )
    help_text = models.CharField(
        verbose_name=_("Help text"), blank=True, null=True, max_length=255,
        help_text=_("Help text shown to the user on the add to basket form")
    )
    order = models.IntegerField(
        _("Ordering"),
        null=True,
        blank=True,
        help_text=_("Controls the ordering of sdu options on sdu detail pages"),
        db_index=True,
    )

    @property
    def is_option(self):
        return self.type in [self.SELECT, self.RADIO]

    @property
    def is_multi_option(self):
        return self.type in [self.MULTI_SELECT, self.CHECKBOX]

    @property
    def is_select(self):
        return self.type in [self.SELECT, self.MULTI_SELECT]

    @property
    def is_radio(self):
        return self.type in [self.RADIO]

    def add_empty_choice(self, choices):
        if self.is_select and not self.is_multi_option:
            choices = [("", self.empty_label)] + choices
        elif self.is_radio:
            choices = [(None, self.empty_radio_label)] + choices
        return choices

    def get_choices(self):
        if self.option_group:
            choices = [(opt.option, opt.option) for opt in self.option_group.options.all()]
        else:
            choices = []

        if not self.required:
            choices = self.add_empty_choice(choices)

        return choices

    def clean(self):
        if self.type in [self.RADIO, self.SELECT, self.MULTI_SELECT, self.CHECKBOX]:
            if self.option_group is None:
                raise ValidationError(
                    _("Option Group is required for type %s") % self.get_type_display()
                )
        elif self.option_group:
            raise ValidationError(
                _("Option Group can not be used with type %s") % self.get_type_display()
            )
        return super().clean()

    class Meta:
        abstract = True
        app_label = 'catalogue'
        ordering = ['type', 'name']
        verbose_name = _("Option")
        verbose_name_plural = _("Options")

    def __str__(self):
        return self.name


class MissingSduImage(object):

    """
    Mimics a Django file field by having a name property.

    :py:mod:`sorl-thumbnail` requires all it's images to be in MEDIA_ROOT. This class
    tries symlinking the default "missing image" image in STATIC_ROOT
    into MEDIA_ROOT for convenience, as that is necessary every time an Oscar
    project is setup. This avoids the less helpful NotFound IOError that would
    be raised when :py:mod:`sorl-thumbnail` tries to access it.
    """

    def __init__(self, name=None):
        self.name = name if name else settings.OSCAR_MISSING_IMAGE_URL
        media_file_path = os.path.join(settings.MEDIA_ROOT, self.name)
        # don't try to symlink if MEDIA_ROOT is not set (e.g. running tests)
        if settings.MEDIA_ROOT and not os.path.exists(media_file_path):
            self.symlink_missing_image(media_file_path)

    def symlink_missing_image(self, media_file_path):
        static_file_path = find('oscar/img/%s' % self.name)
        if static_file_path is not None:
            try:
                # Check that the target directory exists, and attempt to
                # create it if it doesn't.
                media_file_dir = os.path.dirname(media_file_path)
                if not os.path.exists(media_file_dir):
                    os.makedirs(media_file_dir)
                os.symlink(static_file_path, media_file_path)
            except OSError:
                raise ImproperlyConfigured((
                    "Please copy/symlink the "
                    "'missing image' image at %s into your MEDIA_ROOT at %s. "
                    "This exception was raised because Oscar was unable to "
                    "symlink it for you.") % (static_file_path, settings.MEDIA_ROOT))
            else:
                logging.info((
                    "Symlinked the 'missing image' image at %s into your "
                    "MEDIA_ROOT at %s") % (static_file_path, settings.MEDIA_ROOT))


class AbstractSduImage(models.Model):
    """
    An image of a sdu
    """
    sdu = models.ForeignKey(
        'catalogue.Sdu',
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_("Sdu"))
    original = models.ImageField(
        _("Original"), upload_to=get_image_upload_path, max_length=255)
    caption = models.CharField(_("Caption"), max_length=200, blank=True)

    #: Use display_order to determine which is the "primary" image
    display_order = models.PositiveIntegerField(
        _("Display inquiry"), default=0, db_index=True,
        help_text=_("An image with a display inquiry of zero will be the primary"
                    " image for a sdu"))
    date_created = models.DateTimeField(_("Date created"), auto_now_add=True)

    class Meta:
        abstract = True
        app_label = 'catalogue'
        # Any custom models should ensure that this ordering is unchanged, or
        # your query count will explode. See AbstractSdu.primary_image.
        ordering = ["display_order"]
        verbose_name = _('Sdu image')
        verbose_name_plural = _('Sdu images')

    def __str__(self):
        return "Image of '%s'" % self.sdu

    def is_primary(self):
        """
        Return bool if image display inquiry is 0
        """
        return self.display_order == 0

    def delete(self, *args, **kwargs):
        """
        Always keep the display_order as consecutive integers. This avoids
        issue #855.
        """
        super().delete(*args, **kwargs)
        for idx, image in enumerate(self.sdu.images.all()):
            image.display_order = idx
            image.save()
