var http = require('http');
var mqtt    = require('mqtt');
var client  = mqtt.connect('mqtt://hanjo.synology.me:1883');

var express = require('express'),                                                                                        
    http = require('http');                                                                                              
                                                                                                                         
var app = express();         

var taxis = [];
                                                                                                                         
app.engine('handlebars', require('express3-handlebars')({ defaultLayout: 'main' }));                                     
app.set('view engine', 'handlebars');                                                                                    
                                                                                                                         
app.use(require('morgan')('dev'));                                                                                       
                                                                                                                         
app.use(express.static(__dirname + '/public'));                                                                          

client.on('connect', function () {
  client.subscribe('presence');
});
 
client.on('message', function (topic, message) {
  // message is Buffer 
  console.log(message.toString());
  message = JSON.parse(message);
  var taxi = {
		id: message.driver,
		name: message.car,
		amenities: "",
		loc: { lat: message.gps.latitude, lng: message.gps.longitude },
  };
  var added = false;
  for (var i = 0; i < taxis.length; i++) {

  	if (taxis[i].id == message.driver) {

  		taxis[i] = taxi;
  		added = true;
  	}
  }
  if (!added) {

	  taxis.push(taxi);
    app.locals.taxis = taxis;
  }
  // app.render('home');
  console.log(taxis[0]);                                                                                                                     
});

app.get('/', function(req, res){                                                                                  
    res.render('home');                                                                                                  
});                                                                                                                      
                                                                                                                         
app.get('/error', function(req, res){                                                                                    
    throw new Error('Whoops!');                                                                                          
});                                                                                                                      
    
app.get('/api/easycab', function(req, res){                                                                    
    res.json(taxis);                                                                                                                  
});                                                                                                                      
                                                                                                                    
app.get('/partials/taxi-info/:id', function(req, res){  
  console.log(taxis);                                                                 
    res.render('partials/taxi-info', { taxi: taxis.byId[req.params.id], layout: null });                             
});                                                                                                                    
                                                                                                                         
app.use(function(req, res){                                                                                              
    res.render('404');                                                                                                   
});                                                                                                                      
                                                                                                                         
app.use(function(err, req, res, next){                                                                                   
    console.error('Server error: ' + err.stack);                                                                         
    res.render('500');                                                                                                   
});                                                                                                                      
                                                                                                                         
app.listen(8888, function(){                                                                                             
    console.log('listening on port 8888');                                                                               
});                                                                                                                      
        
