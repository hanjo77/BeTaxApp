<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
	<title>easyCab Path Test</title>
    <style>
      html, body, #mapContainer {
        height: 100%;
        margin: 0px;
        padding: 0px
      }
    </style>
   	<script src="../jquery/jquery.min.js"></script>
   	<script src="https://maps.googleapis.com/maps/api/js?v=3.exp"></script>
	<script src="path.js"></script>
    <script type="text/javascript">

      var flightPlanCoordinates = [<?php

        require_once("class.db_util.php");
        $db_util = new DBUtil();
        $pos = $db_util->query("select * from `position` order by `time` desc");
        $started = false;
        for($i = 0; $i < sizeof($pos); $i++) {
          $row = $pos[$i];
          if ($row["latitude"]) {
            if ($started) {
              echo(",");
            }
            $started = true;
            echo("new google.maps.LatLng(".$row["latitude"].",".$row["longitude"].")");
          }
        }

        ?>];

    </script>
</head>
<body>
<div id="mapContainer"></div>
</body>
</html>