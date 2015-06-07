<?php
/**
 * Configuration settings for EasyCab
 * PHP Version 5.0.0
 * @author Hansjürg Jaggi (hanjo) <hanjo77@gmail.com>
 */

class EasyCabConfig {

    public $self = array();

    // Database server connection settings

    public static $db = array(

        "server" => "127.0.0.1",
        "name" => "easycab",
        "user" => "easycab",
        "password" => "raspberry"
    );

    // Email server connection settings

    public static $mail = array(

        "server" => "ssl://smtp.gmail.com",
        "user" => "senkushagame@gmail.com",
        "password" => "53nku-5h4",
        "address" => "senkushagame@gmail.com"
    );

}
