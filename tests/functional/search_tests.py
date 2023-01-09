from django.urls import reverse
from oscar.test.testcases import WebTestCase

from tests.factories import SdfFactory, SdfGroupFactory


class TestTheListOfSdfs(WebTestCase):
    anonymous = True

    def setUp(self):
        super().setUp()
        self.main_location = 'POINT(144.917908 -37.815751)'
        self.other_location = 'POINT(144.998401 -37.772895)'

        self.main_sdf = SdfFactory(
            name="Main sdf in Southbank",
            is_pickup_sdf=True,
            location=self.main_location,
        )
        self.other_sdf = SdfFactory(
            name="Other sdf in Northcote",
            is_pickup_sdf=True,
            location=self.other_location,
        )

    def test_displays_all_sdfs_unfiltered(self):
        page = self.get(reverse('sdfs:index'))
        self.assertContains(page, self.main_sdf.name)
        self.assertContains(page, self.other_sdf.name)

    def test_can_be_filtered_by_location(self):
        page = self.get(reverse('sdfs:index'))
        search_form = page.forms['sdf-search']
        search_form['latitude'] = '-37.7736132'
        search_form['longitude'] = '-144.9997396'
        page = search_form.submit()

        self.assertContains(page, self.main_sdf.name)
        self.assertContains(page, self.other_sdf.name)

        sdfs = page.context[0].get('object_list')
        self.assertSequenceEqual(sdfs, [self.other_sdf, self.main_sdf])

    def test_can_be_filtered_by_sdf_group(self):
        north_group = SdfGroupFactory(name="North")
        south_group = SdfGroupFactory(name="South")

        self.main_sdf.group = south_group
        self.main_sdf.save()
        self.other_sdf.group = north_group
        self.other_sdf.save()

        page = self.get(reverse('sdfs:index'))
        search_form = page.forms['sdf-search']
        search_form['group'] = south_group.id
        page = search_form.submit()

        self.assertContains(page, self.main_sdf.name)

        sdfs = page.context[0].get('object_list')
        self.assertSequenceEqual(sdfs, [self.main_sdf])
