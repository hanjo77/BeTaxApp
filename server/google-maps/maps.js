var map, infoWindow;
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
    strokeColor: '#cc0000',
    strokeOpacity: 1.0,
    strokeWeight: 2
  });

  track.setMap(map);
}

function getBoundsFromPath() {

	if (path) {
		for (var i = 0; i < path.length; i++) {

			var latlng = path[i];
			updateBounds(latlng);
		}
	}
}

function updateBounds(latlng) {

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

function updateMarkers() {

	$.get("positions.json", function(data, status){

		addMarker(data);
    });
}

window.setInterval(updateMarkers, 1000);

function addMarker(position) {

	if (position.driver) {

		var driver = drivers[position.driver];
		var center = ll(position.gps.latitude, position.gps.longitude);
		updateBounds(center);
		var marker = markers[position.car];
		if (marker) {

			marker.setPosition(center);
			$("#car_value").html(position.car);
			$("#driver_value").html(driver);
			$("#lat_value").html(center.lat());
			$("#lng_value").html(center.lng());
		}
		else {

			marker = new google.maps.Marker({
			    position: center,
			    map: map,
			    title: position.car
			});

			google.maps.event.addListener(marker, 'click', function() {
				if (!infoWindow || !infoWindow.getMap()) {

					var date = new Date(position.time).toLocaleDateString("de-CH", {
						year: "numeric", month: "short",
					    day: "numeric", hour: "2-digit", minute: "2-digit"
					});
					infoWindow = new google.maps.InfoWindow();
					infoWindow.setContent("<div id=\"infoWindow\">"
											+ "<h2 id=\"car_value\">" + position.car + "</h2>"
											+ "<span id=\"time_value\">" + date + "</span>"
											+ "<table>"
												+ "<tr>"
													+ "<th>Fahrer</th>"
													+ "<td id=\"driver_value\">" + driver + "</td>"
												+ "</tr>"
												+ "<tr>"
													+ "<th>Breitengrad</th>"
													+ "<td id=\"lat_value\">" + marker.position.lat() + "</td>"
												+ "</tr>"
												+ "<tr>"
													+ "<th>Längengrad</th>"
													+ "<td id=\"lng_value\">" + marker.position.lng() + "</td>"
												+ "</tr>"
											+ "</table>"
										+ "</div>");
					infoWindow.close();
					infoWindow.open(map,marker);
				}
			});

			markers[position.car] = marker;
			map.fitBounds(new google.maps.LatLngBounds(
				new google.maps.LatLng(bounds.lowLat, bounds.lowLon), 
				new google.maps.LatLng(bounds.topLat, bounds.topLon)));
			marker.setMap(map);
		}
		if (path.length <= 0) {
			map.panTo(center);
		}
	}
}

google.maps.event.addDomListener(window, 'load', initialize);