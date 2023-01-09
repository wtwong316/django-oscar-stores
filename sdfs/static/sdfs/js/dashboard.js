var sdfs = sdfs || {};

sdfs.dashboard = {
    defaultLng: -37.82850537866209,
    defaultLat: 144.9661415816081,

    getLatLngFromGeoJSON: function (data) {
        var point = null;
        try {
            point = jQuery.parseJSON(data);
        } catch (e) {}

        if (!point || point.type.toLowerCase() !== "point") {
            return new google.maps.LatLng(
                sdfs.dashboard.defaultLng,
                sdfs.dashboard.defaultLat
                );
        }

        // the GeoJSON format provides latitude and longitude
        // in reverse order in the 'coordinates' list:
        // [x, y] => [longitude, latitude]
        return new google.maps.LatLng(
            point.coordinates[1],
            point.coordinates[0]
            );
    },

    getGeoJsonFromLatLng: function (data) {
        return {
            'type': 'Point',
            // the GeoJSON format provides latitude and longitude
            // in reverse order in the 'coordinates' list:
            // [x, y] => [longitude, latitude]
            'coordinates': [data.lng(), data.lat()]
        };
    },

    init: function () {
        var locationJSON = jQuery('#id_location').val(),
        latLng;

        if (locationJSON) {
            latLng = sdfs.dashboard.getLatLngFromGeoJSON(locationJSON);
        } else {
            latLng = null;
        }

        var input = jQuery('#search-text-field'),
        autocomplete = new google.maps.places.Autocomplete(input[0]),
        zoom = 17,
        marker = null;

        sdfs.dashboard.map = new google.maps.Map(document.getElementById('sdf-map'), {
            zoom: zoom,
            center: latLng,
            mapTypeId: google.maps.MapTypeId.ROADMAP
        });

        marker = new google.maps.Marker({
            position: latLng,
            map: sdfs.dashboard.map,
            draggable: true,
            visible: true,
            icon: 'http://www.google.com/mapfiles/arrow.png'
        });

        sdfs.dashboard.geocoder = new google.maps.Geocoder();
        sdfs.dashboard.autocomplete_serv = new google.maps.places.AutocompleteService();

        google.maps.event.addListener(marker, 'drag', function () {
            sdfs.dashboard.updateMarkerPosition(marker.getPosition());
        });

        google.maps.event.addListener(marker, 'dragend', function () {
            sdfs.dashboard.geocodePosition(marker.getPosition());
        });

        var update_timeout = null;
        google.maps.event.addListener(sdfs.dashboard.map, 'click', function (event) {
            update_timeout = setTimeout(function () {
                marker.setPosition(event.latLng);
                sdfs.dashboard.updateMarkerPosition(event.latLng);
            }, 200);
        });

        google.maps.event.addListener(sdfs.dashboard.map, 'dblclick', function (event) {
            if (update_timeout !== null) {
                clearTimeout(update_timeout);
            }
        });

        google.maps.event.addListener(autocomplete, 'place_changed', function () {
            var place = autocomplete.getPlace();
            if(!place.geometry) {
                return;
            }
            sdfs.dashboard.updateMarkerPlace(marker, place);
        });

        input.keypress(function(e) {
            if(e.which == 13) { // 13 is for Enter key
                e.preventDefault();
                sdfs.dashboard.updateToBestMatch(input, marker);
            }
        });

        //sdfs.dashboard.openingHoursForm();

        $('.nav-list a').on('shown', function (e) {
            google.maps.event.trigger(sdfs.dashboard.map, 'resize');
        })
    },

    updateToBestMatch: function(input, marker) {
        var query = input.val();
        if(!query) {
            return;
        }
        sdfs.dashboard.autocomplete_serv.getQueryPredictions(
            {'input': query},
            function(results, status) {
                if(status === google.maps.places.PlacesServiceStatus.OK) {
                    var address = results[0].description;
                    input.trigger('blur');
                    input.val(address);
                    sdfs.dashboard.updateToAddress(address, marker);
                    input.trigger('change');
                }
            }
            );
    },

    updateMarkerPlace: function(marker, place) {
        if (place.geometry.viewport) {
            sdfs.dashboard.map.fitBounds(place.geometry.viewport);
        } else {
            sdfs.dashboard.map.setCenter(place.geometry.location);
            sdfs.dashboard.map.setZoom(17);  // Why 17? Because it looks good.
        }

        marker.setPosition(place.geometry.location);
        sdfs.dashboard.updateMarkerPosition(place.geometry.location);
    },

    updateMarkerPosition: function (latLng) {
        var new_location = sdfs.dashboard.getGeoJsonFromLatLng(latLng);
        jQuery('#id_location').val(JSON.stringify(new_location));
    },

    geocodePosition: function (pos) {
        sdfs.dashboard.geocoder.geocode({
            latLng: pos
        }, function (responses) {
            if (!responses || responses.length < 0) {
                alert(gettext("did not receive valid geo position"));
            }
        });
    },

    updateToAddress: function(address, marker) {
        sdfs.dashboard.geocoder.geocode(
            {'address': address},
            function(results, status){
                if(status == google.maps.GeocoderStatus.OK) {
                    var latLang = results[0].geometry.location;
                    sdfs.dashboard.updateMarkerPlace(marker, results[0]);
                }
            }
            );
    },

    //openingHoursForm: function(){
    //    function isOpenCallback() {
    //        var isopen = $(this).prop('checked');
    //        var inputs = $(this).closest('.weekday-block').find('input[type=text],button');
    //        inputs.prop('disabled', !isopen);
    //    }
    //    $('#opening_hours_form input[name$=open]').each(isOpenCallback).click(isOpenCallback);

    //    $('#opening_hours_form button.add-more').click(function(e){
    //        e.preventDefault();
    //        $(this).closest('.weekday-block').find('.hour-input.d-none').first().removeClass('d-none');
    //    });
    //}
};
