from django.contrib import admin

from oscar.core.loading import get_model

SduReview = get_model('reviews', 'SduReview')
Vote = get_model('reviews', 'Vote')


class SduReviewAdmin(admin.ModelAdmin):
    list_display = ('sdu', 'title', 'score', 'status', 'total_votes',
                    'delta_votes', 'date_created')
    readonly_fields = ('total_votes', 'delta_votes')


class VoteAdmin(admin.ModelAdmin):
    list_display = ('review', 'user', 'delta', 'date_created')


admin.site.register(SduReview, SduReviewAdmin)
admin.site.register(Vote, VoteAdmin)
