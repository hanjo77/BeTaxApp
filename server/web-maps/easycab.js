var client = new Paho.MQTT.Client("46.101.17.239", 10001,
				"myclientid_" + parseInt(Math.random() * 100, 10));
				

client.onConnectionLost = function (responseObject) {
	alert("connection lost: " + responseObject.errorMessage);
	console.log("connection lost");
};

client.onMessageArrived = function (message) {
	// mqttitude mesaage recieved is in JSON format. See http://mqttitude.org/api.html	
	//console.log(message.payloadString);	
	var recievedmsg = message.payloadString;
	var myObj = jQuery.parseJSON(recievedmsg); //parse payload
	var myDate = new Date(myObj.time *1000); //convert epoch time to readible local datetime
	// console.log('ParsedJSON -- Time: ', myObj.time,' Lat: ', myObj.gps.latitude,' Lon: ',myObj.gps.longitude);
	addMarker(
		myObj.gps.latitude,
		myObj.gps.longitude
		,recievedmsg); //add marker based on lattitude and longittude, using timestamp for description for now
	// center = bounds.getCenter(); //center on marker, zooms in to far atm, needs to be fixed!
	// map.fitBounds(bounds); 
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
var markers = {};
function addMarker(lat, lng, info) {
	//console.log(lat, lng, info);
	var data = jQuery.parseJSON(info);
	var pt = new google.maps.LatLng(lat, lng);
	// bounds.extend(pt);
	if (!markers[data.car]) {

		var icon = new google.maps.MarkerImage("http://46.101.17.239/marker-png/marker.php?text=" + data.car,
				   new google.maps.Size(160, 58), new google.maps.Point(0, 0),
				   new google.maps.Point(80, 58));
		var marker = new google.maps.Marker({
			position: pt,
			icon: icon,
			map: map
		});

		var tableData = '<table class="car' + data.car + '">'
				+ '<tr class="time">'
					+ '<th>Time</th>'
					+ '<td data-key="time">' + data.time + '</td>'
				+ '<tr>'
				+ '<tr class="driver">'
					+ '<th>Driver</th>'
					+ '<td data-key="driver">' + data.driver + '</td>'
				+ '<tr>'
				+ '<tr class="position">'
					+ '<th>Position</th>'
					+ '<td>'
						+ '<span data-key="gps.latitude">' + data.gps.latitude + '</span>, '
						+ '<span data-key="gps.longitude">' + data.gps.longitude + '</span>'
					+ '</td>'
				+ '<tr>'
			+ '<table>';

		$("#menu ul").append("<li>"
			+ '<h2>' + data.car + '</h2>'
			+ tableData
			+ '</li>');

		var popup = new google.maps.InfoWindow({
			content: '<div class="carInfo">'
			+ tableData
			+ '</div>',
			maxWidth: 400
		});
		google.maps.event.addListener(marker, "click", function() {
			if (currentPopup != null) {
				currentPopup.close();
				currentPopup = null;
			}
			popup.open(map, marker);
			currentPopup = popup;
		});
		google.maps.event.addListener(popup, "closeclick", function() {
			// map.panTo(center);
			currentPopup = null;
		});
		markers[data.car] = marker;
	}
	else {

		markers[data.car].setPosition(new google.maps.LatLng(data.gps.latitude, data.gps.longitude));
		$(".car" + data.car + " *[data-key='time']").html(data.time);
		$(".car" + data.car + " *[data-key='driver']").html(data.driver);
		$(".car" + data.car + " *[data-key='gps.latitude']").html(data.gps.latitude);
		$(".car" + data.car + " *[data-key='gps.longitude']").html(data.gps.longitude);
	}
};

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
	// center = bounds.getCenter();
    // map.fitBounds(bounds);
	
	/* Connect to MQTT broker */
	client.connect(options);
};

function updateSize() {
	$("#map").css({
		width: $(window).width()-$("#menu").width(),
		height: $(window).height()
	});
}

$(document).ready(function() {
	updateSize();
	initMap();
	$(window).resize(function() {
		updateSize();
	});
});