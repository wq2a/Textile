<?php


/* This script was written with help from Mark Sanborn at http://www.marksanborn.net  
   
    The ICCC is staffed as follows:
    Monday through Friday from 8:00AM to 8:30PM Eastern Time
    Saturday from 8:00AM to 6:00PM Eastern Time
    Sunday and Postal Holidays - Closed except for the following Holidays: 
        Martin Luther King; President's Day; Columbus Day; & Veteran's Day with hours from 9:00AM to 6:00PM Eastern Time

            E-mail:  uspstechnicalsupport@mailps.custhelp.com
            Telephone:        1-800-344-7779
*/


function USPSParcelRate($weight,$dest_zip, $ship) {
    // ========== CHANGE THESE VALUES TO MATCH YOUR OWN ===========

    $userName = '050TEXTI6311'; // Your USPS Username
    $orig_zip = '37167'; // Zipcode you are shipping FROM
    
    // =============== DON'T CHANGE BELOW THIS LINE ===============

    $url = "http://Production.ShippingAPIs.com/ShippingAPI.dll";
    $ch = curl_init();

    // set the target url
    curl_setopt($ch, CURLOPT_URL,$url);
    curl_setopt($ch, CURLOPT_HEADER, 1);
    curl_setopt($ch,CURLOPT_RETURNTRANSFER,1);

    // parameters to post
    curl_setopt($ch, CURLOPT_POST, 1);
    $data = "API=RateV3&XML=".
        "<RateV3Request USERID=\"$userName\">".
            "<Package ID=\"1ST\">".
                "<Service>$ship</Service>".
                "<ZipOrigination>$orig_zip</ZipOrigination>".
                "<ZipDestination>$dest_zip</ZipDestination>".
                "<Pounds>$weight</Pounds>".
                "<Ounces>0</Ounces>".
                "<Size>REGULAR</Size>".
                "<Length>12</Length>".
                "<Height>6</Height>".
                "<Girth>36</Girth>".
                "<Machinable>TRUE</Machinable>".
            "</Package>".
        "</RateV3Request>";

    // send the POST values to USPS
    curl_setopt($ch, CURLOPT_POSTFIELDS,$data);

    $result=curl_exec ($ch);
    $data = strstr($result, '<?');
    //echo  $data; // Uncomment to show XML in comments
    $banana = substr($data, -49);
    if($ship != "PRIORITY"){return $banana;}
    $xml_parser = xml_parser_create();
    xml_parse_into_struct($xml_parser, $data, $vals, $index);
    xml_parser_free($xml_parser);
    $params = array();
    $level = array();
    foreach ($vals as $xml_elem) {
        if ($xml_elem['type'] == 'open') {
            if (array_key_exists('attributes',$xml_elem)) {
                list($level[$xml_elem['level']],$extra) = array_values($xml_elem['attributes']);
            } else {
            $level[$xml_elem['level']] = $xml_elem['tag'];
            }
        }
        if ($xml_elem['type'] == 'complete') {
            $start_level = 1;
            $php_stmt = '$params';
            while($start_level < $xml_elem['level']) {
                $php_stmt .= '[$level['.$start_level.']]';
                $start_level++;
            }
            $php_stmt .= '[$xml_elem[\'tag\']] = $xml_elem[\'value\'];';
            eval($php_stmt);
        }
    }
    
    curl_close($ch);
    // echo '<pre>'; print_r($params); echo'</pre>'; // Uncomment to see xml tags
    return $params['RATEV3RESPONSE']['1ST']['1']['RATE'];
}
?>