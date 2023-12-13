<?php
// Fetch data from Discord API
function fetchDataFromDiscord() {
    $botToken = getenv('TOKEN');

    if (!$botToken) {
        die('Discord bot token not provided.');
    }

    $url = 'https://discord.com/api/guilds/137344473976799233/members'; // Replace YOUR_GUILD_ID

    $headers = [
        'Authorization: Bot ' . $botToken,
    ];

    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    $response = curl_exec($ch);
    curl_close($ch);

    return json_decode($response, true);
}

// Get the data
$discordData = fetchDataFromDiscord();

// Output data as JSON
header('Content-Type: application/json');
echo json_encode($discordData);
?>
