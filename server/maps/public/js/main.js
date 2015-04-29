
$(document).ready(function(){

	if ($('#map').length > 0) {

		$.get('/api/easycab', function(data){

			if (data[0] && data[0].loc) {
			
			if(!Array.isArray(data)) return console.error('/api/easycab did not return array as expected.');

			var mapOptions = {
	          center: data[0].loc,
	          zoom: 13
	        };

	        var map = new google.maps.Map($('#map').get(0), mapOptions);

			data.forEach(function(taxi){
				var marker = new google.maps.Marker({
					position: taxi.loc,
					map: map,
					title: taxi.name,
				});
				google.maps.event.addListener(marker, 'click', function(){
					$.get('/partials/taxi-info/' + taxi.id, function(data){
						$('#taxiInfo').html(data);
					});
				});
			});
			}
		});
	}
});