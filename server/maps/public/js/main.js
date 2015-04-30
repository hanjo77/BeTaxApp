
$(document).ready(function(){

	if ($('#map').length > 0) {

		var mapOptions = {
          center: { 
          	lat: 46.971378,
          	lng: 7.440972
          },
          zoom: 12
        };

        var map = new google.maps.Map($('#map').get(0), mapOptions);

		$.get('/api/easycab#'+(new Date().getTime()), function(data){

			if (data[0] && data[0].loc) {
			
			if(!Array.isArray(data)) return console.error('/api/easycab did not return array as expected.');

				map.setCenter(data[0].loc);
				map.setZoom(13);
	        };

			data.forEach(function(taxi){
				var marker = new google.maps.Marker({
					position: taxi.loc,
					map: map,
					title: taxi.name,
				});
				google.maps.event.addListener(marker, 'click', function(){
					$.get('/partials/taxi-info#' + (new Date().getTime()), function(data) {
						$('#taxiInfo').html(data);
						$('#taxiInfo').fadeIn('slow');
					});
				});
			});
		});
	}
});