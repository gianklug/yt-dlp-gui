// Download everything in backend
$("#download-button").on ('click', function (e) {
    // Ignore default action
    e.preventDefault();
    // Read form
    const playlist = $("#playlist").val();
    const url = $("#url").val();
    // Start the download
    fetch(`/download?url=${url}&playlist=${playlist}`)
    // Clear the url field
    $("#url").val("");
    // Display a toast
    $("#toast").toast("show");


});

// Automatic status refresh
//async function refreshStatus() {
//    let val = await fetch("/status");
//    $("#status").html(await val.text())
// }
// setInterval(function(){refreshStatus()}, 1000)

//const statusSocket = new WebSocket("ws://172.16.1.142:5000/");
//statusSocket.onmessage = (event) => {
//    console.log(event.data);
//  }
var socket = io();
socket.on('message', function(message) {
    $("#status").html(message)
});