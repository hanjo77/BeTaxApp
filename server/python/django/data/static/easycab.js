var client = new Paho.MQTT.Client("46.101.17.239", 10001,
				"myclientid_" + parseInt(Math.random() * 100, 10));
				

client.onConnectionLost = function (responseObject) {
	console.log("connection lost");
	client.connect(options);
};

client.onMessageArrived = function (message) {
	// mqttitude mesaage recieved is in JSON format. See http://mqttitude.org/api.html	
	//console.log(message.payloadString);	
	var recievedmsg = message.payloadString;
	var myObj = jQuery.parseJSON(recievedmsg); //parse payload
	if (myObj.disconnected) {
		removeMarker(myObj.disconnected);
	}
	else {
		var myDate = new Date(myObj.time *1000); //convert epoch time to readible local datetime
		// console.log('ParsedJSON -- Time: ', myObj.time,' Lat: ', myObj.gps.latitude,' Lon: ',myObj.gps.longitude);
		addMarker(
			myObj.gps.latitude,
			myObj.gps.longitude
			,recievedmsg); //add marker based on lattitude and longittude, using timestamp for description for now
		// center = bounds.getCenter(); //center on marker, zooms in to far atm, needs to be fixed!
		// map.fitBounds(bounds);
	}
};

var options = {
	timeout: 3,
	onSuccess: function () {
		// alert("Connected");
		console.log("mqtt connected");
		// Connection succeeded; subscribe to our topic
		client.subscribe('presence', {qos: 0});
	},
	onFailure: function (message) {
		alert("Connection failed: " + message.errorMessage);
		console.log("connection failed");
	}
};

var center = null;
var map = null;
var currentPopup;
var bounds = new google.maps.LatLngBounds();
var activeMarker = null;
var markers = {};
var timeouts = {};
var database = {};

function removeMarker(key) {
	var marker = markers[key];
	if (marker) {
		/* marker.setMap(null);
		$(".car" + key).remove();
		markers[key] = null; */
		if (key == activeMarker) {
			activeMarker = null;
		}
		marker.setIcon("http://46.101.17.239/marker-png/marker.php?inactive=true&text=" + key);
	}
	$("h3.car" + key).removeClass("active");
}

function refreshAccordion() {
	$("#accordion").accordion("refresh");
	$("#accordion h3.ui-state-active").click(function(event) {
		var $target = $(event.target);
		var targetId = $target.attr("data-key");
		if (markers[targetId]) {

			new google.maps.event.trigger(markers[targetId], 'click');
		}
	});
}

function showAll() {
	for (var key in markers) {
		var $header = $("h3.car"+key);
		$(".car"+key).show();
		markers[key].setMap(map);
	}
}

function showActive() {
	for (var key in markers) {
		var $header = $("h3.car"+key);
		if ($header.hasClass("active")) {
			$(".car"+key).show();
			markers[key].setMap(map);
		}
		else {
			$(".car"+key).hide();
			markers[key].setMap(null);
		}
	}
}

function showInactive() {
	for (var key in markers) {
		var $header = $("h3.car"+key);
		if ($header.hasClass("active")) {
			$(".car"+key).hide();
			markers[key].setMap(null);

		}
		else {
			$(".car"+key).show();
			markers[key].setMap(map);
		}
	}
}

function addMarker(lat, lng, info) {
	//console.log(lat, lng, info);
	var data = jQuery.parseJSON(info);
	var pt = new google.maps.LatLng(lat, lng);
	// bounds.extend(pt);
	if (!markers[data.car]) {

		var icon = new google.maps.MarkerImage("http://46.101.17.239/marker-png/marker.php?text=" + data.car,
				   new google.maps.Size(120, 48), new google.maps.Point(0, 0),
				   new google.maps.Point(60, 48));

		if (!data.time) {
			icon = new google.maps.MarkerImage("http://46.101.17.239/marker-png/marker.php?inactive=true&text=" + data.car,
				   new google.maps.Size(120, 48), new google.maps.Point(0, 0),
				   new google.maps.Point(60, 48));

		}

		var marker = new google.maps.Marker({
			position: pt,
			icon: icon,
			map: map
		});

		if ($('.car' + data.car).length <= 0) {

			var tableData = '<table>'
					+ '<tbody>'
						+ '<tr class="time">'
							+ '<th>Time</th>'
							+ '<td data-key="time">' + formatDateTime(data.time) + '</td>'
						+ '<tr>'
						+ '<tr class="driver">'
							+ '<th>Driver</th>'
							+ '<td data-key="driver">' + getDriverNameFromToken(data.driver) + '</td>'
						+ '<tr>'
						+ '<tr class="position">'
							+ '<th>Position</th>'
							+ '<td>'
								+ '<span data-key="gps.latitude">' + data.gps.latitude.toFixed(7) + '</span>, '
								+ '<span data-key="gps.longitude">' + data.gps.longitude.toFixed(7) + '</span>'
							+ '</td>'
						+ '<tr>'
					+ '</tbody>'
				+ '<table>';

			$("#accordion").append('<h3 id="' + data.car + '" class="car' + data.car + '" data-key="' + data.car + '" data-position="' + data.gps.latitude.toFixed(7) + "," + data.gps.longitude.toFixed(7) + '">' + data.car + '</h3>'
				+ '<div class="car' + data.car + '">'
					+ tableData
				+ '</div>');
		}

		var elem = $('#accordion').find('h3, div').sort(sortByTagAndClass);			


		updateSize();

		/* var popup = new google.maps.InfoWindow({
			content: '<div class="carInfo">'
			+ tableData
			+ '</div>',
			maxWidth: 400
		});
		google.maps.event.addListener(popup, "closeclick", function() {
			// map.panTo(center);
			currentPopup = null;
		}); */
		google.maps.event.addListener(marker, "click", function() {
			var index = Math.floor(parseInt($(".car" + data.car).attr("id").replace("ui-id-", ""), 10) / 2);
		    $("#accordion").accordion({ active: index });
			map.setCenter(new google.maps.LatLng(
				parseFloat($(".car" + data.car + " *[data-key='gps.latitude']").html()),
				parseFloat($(".car" + data.car + " *[data-key='gps.longitude']").html())));
			map.setZoom(16);
			activeMarker = data.car;
			/* if (currentPopup != null) {
				currentPopup.close();
				currentPopup = null;
			}
			popup.open(map, marker);
			currentPopup = popup; */
		});
		markers[data.car] = marker;
	}
	else {

		markers[data.car].setPosition(new google.maps.LatLng(data.gps.latitude, data.gps.longitude));
		markers[data.car].setIcon("http://46.101.17.239/marker-png/marker.php?text=" + data.car);
	}

	if (data.time) {

		$(".car" + data.car + " *[data-key='time']").html(formatDateTime(data.time));
		$(".car" + data.car + " *[data-key='driver']").html(getDriverNameFromToken(data.driver));
		$(".car" + data.car + " *[data-key='gps.latitude']").html(data.gps.latitude.toFixed(7));
		$(".car" + data.car + " *[data-key='gps.longitude']").html(data.gps.longitude.toFixed(7));
		$('h3.car' + data.car).addClass("active");
	}

	$("*[data-key='driver']").each(function(index, object) {
		if ($.trim($(object).html()) == "") {
			$.ajax({
		        url: "/drivers",
		        success: function( data ) {
		            $(object).html(data);
		            $(".driver select").change(function(event) {
		            	var oldId = $(event.target).parent().attr("data-id");
		            	var id = $(event.target).val();
		            	var driverName = event.target.options[event.target.selectedIndex].innerHTML;
		            	if (id != "" && window.confirm("Wollen Sie wirklich den Fahrer auf " + driverName + " ändern?")) {	            		
			            	var taxi = $(event.target).parent().parent().parent().parent().parent().prev().attr("data-key");
			            	$.ajax({ url: "/driver_change/" + taxi + "/" + oldId + "/" + id });
			            	$(event.target).parent().attr("data-id", id);
			            	$(event.target).parent().html(driverName);
		            	}
		            });
		        }
		    });
		}
	});

	if (timeouts[data.car]) {
		window.clearTimeout(timeouts[data.car]);
	}
	timeouts[data.car] = window.setTimeout(function() {
		removeMarker(data.car);
	}, 15000);
	if (activeMarker) {
		new google.maps.event.trigger(markers[activeMarker], 'click');
	}
	updateSize();
	refreshAccordion();
};

function sortByTagAndClass(a, b) {
    return (a.className < b.className || a.tagName > b.tagName);
}

function initMap() {
	map = new google.maps.Map(document.getElementById("map"), {
		zoom: 10,
		mapTypeId: google.maps.MapTypeId.HYBRID,
		mapTypeControl: true,
		mapTypeControlOptions: {
			style: google.maps.MapTypeControlStyle.HORIZONTAL_BAR
		},
		navigationControl: true,
		navigationControlOptions: {
			style: google.maps.NavigationControlStyle.ZOOM_PAN
		}
	});
	map.setCenter(new google.maps.LatLng(47.000,7.400));
	$("body").append('<a href="#" class="btn" id="resetView">Reset</a>');
	$("#resetView").click(function(event) {
		map.setCenter(new google.maps.LatLng(47.000,7.400));
		map.setZoom(10);
		activeMarker = null;
		event.preventDefault();
	});
	// center = bounds.getCenter();
    // map.fitBounds(bounds);
	
	/* Connect to MQTT broker */
	client.connect(options);
};

function updateSize() {
	var mapWidth = $(window).width();
	var mapHeight = $(window).height();
	if(window.innerHeight < window.innerWidth) {
		mapWidth -= $("#menu").outerWidth();
	}
	else {
		mapHeight -= $("#menu").outerHeight();
	}
	$("#map").css({
		width: mapWidth,
		height: mapHeight
	});
}

function getDatabase() {
	$.ajax({
		url: "database.php"
	})
	.done(function( data ) {
		database = $.parseJSON(data);
	});
}

function getDriverNameFromToken(token) {
	if (database && database.drivers && database.drivers[token]) {
		return database.drivers[token].name;
	}
	return token;
}

function formatDateTime(timeString) {
	var date = new Date(timeString);
	return ('0' + date.getDate()).slice(-2) + '.'
		+ ('0' + (date.getMonth()+1)).slice(-2) + '.'
		+ date.getFullYear() + " - "
		+ ('0' + date.getHours()).slice(-2) + ':'
		+ ('0' + date.getMinutes()).slice(-2) + ':'
		+ ('0' + date.getSeconds()).slice(-2);
}

$(document).ready(function() {
	getDatabase();
	initMap();
	updateSize();
	$(window).resize(function() {
		updateSize();
	});
	$.ajax({
        url: "/menu",
        success: function( data ) {
            $('#accordion').html(data);
			$("#accordion").accordion();
			$("#accordion h3").each(function(index, object) {
				var $object = $(object);
				var latlng = $object.attr("data-position").split(",");
				var key = $object.attr("data-key");
				if (!markers[key]) {
					addMarker(latlng[0], latlng[1], '{ "car": "' + key + '", "gps": { "latitude": ' + latlng[0] + ', "longitude": ' + latlng[1] + ' } }');
				}
			});
			refreshAccordion();
			$(".displayFilter").change(function(event) {
				eval($(event.target).val() + "()");
			})
        }
    });
});