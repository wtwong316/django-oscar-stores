from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _

from oscar.core.compat import AUTH_USER_MODEL


class AbstractSduRecord(models.Model):
    """
    A record of a how popular a sdu is.

    This used be auto-merchandising to display the most popular
    sdus.
    """

    sdu = models.OneToOneField(
        'catalogue.Sdu', verbose_name=_("Sdu"),
        related_name='stats', on_delete=models.CASCADE)

    # Data used for generating a score
    num_views = models.PositiveIntegerField(_('Views'), default=0)
    num_basket_additions = models.PositiveIntegerField(
        _('Basket Additions'), default=0)
    num_purchases = models.PositiveIntegerField(
        _('Purchases'), default=0, db_index=True)

    # Sdu score - used within search
    score = models.FloatField(_('Score'), default=0.00)

    class Meta:
        abstract = True
        app_label = 'analytics'
        ordering = ['-num_purchases']
        verbose_name = _('Sdu record')
        verbose_name_plural = _('Sdu records')

    def __str__(self):
        return _("Record for '%s'") % self.sdu


class AbstractUserRecord(models.Model):
    """
    A record of a user's activity.
    """

    user = models.OneToOneField(AUTH_USER_MODEL, verbose_name=_("User"),
                                on_delete=models.CASCADE)

    # Browsing stats
    num_sdu_views = models.PositiveIntegerField(
        _('Sdu Views'), default=0)
    num_basket_additions = models.PositiveIntegerField(
        _('Basket Additions'), default=0)

    # Order stats
    num_orders = models.PositiveIntegerField(
        _('Orders'), default=0, db_index=True)
    num_order_lines = models.PositiveIntegerField(
        _('Order Lines'), default=0, db_index=True)
    num_order_items = models.PositiveIntegerField(
        _('Order Items'), default=0, db_index=True)
    total_spent = models.DecimalField(_('Total Spent'), decimal_places=2,
                                      max_digits=12, default=Decimal('0.00'))
    date_last_order = models.DateTimeField(
        _('Last Order Date'), blank=True, null=True)

    class Meta:
        abstract = True
        app_label = 'analytics'
        verbose_name = _('User record')
        verbose_name_plural = _('User records')


class AbstractUserSduView(models.Model):

    user = models.ForeignKey(
        AUTH_USER_MODEL, verbose_name=_("User"),
        on_delete=models.CASCADE)
    sdu = models.ForeignKey(
        'catalogue.Sdu',
        on_delete=models.CASCADE,
        verbose_name=_("Sdu"))
    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)

    class Meta:
        abstract = True
        app_label = 'analytics'
        ordering = ['-pk']
        verbose_name = _('User sdu view')
        verbose_name_plural = _('User sdu views')

    def __str__(self):
        return _("%(user)s viewed '%(sdu)s'") % {
            'user': self.user, 'sdu': self.sdu}


class AbstractUserSearch(models.Model):

    user = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("User"))
    query = models.CharField(_("Search term"), max_length=255, db_index=True)
    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)

    class Meta:
        abstract = True
        app_label = 'analytics'
        ordering = ['-pk']
        verbose_name = _("User search query")
        verbose_name_plural = _("User search queries")

    def __str__(self):
        return _("%(user)s searched for '%(query)s'") % {
            'user': self.user,
            'query': self.query}
