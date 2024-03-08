var map = L.map('map').setView([41.1579, -8.6291], 14);
map.getPane('tilePane').style.opacity = 0.4;
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map);


// Load and display GPX file
var gpx = "{% static 'gpx/rota.gpx' %}";
//var gpx = 'rota.gpx';

new L.GPX(gpx, {
    async: true
}).on('loaded', function(e) {
    var gpxLayer = e.target;
    var track = gpxLayer.getLayers()[0];

    track.eachLayer(function (segment) {
        var points = segment.getLatLngs();
        for (var i = 0; i < points.length - 1; i++) {
            var speed = calculateSpeed(points[i], points[i + 1]);
            var color = getColorFromSpeed(speed);
            L.polyline([points[i], points[i + 1]], { color: color }).addTo(map);
        }
    });

    map.fitBounds(track.getBounds());
}).addTo(map);

// Function to calculate speed between two points
function calculateSpeed(point1, point2) {
    var distance = point1.distanceTo(point2); // Distance in meters
    var timeDiff = (point2.meta.time - point1.meta.time) / 1000; // Time difference in seconds
    var speed = distance / timeDiff; // Speed in meters per second
    return speed;
}

function getColorFromSpeed(speed) {
    // Define color ranges and corresponding speeds
    var speedScale = chroma.scale(['blue', 'green', 'yellow', 'orange', 'red']).domain([0, 14]); // Adjust the domain as per your speed range

    // Use Chroma.js to interpolate colors based on the speed
    return speedScale(speed).hex();
}


map.on('layeradd', function(event) {
    // Check if the added layer is a marker layer
    if (event.layer instanceof L.Marker) {
        // Remove the marker from the map
        map.removeLayer(event.layer);
    }
});

