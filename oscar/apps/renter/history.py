import json

from django.conf import settings

from oscar.core.loading import get_model

Sdu = get_model('catalogue', 'Sdu')


class RenterHistoryManager:
    cookie_name = settings.OSCAR_RECENTLY_VIEWED_COOKIE_NAME
    cookie_kwargs = {
        'max_age': settings.OSCAR_RECENTLY_VIEWED_COOKIE_LIFETIME,
        'secure': settings.OSCAR_RECENTLY_VIEWED_COOKIE_SECURE,
        'httponly': True,
    }
    max_sdus = settings.OSCAR_RECENTLY_VIEWED_PRODUCTS

    @classmethod
    def get(cls, request):
        """
        Return a list of recently viewed sdus
        """
        ids = cls.extract(request)

        # Reordering as the ID order gets messed up in the query
        sdu_dict = Sdu.objects.browsable().in_bulk(ids)
        ids.reverse()
        return [sdu_dict[sdu_id] for sdu_id in ids if sdu_id in sdu_dict]

    @classmethod
    def extract(cls, request, response=None):
        """
        Extract the IDs of sdus in the history cookie
        """
        ids = []
        if cls.cookie_name in request.COOKIES:
            try:
                ids = json.loads(request.COOKIES[cls.cookie_name])
            except ValueError:
                # This can occur if something messes up the cookie
                if response:
                    response.delete_cookie(cls.cookie_name)
            else:
                # Badly written web crawlers send garbage in double quotes
                if not isinstance(ids, list):
                    ids = []
        return ids

    @classmethod
    def add(cls, ids, new_id):
        """
        Add a new sdu ID to the list of sdu IDs
        """
        if new_id in ids:
            ids.remove(new_id)
        ids.append(new_id)
        if len(ids) > cls.max_sdus:
            ids = ids[len(ids) - cls.max_sdus:]
        return ids

    @classmethod
    def update(cls, sdu, request, response):
        """
        Updates the cookies that store the recently viewed sdus
        removing possible duplicates.
        """
        ids = cls.extract(request, response)
        updated_ids = cls.add(ids, sdu.id)
        response.set_cookie(
            cls.cookie_name,
            json.dumps(updated_ids),
            **cls.cookie_kwargs)
