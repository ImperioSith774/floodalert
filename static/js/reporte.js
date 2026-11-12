(function () {
  // ---------- Mapa de ubicación ----------
  const el = document.getElementById('mapa-ubicacion');
  const latInput = document.getElementById('lat');
  const lngInput = document.getElementById('lng');
  const coordTexto = document.getElementById('coord-texto');
  const centroChoco = [5.69, -76.66];

  const mapa = L.map(el).setView(centroChoco, 12);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap'
  }).addTo(mapa);

  let marcador = null;
  mapa.on('click', (e) => {
    const { lat, lng } = e.latlng;
    latInput.value = lat.toFixed(6);
    lngInput.value = lng.toFixed(6);
    coordTexto.textContent = `${lat.toFixed(5)}, ${lng.toFixed(5)}`;
    coordTexto.style.color = '#0e5fd8';
    if (marcador) marcador.setLatLng([lat, lng]);
    else marcador = L.circleMarker([lat, lng], {
      radius: 8, color: '#fff', weight: 2,
      fillColor: '#0e5fd8', fillOpacity: 1
    }).addTo(mapa);
  });

  // Centrar al elegir municipio
  const selMunicipio = document.getElementById('municipio');
  selMunicipio.addEventListener('change', () => {
    const op = selMunicipio.selectedOptions[0];
    if (op && op.dataset.lat) {
      mapa.setView([op.dataset.lat, op.dataset.lng], 14);
      if (!marcador) {
        latInput.value = op.dataset.lat;
        lngInput.value = op.dataset.lng;
        coordTexto.textContent = 'Centro del municipio — ajusta con un clic';
      }
    }
  });

  // ---------- Vista previa de fotos ----------
  const inputFotos = document.getElementById('fotos');
  const vista = document.getElementById('vista-previa');
  inputFotos.addEventListener('change', () => {
    vista.innerHTML = '';
    [...inputFotos.files].slice(0, 3).forEach(file => {
      if (!file.type.startsWith('image/')) return;
      const img = document.createElement('img');
      img.className = 'foto-mini';
      img.alt = file.name;
      img.src = URL.createObjectURL(file);
      vista.appendChild(img);
    });
    if (inputFotos.files.length > 3) {
      alert('Solo se permiten 3 imágenes. Se enviarán las 3 primeras.');
    }
  });

  // ---------- Validación de envío ----------
  document.getElementById('form-reporte').addEventListener('submit', (e) => {
    if (!latInput.value) {
      e.preventDefault();
      coordTexto.textContent = 'Debes marcar la ubicación en el mapa';
      coordTexto.style.color = '#b3261e';
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  });
})();
