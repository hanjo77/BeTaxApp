<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
	<title>easyCab Test</title>
    <link rel="shortcut icon" href="favicon.ico" type="image/x-icon; charset=binary" />
    <link rel="icon" href="favicon.ico" type="image/x-icon; charset=binary" />
    <link rel="stylesheet" href="style.css" type="text/css" />
   	<script src="../jquery/jquery.min.js"></script>
   	<script src="https://maps.googleapis.com/maps/api/js?v=3.exp"></script>
	  <script src="maps.js"></script>
    <script type="text/javascript">

      var path = [<?php

        require_once("class.db_util.php");
        $db_util = new DBUtil();
        $cond_list = array();

        if (isset($_GET["start_time"])) {
          array_push($cond_list, "`time` >= '".$_GET["start_time"]."'");
        }
        if (isset($_GET["end_time"])) {
          array_push($cond_list, "`time` <= '".$_GET["end_time"]."'");
        }

        if (sizeof($cond_list) > 0) {
          $conditions = " where ".implode(" and ", $cond_list);
          $pos = $db_util->query("select * from `position`".$conditions." order by `time` asc");
          $started = false;
          for($i = 0; $i < sizeof($pos); $i++) {
            $row = $pos[$i];
            if ($row["latitude"]) {
              if ($started) {
                echo(",");
              }
              $started = true;
              echo("ll(".$row["latitude"].",".$row["longitude"].")");
            }
          }
        }


      ?>];
      var drivers = {<?php

        $drivers = $db_util->query("select * from `driver`");
        $started = false;
        for($i = 0; $i < sizeof($drivers); $i++) {
          $driver = $drivers[$i];
          if ($started) {
            echo(",");
          }
          $started = true;
          echo("\"".$driver["token"]."\":\"".$driver["firstname"]." ".$driver["lastname"]."\"");
        }

      ?>};

    </script>
</head>
<body>
<div id="mapContainer"></div>
</body>
</html>