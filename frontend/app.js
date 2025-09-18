let map;
    let userMarker;
    let shelterMarkers = [];

    // Función para obtener los albergues del API
    async function loadShelters() {
      try {
        const response = await fetch('http://localhost:10000/shelters', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const shelters = await response.json();
        return shelters;
      } catch (error) {
        console.error('Error al cargar los albergues:', error);
        return [];
      }
    }

    // Función para mostrar los albergues en el mapa
    function displayShelters(shelters) {
      // Limpiar marcadores existentes
      shelterMarkers.forEach(marker => marker.setMap(null));
      shelterMarkers = [];

      shelters.forEach(shelter => {
        const marker = new google.maps.Marker({
          position: { 
            lat: parseFloat(shelter.latitude), 
            lng: parseFloat(shelter.longitude) 
          },
          map: map,
          title: shelter.name,
          icon: {
            url: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png' // Marcador azul para diferenciar de la ubicación del usuario
          }
        });

        // Agregar InfoWindow para mostrar información del albergue
        const infoWindow = new google.maps.InfoWindow({
          content: `
            <div>
              <h3>${shelter.name}</h3>
              <p>Dirección: ${shelter.address}</p>
              <p>Capacidad: ${shelter.capacity}</p>
              <p>Teléfono: ${shelter.phone}</p>
            </div>
          `
        });

        marker.addListener('click', () => {
          infoWindow.open(map, marker);
        });

        shelterMarkers.push(marker);
      });
    }

    function initMap() {
      // Inicializar el mapa centrado en una ubicación predeterminada
      map = new google.maps.Map(document.getElementById('map'), {
        zoom: 15,
        center: { lat: 4.7110, lng: -74.0721 }, // Bogotá como ejemplo
        streetViewControl: false,
        mapTypeControl: false
      });

      // Cargar y mostrar los albergues
      loadShelters().then(shelters => {
        displayShelters(shelters);
      });

      // Intentar obtener la ubicación del usuario
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          (position) => {
            const pos = {
              lat: position.coords.latitude,
              lng: position.coords.longitude
            };

            // Centrar el mapa en la ubicación del usuario
            map.setCenter(pos);

            // Crear un marcador en la ubicación del usuario
            userMarker = new google.maps.Marker({
              position: pos,
              map: map,
              title: 'Tu ubicación'
            });
          },
          () => {
            console.error('Error al obtener la ubicación');
          }
        );
      }
    }

    // Función para enviar la alerta al microservicio
    async function sendAlert(latitude, longitude) {
      try {
        const response = await fetch('http://localhost:10000/alerts', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            latitude: latitude,
            longitude: longitude
          })
        });

        if (!response.ok) {
          throw new Error(`Error HTTP: ${response.status}`);
        }

        const data = await response.json();
        alert('Alerta SOS enviada con éxito');
        return data;
      } catch (error) {
        console.error('Error al enviar la alerta:', error);
        alert('Error al enviar la alerta SOS. Por favor, intenta de nuevo.');
      }
    }

    // Manejar el clic del botón SOS
    document.getElementById('sos-button').addEventListener('click', async function() {
      if (!userMarker) {
        alert('No se ha podido determinar tu ubicación');
        return;
      }

      const position = userMarker.getPosition();
      await sendAlert(position.lat(), position.lng());
      // Enviar la alerta al microservicio
      await sendAlert(latitude, longitude);
      
      // Enviar el mensaje de WhatsApp
      sendWhatsAppMessage(latitude, longitude);
    });