(function () {
  "use strict";

  const mapa = L.map("mapa").setView([5.69, -76.66], 8);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap"
  }).addTo(mapa);

  const COLORES = {
    pendiente: "#e9a113",
    verificado: "#0e5fd8",
    seguimiento: "#6d3ec4",
    atendido: "#0b7a45",
    cerrado: "#8b8f96",
    rechazado: "#b3261e"
  };
  const ETIQUETAS = {
    pendiente: "Pendiente", verificado: "Verificado", seguimiento: "En seguimiento",
    atendido: "Atendido", cerrado: "Cerrado", rechazado: "Rechazado"
  };
  const NIVELES = {
    tobillo: "Hasta el tobillo", rodilla: "Hasta la rodilla", cintura: "Hasta la cintura",
    pecho: "Hasta el pecho", techo: "Sobre el techo"
  };

  const capa = L.layerGroup().addTo(mapa);
  const items = [];
  const lista = document.getElementById("lista-puntos");
  const contador = document.getElementById("contador");

  function pin(color) {
    return L.divIcon({
      className: "",
      html: `<span class="marker-pin" style="display:block;background:${color}"></span>`,
      iconSize: [18, 18], iconAnchor: [9, 9]
    });
  }

  function formatoFecha(iso) {
    const d = new Date(iso);
    return d.toLocaleString("es-CO", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
  }

  function popupHtml(p) {
    return `
      <div style="min-width:230px">
        <div class="d-flex align-items-center gap-2 mb-1">
          <span class="badge-fa badge-${p.estado}">${ETIQUETAS[p.estado]}</span>
          <span class="badge-nivel">${NIVELES[p.nivel_agua] || p.nivel_agua}</span>
        </div>
        <div class="popup-titulo">${p.barrio}</div>
        <div class="text-muted">${p.municipio} · ${formatoFecha(p.fecha_incidente)}</div>
        ${p.foto ? `<img class="popup-foto" src="/uploads/${p.foto}" alt="Evidencia">` : ""}
        <a href="/detalle/${p.id_incidente}" class="d-inline-block mt-2">Ver seguimiento completo →</a>
      </div>`;
  }

  function agregar(p) {
    const color = COLORES[p.estado] || "#0e5fd8";
    const m = L.marker([p.lat, p.lng], { icon: pin(color) })
      .addTo(capa)
      .bindPopup(popupHtml(p));
    items.push({ ...p, marcador: m });
  }

  function fila(i, p) {
    const div = document.createElement("button");
    div.className = "report-item w-100 text-start border-0 bg-transparent p-0 py-2 px-1";
    div.style = "border-top:1px solid var(--border)!important";
    div.innerHTML = `
      <div class="d-flex align-items-center gap-2">
        <span class="marker-pin" style="display:inline-block;flex:none;background:${COLORES[p.estado]};width:10px;height:10px"></span>
        <div style="min-width:0">
          <div class="fw-semibold" style="font-size:13.5px">${p.barrio}</div>
          <div class="report-meta text-dark" style="color:var(--text-3)!important">${p.municipio}</div>
        </div>
      </div>`;
    div.addEventListener("click", () => {
      p.marcador.openPopup();
      mapa.flyTo([p.lat, p.lng], 14, { duration: .6 });
    });
    return div;
  }

  function pintarLista() {
    lista.innerHTML = "";
    items.forEach((p, i) => lista.appendChild(fila(i, p)));
    contador.textContent = `(${items.length})`;
  }

  function cargar() {
    capa.clearLayers();
    items.length = 0;
    const estado = document.getElementById("f-estado").value;
    const municipio = document.getElementById("f-municipio").value;
    const params = new URLSearchParams();
    if (estado) params.set("estado", estado);
    if (municipio) params.set("municipio", municipio);
    fetch(`/api/incidentes?${params}`)
      .then(r => r.json())
      .then(data => {
        data.forEach(agregar);
        pintarLista();
        if (data.length) {
          mapa.fitBounds(items.map(i => [i.lat, i.lng]), { padding: [40, 40], maxZoom: 13 });
        }
      });
  }

  document.getElementById("f-estado").addEventListener("change", cargar);
  document.getElementById("f-municipio").addEventListener("change", cargar);
  cargar();
})();
