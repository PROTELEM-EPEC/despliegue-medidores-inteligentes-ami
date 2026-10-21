
// Tab Navigation
document.querySelectorAll('.nav-item').forEach(button => {
  button.addEventListener('click', () => {
    document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

    button.classList.add('active');
    const tabId = button.getAttribute('data-tab');
    document.getElementById(tabId).classList.add('active');
  });
});

// Load Cronograma Data
async function loadData() {
  try {
    const cronResp = await fetch('data/cronograma_entregas_ami.json');
    const cronData = await cronResp.json();
    renderCronograma(cronData.entregas);
    renderSimulator(cronData.entregas);

    const planesResp = await fetch('data/diagnostico_planes_capital.json');
    const planesData = await planesResp.json();
    renderPlanes(planesData);

    const interiorResp = await fetch('data/relevamiento_interior.json');
    const interiorData = await interiorResp.json();
    renderInterior(interiorData);
  } catch (err) {
    console.error('Error fetching data:', err);
  }
}

function renderCronograma(entregas) {
  const tbody = document.getElementById('cronograma-tbody');
  tbody.innerHTML = '';
  entregas.forEach(item => {
    const tr = document.createElement('tr');
    const tagClass = item.marca === 'Sanxing' ? 'tag-sanxing' : 'tag-clou';
    tr.innerHTML = `
      <td><span class="tag-badge ${tagClass}">${item.marca} E${item.entrega_nro}</span></td>
      <td><strong>${item.cantidad.toLocaleString('es-AR')} u.</strong></td>
      <td>${item.dias_contractuales} d</td>
      <td><span class="status-pill" style="background: rgba(255,255,255,0.08); font-size: 11px;">VP ${item.vp_dias} d</span></td>
      <td><strong style="color: #38bdf8">${item.fecha_disponible}</strong></td>
      <td>${item.acumulado_total.toLocaleString('es-AR')} u.</td>
      <td style="color: #94a3b8; font-size: 12.5px;">${item.destino_principal}</td>
    `;
    tbody.appendChild(tr);
  });
}

function renderPlanes(planes) {
  const container = document.getElementById('planes-grid');
  container.innerHTML = '';
  for (const [key, p] of Object.entries(planes)) {
    const card = document.createElement('div');
    card.className = 'plan-card';
    card.innerHTML = `
      <div class="plan-header">
        <h3>${p.nombre}</h3>
        <span class="tag-badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8;">${p.prioridad}</span>
      </div>
      <div class="plan-body">
        <p><strong>Estado:</strong> ${p.estado_relevamiento}</p>
        <p><strong>Tecnología:</strong> <span style="color: #f59e0b;">${p.tecnologia_recomendada}</span></p>
        <p style="margin-top: 8px; font-size: 12px;">${p.notas}</p>
      </div>
    `;
    container.appendChild(card);
  }
}

function renderInterior(distritos) {
  const container = document.getElementById('interior-grid');
  container.innerHTML = '';
  for (const [key, d] of Object.entries(distritos)) {
    const card = document.createElement('div');
    card.className = 'plan-card';
    card.innerHTML = `
      <div class="plan-header">
        <h3>Distrito ${d.distrito}</h3>
        <span class="tag-badge tag-sanxing">${d.marca_asignada}</span>
      </div>
      <div class="plan-body">
        <p><strong>Puntos Relevados:</strong> <span style="font-size: 18px; font-weight: bold; color: #fff;">${d.puntos_relevados.toLocaleString('es-AR')}</span></p>
        <p><strong>Lote Asignado:</strong> ${d.lote_sugerido}</p>
        <p><strong>Estado Cartográfico:</strong> ${d.estado_poligonos}</p>
      </div>
    `;
    container.appendChild(card);
  }
}

function renderSimulator(entregas) {
  const btn = document.getElementById('btn-recalcular');
  btn.addEventListener('click', () => {
    const cuadrillas = parseInt(document.getElementById('input-cuadrillas').value) || 50;
    const rend = parseInt(document.getElementById('input-rendimiento').value) || 14;
    const porDia = cuadrillas * rend;
    const porMes = porDia * 22; // 22 días hábiles

    const output = document.getElementById('simulador-resultado');
    output.innerHTML = `
      <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.25); padding: 18px; border-radius: 8px; margin-top: 10px;">
        <h4 style="color: #10b981; margin-bottom: 8px;">Capacidad Mensual de Cuadrillas: ${porMes.toLocaleString('es-AR')} medidores/mes</h4>
        <p style="font-size: 13.5px; color: #cbd5e1;">Con <strong>${cuadrillas} cuadrillas</strong> activas instalando <strong>${rend} medidores/día</strong> cada una, se instalan <strong>${porDia.toLocaleString('es-AR')} equipos/día</strong>.</p>
        <p style="font-size: 13px; color: #94a3b8; margin-top: 6px;">En los primeros 5 meses (Feb - Jun 2027) ingresan 242.000 medidores. Las cuadrillas consumirán aproximadamente 75.000 - 85.000 equipos en dicho periodo, generando un stock de reserva de <strong>+150.000 medidores en almacenes</strong> para sostener el invierno sin quiebres.</p>
      </div>
    `;
  });
  btn.click();
}

document.addEventListener('DOMContentLoaded', loadData);
