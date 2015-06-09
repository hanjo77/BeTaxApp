var map;
var markers = {};
var bounds = null;

function initialize() {

  var mapOptions = {
    zoom: 3,
    center: new google.maps.LatLng(0, 0),
    mapTypeId: google.maps.MapTypeId.SATELLITE
  };
  map = new google.maps.Map(document.getElementById('mapContainer'), mapOptions);
  if (path) {

  	addPath();
  }
}

function ll(lat, lng) {

	return new google.maps.LatLng(lat, lng);
}

function addPath() {

  getBoundsFromPath();
  var track = new google.maps.Polyline({
    path: path,
    geodesic: true,
    strokeColor: '#FF0000',
    strokeOpacity: 1.0,
    strokeWeight: 2
  });

  track.setMap(map);
}

function getBoundsFromPath() {

	if (path) {
		for (var i = 0; i < path.length; i++) {

			var latlng = path[i];
			if (!bounds) {

				bounds = {

					"lowLat": latlng.lat(),
					"lowLon": latlng.lng(),
					"topLat": latlng.lat(),
					"topLon": latlng.lng()
				}
			}
			if (latlng.lat() < bounds.lowLat) {

				bounds.lowLat = latlng.lat();
			}
			if (latlng.lat() > bounds.topLat) {

				bounds.topLat = latlng.lat();
			}
			if (latlng.lng() < bounds.lowLon) {

				bounds.lowLon = latlng.lng();
			}
			if (latlng.lng() > bounds.topLon) {

				bounds.topLon = latlng.lng();
			}
		}
	}
}

function updateMarkers() {

	$.get("positions.json", function(data, status){

		addMarker(data);
    });
}

window.setInterval(updateMarkers, 1000);

function addMarker(position) {

	var center = new google.maps.LatLng(position.gps.latitude, position.gps.longitude);
	if (!bounds) {

		bounds = {

			"lowLat": position.gps.latitude,
			"lowLon": position.gps.longitude,
			"topLat": position.gps.latitude,
			"topLon": position.gps.longitude
		}
	}
	else {

		if (position.gps.latitude < bounds.lowLat) {

			bounds.lowLat = position.gps.latitude;
		}
		if (position.gps.latitude > bounds.topLat) {

			bounds.topLat = position.gps.latitude;
		}
		if (position.gps.longitude < bounds.lowLon) {

			bounds.lowLon = position.gps.longitude;
		}
		if (position.gps.longitude > bounds.topLon) {

			bounds.topLon = position.gps.longitude;
		}
	}
	var marker = markers[position.car];
	if (marker) {

		marker.setPosition(center);
	}
	else {

		marker = new google.maps.Marker({
		    position: center,
		    map: map,
		    title: position.car
		});
		markers[position.car] = marker;
		// map.setCenter(center);
		// map.setZoom(10);
		map.fitBounds(new google.maps.LatLngBounds(
			new google.maps.LatLng(bounds.lowLat, bounds.lowLon), 
			new google.maps.LatLng(bounds.topLat, bounds.topLon)));
		marker.setMap(map);
	}
}

google.maps.event.addDomListener(window, 'load', initialize);