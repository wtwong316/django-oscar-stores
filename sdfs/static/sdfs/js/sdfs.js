var sdfs = (function(s, gmaps, o) {
    s.maps = {
        'overview': {
            init: function(sdfs, marker) {
                var map = s.maps.overview.createOverviewMap(sdfs, marker);
                s.maps.overview.initAutocomplete();
                s.maps.overview.initGeoLocation();

                // Submit form when a user selects a sdf type
                $('[data-behaviours~=filter-group]').on('change', function () {
                    $('#sdf-search').submit();
                });
            },

            initAutocomplete: function() {
                var input = $('#id_query'),
                    autocomplete = new gmaps.places.Autocomplete(input[0]);

                // 'placed_changed' event fires when a user selects a place from the
                // autocomplete predictions.  We update the hidden location input with
                // a geo-json version of the LatLng and submit the form after a short delay.
                gmaps.event.addListener(autocomplete, 'place_changed', function() {
                    var place = autocomplete.getPlace();
                    if (place.geometry) {
                        s.maps.overview.updateLocation(place.geometry.location);
                        $('#sdf-search').submit();
                    }
                });
            },

            initGeoLocation: function() {
                $(document).on('click', '[data-behaviours~=geo-location]', function (ev) {
                    if (navigator.geolocation) {
                        // Define callbacks for error/success
                        var error = function(msg) {
                            if (console) {
                                console.log("Geoposition error: ", msg);
                            }
                            o.messages.error(gettext("Your position could not be determined.  Please check your browser settings."));
                        };
                        var success = function (position) {
                            latLng = new gmaps.LatLng(
                                position.coords.latitude,
                                position.coords.longitude
                            );
                            s.maps.overview.updateLocation(latLng);
                            // Clear other form fields before submitting form
                            $('#id_query, #id_group').val('');
                            $('#sdf-search').submit();
                        };
                        navigator.geolocation.getCurrentPosition(success, error);
                    } else {
                        o.messages.error(gettext('Your location could not be determined'));
                    }
                });
            },

            // Create the initial map
            createOverviewMap: function(sdfs, markerLatLng) {
                var map = new gmaps.Map($('#sdf-map')[0], {
                    // We use a default center as adding the sdfs will
                    // centre the map.
                    center: new gmaps.LatLng(0, 0),
                    mapTypeId: gmaps.MapTypeId.ROADMAP,
                    disableDefaultUI: false,
                    zoomControl: true,
                    scrollwheel: true,
                    zoom: 17
                });
                var bounds = new gmaps.LatLngBounds();

                if (markerLatLng) {
                    var marker = new gmaps.Marker({
                        position: markerLatLng,
                        map: map,
                        visible: true,
                        icon: 'http://www.google.com/mapfiles/arrow.png'
                    });
                    bounds.extend(markerLatLng);
                    map.fitBounds(bounds);
                }
                s.maps.overview.addSdfMarkers(map, bounds, sdfs);
                return map;
            },

            getSdfInfoHTML: function(sdf) {
                var infoHTML;

                if (sdf.url) {
                    infoHTML = '<h5><a href="' + sdf.url + '">' + sdf.name + '</a></h5>';
                } else {
                    infoHTML = '<h5>' + sdf.name + '</h5>';
                }
                if (sdf.phone) {
                    infoHTML += '<p>' + sdf.phone + '</p>';
                }
                infoHTML += '<p>' + sdf.address1;
                if (sdf.address2) infoHTML += '<br/>' + sdf.address2;
                if (sdf.address3) infoHTML += '<br/>' + sdf.address3;
                infoHTML += '<br/>' + sdf.postcode + ' ' + sdf.address4 + '</p>';
                return infoHTML;
            },

            addSdfMarkers: function(map, bounds, sdfs) {
                var activeInfoWindow = null, that = this;
                $.each(sdfs, function(index, sdf) {
                    var sdfMarker = new gmaps.Marker({
                        position: sdf.location,
                        map: map,
                        title: sdf.name,
                        visible: true
                    });
                    bounds.extend(sdf.location);
                    map.fitBounds(bounds);

                    var infowindow = new gmaps.InfoWindow({
                        content: that.getSdfInfoHTML(sdf)
                    });

                    // Open the infowindow on marker click
                    gmaps.event.addListener(sdfMarker, "click", function() {
                        if (activeInfoWindow) {
                            activeInfoWindow.close();
                        }
                        infowindow.open(map, sdfMarker);
                        activeInfoWindow = infowindow;
                    });
                });
            },

            // Persist a LatLng in the hidden input
            updateLocation: function(latLng) {
                $('#id_latitude').val(latLng.lat());
                $('#id_longitude').val(latLng.lng());
            }
        },

        initSdf: function() {
            $('.sdf-map').each(function(elem) {
                s.maps.createIndividualMap(this, $('.sdf-details address'), 16);
                $(this).css({width: $(this).parents('.row').width()});
            });
        },

        createIndividualMap: function (mapElem, addressElem, zoomLevel) {
            lat = addressElem.data('lat');
            lng = addressElem.data('lng');

            if (lat & lng) {
                sdfLatLng = new gmaps.LatLng(lat, lng);

                map = new gmaps.Map(mapElem, {
                    mapTypeId: gmaps.MapTypeId.ROADMAP,
                    disableDefaultUI: true,
                    scrollwheel: false,
                    zoom: zoomLevel
                });
                map.setCenter(sdfLatLng);

                marker = new gmaps.Marker({
                    position: sdfLatLng,
                    map: map
                });

                if (!zoomLevel) {
                    bounds = new gmaps.LatLngBounds();
                    bounds.extend(sdfLatLng);
                    map.fitBounds(bounds);
                    map.setCenter(bounds.getCenter());
                }
            }
        }
    };
    return s;

})(sdfs || {}, google.maps, oscar);
