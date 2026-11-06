/**
 * Mini-Courier Planner - Frontend Application
 * Handles State, Canvas Map Rendering, DP Matrix Inspection, Courier Van Animation,
 * Vector SVG Route Visualization, and Real-Time Algorithmic Pipeline Optimization.
 */

// Application State
const state = {
  dataset: 'small',
  graph: { directed: false, nodes: [], edges: [] },
  parcels: [],
  vehicle_capacity: 40,
  sort_strategy: 'deadline_priority',
  sort_algorithm: 'mergesort',
  use_two_opt: true,
  depot_node: 'Depot',
  speed_kmh: 40.0,
  lastResult: null,
  activeTab: 'tab-manifest',
  manifestFilter: 'all',
  manifestSearch: '',
  selectedNode: null,
  showDistanceLabels: true,
  toastTimeout: null,

  // DP Matrix Inspector Windowing
  dpWindowMode: 'auto', // 'auto', 'optimal', 'base', 'all', 'custom'
  dpWindowStart: 0,
  dpWindowEnd: 100,

  // Map Canvas & Pan/Zoom
  map: {
    canvas: null,
    ctx: null,
    zoom: 1.0,
    offsetX: 0,
    offsetY: 0,
    isDragging: false,
    dragStartX: 0,
    dragStartY: 0,
    hoveredNode: null,
    padding: 60,
    hasFitted: false,
    needsFit: true,
  },

  // Courier Van Simulation
  sim: {
    active: false,
    animId: null,
    progress: 0.0, // 0.0 to 1.0 along entire detailed path
    speed: 1.0,
    pathPoints: [], // Array of {x, y, node_id, cum_dist}
    totalPathDistance: 0,
  }
};

// ==========================================================================
// Initialization & Event Wiring
// ==========================================================================
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initTabs();
  initControls();
  initMapCanvas();
  initExportMenu();
  initCustomImports();
  initToast();
  loadDataset('small');
});

function initTheme() {
  let saved = 'dark';
  try {
    saved = localStorage.getItem('mcp_theme') || 'dark';
  } catch (e) {
    saved = 'dark';
  }
  document.body.className = `theme-${saved}`;

  const toggleBtn = document.getElementById('themeToggleBtn');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      const isDark = document.body.classList.contains('theme-dark');
      const newTheme = isDark ? 'light' : 'dark';
      document.body.className = `theme-${newTheme}`;
      try {
        localStorage.setItem('mcp_theme', newTheme);
      } catch (e) {
        // Ignore in restricted iframe
      }
      renderMap();
    });
  }
}

function initTabs() {
  const tabBtns = document.querySelectorAll('.tab-btn');
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      const targetId = btn.getAttribute('data-tab');
      const targetPane = document.getElementById(targetId);
      if (targetPane) {
        targetPane.classList.add('active');
        state.activeTab = targetId;

        if (targetId === 'tab-map') {
          // Re-measure and fit view properly
          resizeCanvas();
          if (state.map.needsFit || !state.map.hasFitted) {
            fitMapToScreen();
            state.map.hasFitted = true;
            state.map.needsFit = false;
          }
          renderMap();
        }
      }
    });
  });
}

function initControls() {
  // Dataset Select
  const datasetSelect = document.getElementById('datasetSelect');
  datasetSelect.addEventListener('change', (e) => {
    const val = e.target.value;
    if (val === 'custom') {
      state.dataset = 'custom';
      // Switch to parcel manager
      const tabBtn = document.querySelector('[data-tab="tab-parcels"]');
      if (tabBtn) tabBtn.click();
      showToast('Custom Dataset mode active. Manage parcel pool or import CSV/JSON files below.', 'info');
    } else {
      loadDataset(val);
    }
  });

  // Capacity Slider & Number Input Sync
  const capSlider = document.getElementById('capacitySlider');
  const capInput = document.getElementById('capacityInput');
  const capDisplay = document.getElementById('capacityDisplay');

  capSlider.addEventListener('input', (e) => {
    const val = parseInt(e.target.value, 10);
    capInput.value = val;
    capDisplay.textContent = val;
    state.vehicle_capacity = val;
  });

  capSlider.addEventListener('change', () => {
    runOptimization();
  });

  capInput.addEventListener('change', (e) => {
    let val = parseInt(e.target.value, 10) || 40;
    val = Math.max(1, Math.min(1000, val));
    capInput.value = val;
    capSlider.value = Math.min(150, val);
    capDisplay.textContent = val;
    state.vehicle_capacity = val;
    runOptimization();
  });

  // Algorithm Controls
  document.getElementById('sortStrategySelect').addEventListener('change', (e) => {
    state.sort_strategy = e.target.value;
    runOptimization();
  });

  document.getElementById('sortAlgoSelect').addEventListener('change', (e) => {
    state.sort_algorithm = e.target.value;
    runOptimization();
  });

  document.getElementById('depotSelect').addEventListener('change', (e) => {
    state.depot_node = e.target.value;
    runOptimization();
  });

  document.getElementById('useTwoOptToggle').addEventListener('change', (e) => {
    state.use_two_opt = e.target.checked;
    runOptimization();
  });

  document.getElementById('vehicleSpeedInput').addEventListener('change', (e) => {
    state.speed_kmh = Math.max(5, parseFloat(e.target.value) || 40.0);
    if (state.lastResult) {
      updateItineraryView(state.lastResult.route_result.itinerary);
    }
  });

  // Run Planner Button
  document.getElementById('runPlannerBtn').addEventListener('click', () => {
    runOptimization();
  });

  // Manifest Filters
  const filterPills = document.querySelectorAll('.filter-pills .pill');
  filterPills.forEach(pill => {
    pill.addEventListener('click', () => {
      filterPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      state.manifestFilter = pill.getAttribute('data-filter');
      renderManifestTable();
    });
  });

  document.getElementById('manifestSearchInput').addEventListener('input', (e) => {
    state.manifestSearch = e.target.value.toLowerCase().trim();
    renderManifestTable();
  });

  // Parcel Form
  document.getElementById('addParcelForm').addEventListener('submit', (e) => {
    e.preventDefault();
    handleAddParcelForm();
  });

  document.getElementById('generateRandomParcelsBtn').addEventListener('click', () => {
    generateRandomParcels(5);
  });

  document.getElementById('resetParcelsToDefaultBtn').addEventListener('click', () => {
    loadDataset(state.dataset === 'custom' ? 'small' : state.dataset);
  });

  document.getElementById('clearAllParcelsBtn').addEventListener('click', () => {
    if (confirm('Are you sure you want to clear all parcels from the active pool?')) {
      state.parcels = [];
      state.dataset = 'custom';
      document.getElementById('datasetSelect').value = 'custom';
      renderParcelPoolTable();
      runOptimization();
      showToast('All parcels cleared. Add or import parcels to plan dispatch.', 'warning');
    }
  });

  // Benchmarks Tab Buttons
  document.getElementById('runSortingBenchmarkBtn').addEventListener('click', () => {
    runSortingBenchmark();
  });

  // DP Jump Buttons
  document.getElementById('jumpBacktrackStartBtn').addEventListener('click', () => {
    jumpToDpCell(state.parcels.length, state.vehicle_capacity);
  });

  document.getElementById('jumpOriginBtn').addEventListener('click', () => {
    jumpToDpCell(0, 0);
  });
}

function initExportMenu() {
  const exportBtn = document.getElementById('exportBtn');
  const menu = document.getElementById('exportMenu');

  exportBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    menu.classList.toggle('hidden');
  });

  document.addEventListener('click', () => {
    menu.classList.add('hidden');
  });

  document.getElementById('exportJsonBtn').addEventListener('click', (e) => {
    e.preventDefault();
    downloadJsonManifest();
  });

  document.getElementById('exportCsvBtn').addEventListener('click', (e) => {
    e.preventDefault();
    downloadCsvManifest();
  });

  document.getElementById('exportItineraryCsvBtn').addEventListener('click', (e) => {
    e.preventDefault();
    downloadItineraryCsv();
  });

  document.getElementById('exportMapSvgBtn').addEventListener('click', (e) => {
    e.preventDefault();
    exportMapSvg();
  });

  document.getElementById('printReportBtn').addEventListener('click', (e) => {
    e.preventDefault();
    window.print();
  });

  // Import buttons in nav dropdown
  document.getElementById('importParcelsNavBtn').addEventListener('click', (e) => {
    e.preventDefault();
    document.getElementById('importParcelsFileInput').click();
  });

  document.getElementById('importGraphNavBtn').addEventListener('click', (e) => {
    e.preventDefault();
    document.getElementById('importGraphFileInput').click();
  });
}

function initCustomImports() {
  const parcelsFileInput = document.getElementById('importParcelsFileInput');
  const graphFileInput = document.getElementById('importGraphFileInput');

  parcelsFileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      importParcelsFromCsv(event.target.result);
      parcelsFileInput.value = '';
    };
    reader.readAsText(file);
  });

  graphFileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      importGraphFromJson(event.target.result);
      graphFileInput.value = '';
    };
    reader.readAsText(file);
  });

  // Buttons in Parcel Manager tab
  const btnImportParcels = document.getElementById('importParcelsBtn');
  if (btnImportParcels) {
    btnImportParcels.addEventListener('click', () => parcelsFileInput.click());
  }
  const btnImportGraph = document.getElementById('importGraphBtn');
  if (btnImportGraph) {
    btnImportGraph.addEventListener('click', () => graphFileInput.click());
  }

  // Button on map controls for Vector SVG export
  const btnExportSvgMap = document.getElementById('exportSvgMapBtn');
  if (btnExportSvgMap) {
    btnExportSvgMap.addEventListener('click', () => exportMapSvg());
  }
}

function initToast() {
  const closeBtn = document.getElementById('toastCloseBtn');
  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      document.getElementById('toastNotification').classList.add('hidden');
    });
  }
}

function showToast(message, type = 'info', timeoutMs = 4500) {
  const toast = document.getElementById('toastNotification');
  if (!toast) return;
  const msgEl = document.getElementById('toastMessage');
  const iconEl = document.getElementById('toastIcon');

  msgEl.textContent = message;
  toast.className = `toast-notification toast-${type}`;

  const icons = {
    info: 'ℹ️',
    success: '✅',
    warning: '⚠️',
    error: '❌'
  };
  iconEl.textContent = icons[type] || 'ℹ️';

  if (state.toastTimeout) {
    clearTimeout(state.toastTimeout);
  }
  state.toastTimeout = setTimeout(() => {
    toast.classList.add('hidden');
  }, timeoutMs);
}

// ==========================================================================
// API Communication
// ==========================================================================
async function loadDataset(datasetName) {
  setApiStatus('loading', `Loading ${datasetName}...`);
  try {
    const res = await fetch(`/api/datasets/${datasetName}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    state.dataset = datasetName;
    document.getElementById('datasetSelect').value = datasetName;
    state.graph = data.graph;
    state.parcels = data.parcels;

    if (data.recommended_capacity) {
      state.vehicle_capacity = data.recommended_capacity;
      document.getElementById('capacitySlider').value = Math.min(150, data.recommended_capacity);
      document.getElementById('capacityInput').value = data.recommended_capacity;
      document.getElementById('capacityDisplay').textContent = data.recommended_capacity;
    }

    state.map.hasFitted = false;
    state.map.needsFit = true;

    populateDepotAndDestDropdowns();
    renderParcelPoolTable();
    await runOptimization();
    setApiStatus('ready', 'Optimized & Ready');
    showToast(`Loaded ${data.id.toUpperCase()} dataset (${state.graph.nodes.length} nodes, ${state.parcels.length} parcels).`, 'success');
  } catch (err) {
    console.error('Failed to load dataset:', err);
    setApiStatus('error', 'Dataset Load Error');
    showToast(`Failed to load dataset: ${err.message}`, 'error');
  }
}

async function runOptimization() {
  const runBtn = document.getElementById('runPlannerBtn');
  runBtn.disabled = true;
  setApiStatus('loading', 'Solving 0/1 DP & Route...');

  const payload = {
    parcels: state.parcels,
    graph: state.graph,
    vehicle_capacity: state.vehicle_capacity,
    sort_strategy: state.sort_strategy,
    sort_algorithm: state.sort_algorithm,
    use_two_opt: state.use_two_opt,
    depot_node: state.depot_node,
    speed_kmh: state.speed_kmh,
  };

  try {
    const t0 = performance.now();
    const res = await fetch('/api/plan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.error || `HTTP ${res.status}`);
    }

    const result = await res.json();
    state.lastResult = result;

    // Update all dashboard sections
    updateKpiBanner(result);
    renderManifestTable();
    updateItineraryView(result.route_result.itinerary);
    renderDpMatrix(result.packing_result.dp_table, result.packing_result.backtrack_path);
    updateBenchmarkView(result.benchmarks);
    updateRouteStopTags(result.route_result.ordered_stops);
    prepareVanSimulationPath(result);

    if (state.activeTab === 'tab-map') {
      if (state.map.needsFit || !state.map.hasFitted) {
        resizeCanvas();
        fitMapToScreen();
        state.map.hasFitted = true;
        state.map.needsFit = false;
      }
      renderMap();
    }

    setApiStatus('ready', `Solved in ${(performance.now() - t0).toFixed(1)} ms`);
  } catch (err) {
    console.error('Optimization error:', err);
    showToast(`Optimization Error: ${err.message}`, 'error', 6000);
    setApiStatus('error', 'Optimization Error');
  } finally {
    runBtn.disabled = false;
  }
}

async function runSortingBenchmark() {
  const resultsDiv = document.getElementById('sortingResultsDisplay');
  resultsDiv.innerHTML = '<p class="text-muted">Running 10 benchmark iterations...</p>';

  try {
    const res = await fetch('/api/benchmark', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ parcels: state.parcels })
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const s = data.sorting;

    resultsDiv.innerHTML = `
      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem; margin-top: 0.5rem;">
        <div style="background: var(--bg-tertiary); padding: 0.5rem; border-radius: 6px;">
          <div style="color: var(--text-muted); font-size: 0.7rem;">MergeSort (Stable)</div>
          <div style="font-weight: 700; color: var(--accent-success);">${s.mergesort_time_ms.toFixed(3)} ms</div>
        </div>
        <div style="background: var(--bg-tertiary); padding: 0.5rem; border-radius: 6px;">
          <div style="color: var(--text-muted); font-size: 0.7rem;">QuickSort (In-place)</div>
          <div style="font-weight: 700; color: var(--accent-primary);">${s.quicksort_time_ms.toFixed(3)} ms</div>
        </div>
        <div style="background: var(--bg-tertiary); padding: 0.5rem; border-radius: 6px;">
          <div style="color: var(--text-muted); font-size: 0.7rem;">Python Timsort</div>
          <div style="font-weight: 700; color: var(--accent-info);">${s.timsort_time_ms.toFixed(3)} ms</div>
        </div>
      </div>
      <div style="margin-top: 0.5rem; font-size: 0.75rem; color: var(--text-secondary);">
        Tested on <strong>${s.count}</strong> parcels. Output verification: MergeSort matches standard Timsort: <strong>${s.merge_equals_tim ? '✓ Verified' : '✗ Discrepancy'}</strong>.
      </div>
    `;
    showToast('Sorting benchmark completed successfully!', 'success');
  } catch (err) {
    resultsDiv.innerHTML = `<span class="text-danger">Benchmark failed: ${err.message}</span>`;
    showToast(`Benchmark error: ${err.message}`, 'error');
  }
}

function setApiStatus(type, message) {
  const badge = document.getElementById('apiStatusBadge');
  const text = badge.querySelector('.status-text');
  text.textContent = message;

  badge.className = 'status-badge';
  if (type === 'loading') {
    badge.style.color = 'var(--accent-info)';
    badge.style.borderColor = 'rgba(6, 182, 212, 0.4)';
    badge.style.backgroundColor = 'rgba(6, 182, 212, 0.15)';
  } else if (type === 'error') {
    badge.style.color = 'var(--accent-danger)';
    badge.style.borderColor = 'rgba(239, 68, 68, 0.4)';
    badge.style.backgroundColor = 'rgba(239, 68, 68, 0.15)';
  } else {
    badge.style.color = 'var(--accent-success)';
    badge.style.borderColor = 'rgba(16, 185, 129, 0.3)';
    badge.style.backgroundColor = 'rgba(16, 185, 129, 0.15)';
  }
}

// ==========================================================================
// KPI & Summary Views
// ==========================================================================
function updateKpiBanner(res) {
  const pack = res.packing_result;
  const route = res.route_result;
  const bench = res.benchmarks;

  // Capacity & Weight
  document.getElementById('kpiWeight').textContent = `${pack.total_weight} / ${pack.capacity} kg`;
  const utilBadge = document.getElementById('kpiUtilizationBadge');
  utilBadge.textContent = `${pack.capacity_utilization.toFixed(1)}%`;
  document.getElementById('kpiProgressBar').style.width = `${Math.min(100, pack.capacity_utilization)}%`;

  if (pack.capacity_utilization > 90) {
    utilBadge.className = 'badge badge-success';
  } else if (pack.capacity_utilization > 60) {
    utilBadge.className = 'badge badge-info';
  } else {
    utilBadge.className = 'badge badge-warning';
  }

  // Delivery Value & Optimality Gap
  document.getElementById('kpiValue').textContent = `${pack.total_value} pts`;
  const optGap = bench.knapsack.optimality_gap_percent;
  const optBadge = document.getElementById('kpiOptimalityBadge');
  if (optGap > 0) {
    optBadge.textContent = `+${optGap.toFixed(1)}% vs Greedy`;
    optBadge.className = 'badge badge-accent';
  } else {
    optBadge.textContent = '100% Optimal';
    optBadge.className = 'badge badge-success';
  }
  document.getElementById('kpiGreedySubtext').textContent = `Greedy heuristic baseline: ${bench.knapsack.greedy_value} pts (${bench.knapsack.greedy_weight} kg)`;

  // Route Distance & ETA
  document.getElementById('kpiDistance').textContent = `${route.total_distance.toFixed(1)} km`;
  const totalEtaMinutes = route.itinerary && route.itinerary.length > 0
    ? route.itinerary[route.itinerary.length - 1].eta_minutes
    : Math.round((route.total_distance / state.speed_kmh) * 60);

  const hours = Math.floor(totalEtaMinutes / 60);
  const mins = Math.round(totalEtaMinutes % 60);
  document.getElementById('kpiEtaBadge').textContent = hours > 0 ? `${hours}h ${mins}m ETA` : `${mins} min ETA`;

  const distSaved = bench.tsp.distance_saved_km;
  const redPct = bench.tsp.reduction_percent;
  document.getElementById('kpiSavingsSubtext').textContent = state.use_two_opt
    ? `2-Opt savings: ${distSaved} km (${redPct}% reduction)`
    : `2-Opt disabled: Nearest-Neighbor raw`;

  // Computational Latency
  document.getElementById('kpiRuntime').textContent = `${res.total_runtime_ms.toFixed(2)} ms`;
  const bk = res.runtime_breakdown_ms;
  document.getElementById('kpiBreakdownSubtext').textContent = `DP: ${bk.knapsack_dp_ms}ms | Dijkstra: ${bk.dijkstra_ms}ms | TSP: ${bk.tsp_routing_ms}ms`;
}

// ==========================================================================
// Manifest & Itinerary Views
// ==========================================================================
function renderManifestTable() {
  if (!state.lastResult) return;

  const pack = state.lastResult.packing_result;
  const selectedIds = new Set(pack.selected_parcels.map(p => p.parcel_id));
  const tbody = document.getElementById('parcelsTableBody');
  tbody.innerHTML = '';

  const allParcels = state.parcels;
  document.getElementById('allCount').textContent = allParcels.length;
  document.getElementById('selectedCount').textContent = pack.selected_parcels.length;
  document.getElementById('rejectedCount').textContent = pack.rejected_parcels.length;

  const filter = state.manifestFilter;
  const query = state.manifestSearch;

  let displayCount = 0;

  allParcels.forEach((p) => {
    const isSelected = selectedIds.has(p.parcel_id);

    // Filter check
    if (filter === 'selected' && !isSelected) return;
    if (filter === 'rejected' && isSelected) return;

    // Search query check
    if (query) {
      const match = p.parcel_id.toLowerCase().includes(query) ||
                    p.destination.toLowerCase().includes(query) ||
                    (p.customer_name && p.customer_name.toLowerCase().includes(query));
      if (!match) return;
    }

    displayCount++;
    const tr = document.createElement('tr');
    tr.className = isSelected ? 'row-selected' : 'row-rejected';

    const decisionNote = isSelected
      ? '<span style="color: var(--accent-success); font-weight:600;">✓ Loaded</span> (Optimal knapsack subset)'
      : '<span style="color: var(--accent-danger);">✗ Deferred</span> (Exceeds payload budget)';

    tr.innerHTML = `
      <td>
        <span class="badge ${isSelected ? 'badge-success' : 'badge-danger'}">
          ${isSelected ? 'PACKED' : 'LEFT BEHIND'}
        </span>
      </td>
      <td><strong>${p.parcel_id}</strong></td>
      <td><span class="badge badge-neutral">${p.destination}</span></td>
      <td>${p.weight} kg</td>
      <td>${'★'.repeat(p.priority)}${'☆'.repeat(5 - p.priority)}</td>
      <td>${p.deadline.toFixed(1)} hrs</td>
      <td><strong>${p.value}</strong></td>
      <td>${p.customer_name || '<em style="color:var(--text-muted)">Unspecified</em>'}</td>
      <td style="font-size:0.75rem;">${decisionNote}</td>
    `;
    tbody.appendChild(tr);
  });

  if (displayCount === 0) {
    const tr = document.createElement('tr');
    tr.innerHTML = '<td colspan="9" style="text-align:center; padding: 2rem; color: var(--text-muted);">No parcels match the current filter or search criteria.</td>';
    tbody.appendChild(tr);
  }
}

function updateItineraryView(itinerary) {
  const container = document.getElementById('itineraryTimeline');
  container.innerHTML = '';
  document.getElementById('itineraryStopCount').textContent = `${itinerary.length} Tour Steps`;

  itinerary.forEach((step, idx) => {
    const item = document.createElement('div');
    item.className = 'timeline-item';

    const dotClass = step.is_depot ? 'timeline-dot depot' : 'timeline-dot';
    const pkgInfo = step.parcels_count > 0
      ? `<span class="badge badge-success" style="margin-left:0.4rem;">${step.parcels_count} parcel(s)</span>`
      : '';

    item.innerHTML = `
      <div class="${dotClass}"></div>
      <div class="timeline-content">
        <div class="timeline-header">
          <span>Stop #${idx + 1}: <strong>${step.node_id}</strong> ${step.is_depot ? '(Depot)' : ''} ${pkgInfo}</span>
          <span class="timeline-eta">ETA: +${step.eta_minutes}m</span>
        </div>
        <div class="timeline-details">
          <span>Leg: ${step.leg_distance_km} km | Total: ${step.cumulative_distance_km} km</span>
          ${step.parcels_dropped.length > 0 ? `
            <div style="margin-top: 0.35rem; font-size: 0.725rem; color: var(--text-secondary);">
              Dropping: ${step.parcels_dropped.map(p => `<strong>${p.parcel_id}</strong> (${p.weight}kg, ${p.value}pts)`).join(', ')}
            </div>
          ` : ''}
        </div>
      </div>
    `;
    container.appendChild(item);
  });
}

function updateRouteStopTags(stops) {
  const container = document.getElementById('routeStopList');
  container.innerHTML = '';
  stops.forEach((stop, i) => {
    const tag = document.createElement('span');
    tag.className = stop === state.depot_node ? 'stop-tag depot-tag' : 'stop-tag';
    tag.textContent = `${i + 1}. ${stop}`;
    tag.title = `Stop #${i + 1}: ${stop}`;
    tag.addEventListener('click', () => {
      selectNode(stop);
    });
    container.appendChild(tag);
  });
}

// ==========================================================================
// Interactive Canvas Route Map
// ==========================================================================
function initMapCanvas() {
  const canvas = document.getElementById('routeCanvas');
  state.map.canvas = canvas;
  state.map.ctx = canvas.getContext('2d');

  resizeCanvas();
  window.addEventListener('resize', () => {
    resizeCanvas();
    if (state.activeTab === 'tab-map') {
      renderMap();
    }
  });

  // Mouse pan & zoom listeners
  canvas.addEventListener('mousedown', (e) => {
    state.map.isDragging = true;
    state.map.dragStartX = e.clientX - state.map.offsetX;
    state.map.dragStartY = e.clientY - state.map.offsetY;
  });

  window.addEventListener('mouseup', () => {
    state.map.isDragging = false;
  });

  canvas.addEventListener('mousemove', (e) => {
    if (state.map.isDragging) {
      state.map.offsetX = e.clientX - state.map.dragStartX;
      state.map.offsetY = e.clientY - state.map.dragStartY;
      renderMap();
    } else {
      handleMapHover(e);
    }
  });

  canvas.addEventListener('wheel', (e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.15 : 0.87;
    zoomAt(e.offsetX, e.offsetY, zoomFactor);
  });

  canvas.addEventListener('click', () => {
    if (state.map.hoveredNode) {
      selectNode(state.map.hoveredNode.node_id);
    }
  });

  // Floating controls
  document.getElementById('zoomInBtn').addEventListener('click', () => {
    const rect = canvas.getBoundingClientRect();
    zoomAt(rect.width / 2, rect.height / 2, 1.25);
  });

  document.getElementById('zoomOutBtn').addEventListener('click', () => {
    const rect = canvas.getBoundingClientRect();
    zoomAt(rect.width / 2, rect.height / 2, 0.8);
  });

  document.getElementById('resetViewBtn').addEventListener('click', () => {
    fitMapToScreen();
    renderMap();
    showToast('Map view centered and scale reset.', 'info');
  });

  const toggleLabelsBtn = document.getElementById('toggleLabelsBtn');
  toggleLabelsBtn.addEventListener('click', () => {
    state.showDistanceLabels = !state.showDistanceLabels;
    toggleLabelsBtn.classList.toggle('active', state.showDistanceLabels);
    renderMap();
  });

  // Van Simulation Controls
  document.getElementById('simPlayPauseBtn').addEventListener('click', toggleVanSimulation);
  document.getElementById('simResetBtn').addEventListener('click', resetVanSimulation);

  document.querySelectorAll('.sim-speed-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.sim-speed-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.sim.speed = parseFloat(btn.getAttribute('data-speed')) || 1.0;
    });
  });
}

function resizeCanvas() {
  const canvas = state.map.canvas;
  if (!canvas) return;
  const container = canvas.parentElement;
  if (!container) return;
  const rect = container.getBoundingClientRect();
  if (rect.width === 0 || rect.height === 0) return;

  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.round(rect.width * dpr);
  canvas.height = Math.round(rect.height * dpr);
  canvas.style.width = `${rect.width}px`;
  canvas.style.height = `${rect.height}px`;

  state.map.ctx.scale(dpr, dpr);
}

function fitMapToScreen() {
  const nodes = state.graph.nodes || [];
  if (nodes.length === 0) return;

  const canvas = state.map.canvas;
  if (!canvas) return;
  const container = canvas.parentElement;
  if (!container) return;
  const rect = container.getBoundingClientRect();

  if (rect.width === 0 || rect.height === 0) {
    state.map.needsFit = true;
    return;
  }

  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  nodes.forEach(n => {
    if (n.x < minX) minX = n.x;
    if (n.x > maxX) maxX = n.x;
    if (n.y < minY) minY = n.y;
    if (n.y > maxY) maxY = n.y;
  });

  const widthWorld = (maxX - minX) || 50;
  const heightWorld = (maxY - minY) || 50;

  const padding = state.map.padding;
  const scaleX = (rect.width - padding * 2) / widthWorld;
  const scaleY = (rect.height - padding * 2) / heightWorld;
  state.map.zoom = Math.min(scaleX, scaleY);

  const centerX = (minX + maxX) / 2;
  const centerY = (minY + maxY) / 2;

  state.map.offsetX = rect.width / 2 - centerX * state.map.zoom;
  state.map.offsetY = rect.height / 2 - centerY * state.map.zoom;
  state.map.hasFitted = true;
  state.map.needsFit = false;
}

function zoomAt(screenX, screenY, factor) {
  const newZoom = Math.max(0.2, Math.min(10.0, state.map.zoom * factor));
  const worldX = (screenX - state.map.offsetX) / state.map.zoom;
  const worldY = (screenY - state.map.offsetY) / state.map.zoom;

  state.map.zoom = newZoom;
  state.map.offsetX = screenX - worldX * newZoom;
  state.map.offsetY = screenY - worldY * newZoom;
  renderMap();
}

function worldToScreen(wx, wy) {
  return {
    x: wx * state.map.zoom + state.map.offsetX,
    y: wy * state.map.zoom + state.map.offsetY,
  };
}

function handleMapHover(e) {
  if (!state.map.canvas) return;
  const rect = state.map.canvas.getBoundingClientRect();
  const mouseX = e.clientX - rect.left;
  const mouseY = e.clientY - rect.top;

  const nodes = state.graph.nodes || [];
  let found = null;
  const threshold = 14; // pixels

  for (const n of nodes) {
    const sp = worldToScreen(n.x, n.y);
    const dist = Math.hypot(sp.x - mouseX, sp.y - mouseY);
    if (dist <= threshold) {
      found = n;
      break;
    }
  }

  if (state.map.hoveredNode !== found) {
    state.map.hoveredNode = found;
    state.map.canvas.style.cursor = found ? 'pointer' : (state.map.isDragging ? 'grabbing' : 'grab');
    renderMap();
    if (found) {
      inspectNode(found);
    }
  }
}

function selectNode(nodeId) {
  const node = state.graph.nodes.find(n => n.node_id === nodeId);
  if (node) {
    state.selectedNode = node;
    inspectNode(node);
    renderMap();
  }
}

function inspectNode(node) {
  const card = document.getElementById('nodeDetailsCard');
  const isDepot = node.node_id === state.depot_node;

  // Find incoming & outgoing edges
  const edges = state.graph.edges.filter(e => e.source === node.node_id || e.target === node.node_id);

  // Find parcels assigned to this node
  const parcels = state.parcels.filter(p => p.destination === node.node_id);
  const selectedParcels = (state.lastResult?.packing_result?.selected_parcels || [])
    .filter(p => p.destination === node.node_id);

  // Check tour stop sequence
  const stops = state.lastResult?.route_result?.ordered_stops || [];
  const stopIndices = [];
  stops.forEach((s, idx) => {
    if (s === node.node_id) stopIndices.push(idx + 1);
  });

  card.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
      <h4 style="font-size: 1.05rem; font-weight: 700;">
        ${node.node_id} ${isDepot ? '<span class="badge badge-warning">CENTRAL DEPOT</span>' : ''}
      </h4>
      <span style="font-family: var(--font-mono); font-size: 0.75rem; color: var(--text-muted);">
        (${node.x.toFixed(1)}, ${node.y.toFixed(1)})
      </span>
    </div>

    <div style="font-size: 0.8rem; margin-bottom: 0.65rem;">
      <strong>Name:</strong> ${node.name || 'Delivery Point'}
    </div>

    ${stopIndices.length > 0 ? `
      <div style="margin-bottom: 0.65rem; font-size: 0.8rem;">
        <strong>Tour Stops:</strong>
        <span class="badge badge-info">${stopIndices.map(i => `Stop #${i}`).join(', ')}</span>
      </div>
    ` : '<div style="margin-bottom: 0.65rem; font-size: 0.8rem; color: var(--text-muted);">Not in active tour sequence</div>'}

    <div style="margin-bottom: 0.75rem;">
      <strong style="font-size: 0.8rem;">Parcels Destined Here (${parcels.length}):</strong>
      ${parcels.length > 0 ? `
        <div style="margin-top: 0.35rem; display: flex; flex-direction: column; gap: 0.35rem;">
          ${parcels.map(p => {
            const packed = selectedParcels.some(sp => sp.parcel_id === p.parcel_id);
            return `
              <div style="padding: 0.35rem 0.5rem; background: var(--bg-tertiary); border-radius: 4px; font-size: 0.75rem; display: flex; justify-content: space-between;">
                <span><strong>${p.parcel_id}</strong> (${p.weight}kg, ${p.value}pts)</span>
                <span class="badge ${packed ? 'badge-success' : 'badge-danger'}">${packed ? 'PACKED' : 'DEFERRED'}</span>
              </div>
            `;
          }).join('')}
        </div>
      ` : '<div style="color: var(--text-muted); font-size: 0.75rem;">None</div>'}
    </div>

    <div>
      <strong style="font-size: 0.8rem;">Road Connections (${edges.length}):</strong>
      <div style="display: flex; flex-wrap: wrap; gap: 0.3rem; margin-top: 0.35rem;">
        ${edges.map(e => {
          const neighbor = e.source === node.node_id ? e.target : e.source;
          return `<span class="stop-tag">${neighbor} (${e.weight} km)</span>`;
        }).join('')}
      </div>
    </div>
  `;
}

function renderMap() {
  const canvas = state.map.canvas;
  if (!canvas) return;
  const ctx = state.map.ctx;
  const container = canvas.parentElement;
  if (!container) return;
  const rect = container.getBoundingClientRect();
  if (rect.width === 0 || rect.height === 0) return;

  ctx.clearRect(0, 0, rect.width, rect.height);

  const isDark = document.body.classList.contains('theme-dark');
  const roadColor = isDark ? '#1e293b' : '#cbd5e1';
  const roadTextColor = isDark ? '#64748b' : '#94a3b8';
  const tourRouteColor = isDark ? '#38bdf8' : '#0284c7';
  const depotColor = '#f59e0b';
  const deliveredColor = '#10b981';
  const unvisitedColor = isDark ? '#475569' : '#94a3b8';

  const nodeMap = new Map();
  (state.graph.nodes || []).forEach(n => nodeMap.set(n.node_id, n));

  // 1. Draw Road Network Edges
  ctx.save();
  ctx.lineWidth = 1.5;
  ctx.strokeStyle = roadColor;

  (state.graph.edges || []).forEach(edge => {
    const u = nodeMap.get(edge.source);
    const v = nodeMap.get(edge.target);
    if (!u || !v) return;

    const p1 = worldToScreen(u.x, u.y);
    const p2 = worldToScreen(v.x, v.y);

    ctx.beginPath();
    ctx.moveTo(p1.x, p1.y);
    ctx.lineTo(p2.x, p2.y);
    ctx.stroke();

    if (state.showDistanceLabels && state.map.zoom > 0.6) {
      const midX = (p1.x + p2.x) / 2;
      const midY = (p1.y + p2.y) / 2;
      ctx.font = '10px JetBrains Mono';
      ctx.fillStyle = roadTextColor;
      ctx.textAlign = 'center';
      ctx.fillText(`${edge.weight}km`, midX, midY - 3);
    }
  });
  ctx.restore();

  // 2. Draw Active TSP Tour Route (Detailed path)
  const detailedPath = state.lastResult?.route_result?.detailed_path || [];
  if (detailedPath.length > 1) {
    ctx.save();
    ctx.lineWidth = 3.5;
    ctx.strokeStyle = tourRouteColor;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.shadowColor = tourRouteColor;
    ctx.shadowBlur = isDark ? 8 : 4;

    ctx.beginPath();
    for (let i = 0; i < detailedPath.length; i++) {
      const n = nodeMap.get(detailedPath[i]);
      if (!n) continue;
      const sp = worldToScreen(n.x, n.y);
      if (i === 0) ctx.moveTo(sp.x, sp.y);
      else ctx.lineTo(sp.x, sp.y);
    }
    ctx.stroke();
    ctx.restore();
  }

  // 3. Draw Nodes
  const orderedStops = state.lastResult?.route_result?.ordered_stops || [];
  const stopIndexMap = new Map();
  orderedStops.forEach((s, idx) => {
    if (!stopIndexMap.has(s)) stopIndexMap.set(s, idx + 1);
  });

  const selectedDestinations = new Set(
    (state.lastResult?.packing_result?.selected_parcels || []).map(p => p.destination)
  );

  (state.graph.nodes || []).forEach(node => {
    const sp = worldToScreen(node.x, node.y);
    const isDepot = node.node_id === state.depot_node;
    const isDelivered = selectedDestinations.has(node.node_id);
    const isHovered = state.map.hoveredNode?.node_id === node.node_id;
    const isSelected = state.selectedNode?.node_id === node.node_id;

    ctx.save();

    // Node Outer Ring / Focus
    if (isHovered || isSelected) {
      ctx.beginPath();
      ctx.arc(sp.x, sp.y, isDepot ? 17 : 14, 0, Math.PI * 2);
      ctx.fillStyle = isDepot ? 'rgba(245, 158, 11, 0.3)' : 'rgba(56, 189, 248, 0.35)';
      ctx.fill();
    }

    // Node Circle Body
    const radius = isDepot ? 11 : (isDelivered ? 8 : 6);
    ctx.beginPath();
    ctx.arc(sp.x, sp.y, radius, 0, Math.PI * 2);

    if (isDepot) {
      ctx.fillStyle = depotColor;
      ctx.strokeStyle = '#ffffff';
    } else if (isDelivered) {
      ctx.fillStyle = deliveredColor;
      ctx.strokeStyle = '#ffffff';
    } else {
      ctx.fillStyle = unvisitedColor;
      ctx.strokeStyle = roadColor;
    }

    ctx.lineWidth = 2;
    ctx.fill();
    ctx.stroke();

    // Node Label
    ctx.font = isDepot ? 'bold 12px Outfit' : '10px Outfit';
    ctx.fillStyle = isDark ? '#f8fafc' : '#0f172a';
    ctx.textAlign = 'center';
    ctx.fillText(node.node_id, sp.x, sp.y + radius + 12);

    // Stop Sequence Badge
    if (stopIndexMap.has(node.node_id) && !isDepot) {
      const stopNum = stopIndexMap.get(node.node_id);
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 8px JetBrains Mono';
      ctx.fillText(stopNum, sp.x, sp.y + 3);
    }

    ctx.restore();
  });

  // 4. Draw Animated Courier Van
  renderCourierVan(ctx);
}

function prepareVanSimulationPath(res) {
  const detailedPath = res?.route_result?.detailed_path || [];
  if (detailedPath.length <= 1) {
    state.sim.pathPoints = [];
    state.sim.totalPathDistance = 0;
    return;
  }

  const nodeMap = new Map();
  state.graph.nodes.forEach(n => nodeMap.set(n.node_id, n));

  const points = [];
  let cum = 0;

  for (let i = 0; i < detailedPath.length; i++) {
    const n = nodeMap.get(detailedPath[i]);
    if (!n) continue;

    if (i > 0) {
      const prev = points[i - 1];
      const dist = Math.hypot(n.x - prev.x, n.y - prev.y);
      cum += dist;
    }

    points.push({
      x: n.x,
      y: n.y,
      node_id: n.node_id,
      cum_dist: cum
    });
  }

  state.sim.pathPoints = points;
  state.sim.totalPathDistance = cum;
  state.sim.progress = 0.0;
  updateSimOdometer();
}

function toggleVanSimulation() {
  if (state.sim.active) {
    pauseVanSimulation();
  } else {
    startVanSimulation();
  }
}

function startVanSimulation() {
  if (state.sim.pathPoints.length <= 1 || state.sim.totalPathDistance <= 0) {
    showToast('No active delivery route to simulate. Ensure at least one delivery stop is packed.', 'warning');
    return;
  }

  if (state.sim.progress >= 1.0) {
    state.sim.progress = 0.0;
  }

  state.sim.active = true;
  document.getElementById('simPlayIcon').textContent = '⏸';
  document.getElementById('simPlayText').textContent = 'Pause Simulation';

  let lastTime = performance.now();

  function animate(now) {
    if (!state.sim.active) return;
    const delta = (now - lastTime) / 1000;
    lastTime = now;

    // Advance progress based on user speed multiplier
    const advanceRate = 0.08 * state.sim.speed;
    state.sim.progress += advanceRate * delta;

    if (state.sim.progress >= 1.0) {
      state.sim.progress = 1.0;
      pauseVanSimulation();
      document.getElementById('simPlayIcon').textContent = '🔄';
      document.getElementById('simPlayText').textContent = 'Restart Simulation';
      showToast('Delivery tour completed! Van returned to Central Depot.', 'success');
    }

    updateSimOdometer();
    if (state.activeTab === 'tab-map') {
      renderMap();
    }

    if (state.sim.active) {
      state.sim.animId = requestAnimationFrame(animate);
    }
  }

  state.sim.animId = requestAnimationFrame(animate);
}

function pauseVanSimulation() {
  state.sim.active = false;
  document.getElementById('simPlayIcon').textContent = '▶';
  document.getElementById('simPlayText').textContent = 'Resume Simulation';
  if (state.sim.animId) {
    cancelAnimationFrame(state.sim.animId);
    state.sim.animId = null;
  }
}

function resetVanSimulation() {
  pauseVanSimulation();
  state.sim.progress = 0.0;
  document.getElementById('simPlayIcon').textContent = '▶';
  document.getElementById('simPlayText').textContent = 'Simulate Route';
  updateSimOdometer();
  renderMap();
}

function updateSimOdometer() {
  const total = state.sim.totalPathDistance;
  const currentDist = (state.sim.progress * total).toFixed(1);
  document.getElementById('simDistanceTraveled').textContent = `${currentDist} km`;

  // Find nearest current waypoint
  const currentTargetDist = state.sim.progress * total;
  let currNode = state.depot_node;
  for (const pt of state.sim.pathPoints) {
    if (pt.cum_dist <= currentTargetDist) {
      currNode = pt.node_id;
    }
  }
  document.getElementById('simCurrentStop').textContent = currNode;
}

function renderCourierVan(ctx) {
  if (state.sim.pathPoints.length <= 1) return;

  const points = state.sim.pathPoints;
  const total = state.sim.totalPathDistance;
  if (total <= 0) return;
  const targetDist = state.sim.progress * total;

  // Interpolate coordinate & heading angle
  let wx = points[0].x;
  let wy = points[0].y;
  let angle = 0;

  for (let i = 0; i < points.length - 1; i++) {
    const p1 = points[i];
    const p2 = points[i + 1];
    if (targetDist >= p1.cum_dist && targetDist <= p2.cum_dist) {
      const segLen = p2.cum_dist - p1.cum_dist;
      const t = segLen > 0 ? (targetDist - p1.cum_dist) / segLen : 0;
      wx = p1.x + (p2.x - p1.x) * t;
      wy = p1.y + (p2.y - p1.y) * t;
      angle = Math.atan2(p2.y - p1.y, p2.x - p1.x);
      break;
    }
  }

  const sp = worldToScreen(wx, wy);

  ctx.save();
  ctx.translate(sp.x, sp.y);
  ctx.rotate(angle);

  // Draw Courier Van Graphic
  ctx.shadowColor = 'rgba(0, 0, 0, 0.45)';
  ctx.shadowBlur = 6;

  // Van Body
  ctx.fillStyle = '#f59e0b';
  ctx.beginPath();
  if (typeof ctx.roundRect === 'function') {
    ctx.roundRect(-14, -8, 28, 16, 4);
  } else {
    ctx.rect(-14, -8, 28, 16);
  }
  ctx.fill();

  // Windshield
  ctx.fillStyle = '#1e293b';
  ctx.fillRect(4, -6, 6, 12);

  // Headlights
  ctx.fillStyle = '#fef08a';
  ctx.fillRect(13, -6, 2, 3);
  ctx.fillRect(13, 3, 2, 3);

  // Delivery Icon on Roof
  ctx.fillStyle = '#ffffff';
  ctx.font = 'bold 8px Outfit';
  ctx.textAlign = 'center';
  ctx.fillText('📦', -3, 3);

  ctx.restore();
}

// ==========================================================================
// Dynamic Programming Matrix Inspector
// ==========================================================================
function renderDpMatrix(dpTable, backtrackPath) {
  const table = document.getElementById('dpGridTable');
  table.innerHTML = '';

  if (!dpTable || dpTable.length === 0) {
    table.innerHTML = '<tr><td>DP Table not available.</td></tr>';
    return;
  }

  const prioritized = state.lastResult.prioritized_parcels || [];
  const rows = dpTable.length;
  const cols = dpTable[0].length;
  const maxCap = cols - 1;

  // Determine Visible Columns Slice
  let startCol = 0;
  let endCol = maxCap;

  if (maxCap <= 120 || state.dpWindowMode === 'all') {
    startCol = 0;
    endCol = maxCap;
  } else if (state.dpWindowMode === 'base') {
    startCol = 0;
    endCol = Math.min(maxCap, 60);
  } else if (state.dpWindowMode === 'optimal' || state.dpWindowMode === 'auto') {
    startCol = Math.max(0, maxCap - 60);
    endCol = maxCap;
  } else if (state.dpWindowMode === 'custom') {
    startCol = Math.max(0, state.dpWindowStart);
    endCol = Math.min(maxCap, state.dpWindowEnd);
  }

  state.dpWindowStart = startCol;
  state.dpWindowEnd = endCol;

  // Render Window Selector Pills
  renderDpWindowSelector(maxCap);

  // Set of backtrack coordinates
  const backtrackSet = new Set(backtrackPath.map(p => `${p.row},${p.col}`));

  // Header Row
  const thead = document.createElement('thead');
  const trHeader = document.createElement('tr');

  const thItem = document.createElement('th');
  thItem.className = 'col-sticky';
  thItem.textContent = 'Parcel Candidate i (w, v)';
  trHeader.appendChild(thItem);

  for (let w = startCol; w <= endCol; w++) {
    const th = document.createElement('th');
    th.textContent = `w=${w}`;
    if (w === maxCap) {
      th.style.color = 'var(--accent-success)';
      th.title = `Vehicle Capacity W = ${maxCap}`;
    }
    trHeader.appendChild(th);
  }
  thead.appendChild(trHeader);
  table.appendChild(thead);

  // Table Body Rows
  const tbody = document.createElement('tbody');

  for (let i = 0; i < rows; i++) {
    const tr = document.createElement('tr');

    // Row Label
    const thRow = document.createElement('th');
    thRow.className = 'col-sticky';
    if (i === 0) {
      thRow.innerHTML = '<em>0 (Base: No Items)</em>';
    } else {
      const p = prioritized[i - 1];
      thRow.innerHTML = `<strong>${p.parcel_id}</strong> (w=${p.weight}, v=${p.value})`;
    }
    tr.appendChild(thRow);

    // Columns
    for (let w = startCol; w <= endCol; w++) {
      const td = document.createElement('td');
      const val = dpTable[i][w];
      td.textContent = val;
      td.setAttribute('data-row', i);
      td.setAttribute('data-col', w);

      const isBacktrack = backtrackSet.has(`${i},${w}`);
      if (isBacktrack) {
        td.className = 'dp-cell-backtrack';
      }

      td.addEventListener('click', () => {
        inspectDpCell(i, w, val, dpTable, prioritized);
        highlightActiveDpCell(td);
      });

      tr.appendChild(td);
    }
    tbody.appendChild(tr);
  }
  table.appendChild(tbody);

  // Render Backtrack Trace Log
  renderBacktrackStepList(backtrackPath);

  // Auto-inspect cell at (rows - 1, endCol)
  inspectDpCell(rows - 1, endCol, dpTable[rows - 1][endCol], dpTable, prioritized);
}

function renderDpWindowSelector(maxCap) {
  const container = document.getElementById('dpWindowSelector');
  if (!container) return;
  container.innerHTML = '';

  if (maxCap <= 120) {
    container.innerHTML = `<span style="font-size:0.75rem; color:var(--text-muted);">Showing All 0..${maxCap} Subproblems</span>`;
    return;
  }

  const modes = [
    { id: 'optimal', label: `Optimal End (${Math.max(0, maxCap - 60)}..${maxCap})` },
    { id: 'base', label: 'Base Case (0..60)' },
    { id: 'all', label: `Full Matrix (All ${maxCap + 1} cols)` }
  ];

  modes.forEach(m => {
    const btn = document.createElement('button');
    btn.className = `dp-window-btn ${state.dpWindowMode === m.id ? 'active' : ''}`;
    btn.textContent = m.label;
    btn.addEventListener('click', () => {
      state.dpWindowMode = m.id;
      if (state.lastResult) {
        renderDpMatrix(state.lastResult.packing_result.dp_table, state.lastResult.packing_result.backtrack_path);
      }
    });
    container.appendChild(btn);
  });
}

function inspectDpCell(i, w, val, dpTable, prioritized) {
  const inspector = document.getElementById('dpCellInspectorContent');

  if (i === 0) {
    inspector.innerHTML = `
      <div style="font-size: 0.85rem;">
        <strong>Base Case:</strong> DP[0][${w}] = 0
      </div>
      <p style="font-size: 0.775rem; color: var(--text-muted); margin-top: 0.35rem;">
        With zero parcel items considered, the maximum obtainable value is identically zero across all sub-capacities.
      </p>
    `;
    return;
  }

  const p = prioritized[i - 1];
  const w_i = p.weight;
  const v_i = p.value;
  const excludeVal = dpTable[i - 1][w];

  let includeFormula = '';
  let decision = '';

  if (w_i <= w) {
    const includeVal = dpTable[i - 1][w - w_i] + v_i;
    includeFormula = `Include: DP[${i-1}][${w} - ${w_i}] + ${v_i} = ${dpTable[i-1][w-w_i]} + ${v_i} = <strong>${includeVal}</strong>`;
    if (includeVal > excludeVal) {
      decision = `<span class="badge badge-success">INCLUDED</span> Parcel ${p.parcel_id} was chosen because including it yields higher value (${includeVal} > ${excludeVal}).`;
    } else {
      decision = `<span class="badge badge-neutral">EXCLUDED</span> Excluding Parcel ${p.parcel_id} yields equal or better value (${excludeVal} >= ${includeVal}).`;
    }
  } else {
    includeFormula = `Include: <em>Infeasible</em> (Item weight ${w_i} kg exceeds subproblem capacity ${w} kg).`;
    decision = `<span class="badge badge-danger">EXCLUDED</span> Item weight exceeds current subproblem limit.`;
  }

  inspector.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
      <h5 style="font-size: 0.9rem;">State DP[i=${i}][w=${w}] = <span class="highlight-val">${val}</span></h5>
      <span class="badge badge-info">${p.parcel_id}</span>
    </div>

    <div style="font-size: 0.8rem; margin-bottom: 0.5rem;">
      <strong>Item Candidate:</strong> ${p.parcel_id} | Weight: <strong>${w_i} kg</strong> | Value: <strong>${v_i} pts</strong>
    </div>

    <div class="formula-box">
      <div>Exclude: DP[${i-1}][${w}] = <strong>${excludeVal}</strong></div>
      <div>${includeFormula}</div>
      <div style="margin-top: 0.35rem; padding-top: 0.35rem; border-top: 1px dashed var(--border-color);">
        Recurrence: max(Exclude, Include) = <strong>${val}</strong>
      </div>
    </div>

    <div style="margin-top: 0.75rem; font-size: 0.775rem;">
      ${decision}
    </div>
  `;
}

function highlightActiveDpCell(td) {
  document.querySelectorAll('.dp-cell-active-inspect').forEach(c => c.classList.remove('dp-cell-active-inspect'));
  td.classList.add('dp-cell-active-inspect');
}

function renderBacktrackStepList(steps) {
  const list = document.getElementById('backtrackStepList');
  list.innerHTML = '';

  steps.forEach(step => {
    const item = document.createElement('div');
    item.className = step.picked ? 'backtrack-step-item picked' : 'backtrack-step-item';
    item.style.cursor = 'pointer';
    item.title = `Click to jump to cell DP[${step.row}][${step.col}]`;

    if (step.row === 0) {
      item.innerHTML = `
        <span><strong>DP[0][${step.col}]</strong> Base Case reached</span>
        <span class="badge badge-neutral">TERMINATE</span>
      `;
    } else {
      item.innerHTML = `
        <div>
          <strong>DP[${step.row}][${step.col}]</strong> → Parcel <strong>${step.parcel_id}</strong>
          <span style="font-size: 0.7rem; color: var(--text-muted); display: block;">(${step.weight}kg, ${step.value}pts)</span>
        </div>
        <span class="badge ${step.picked ? 'badge-success' : 'badge-neutral'}">
          ${step.picked ? '+ PICKED' : 'SKIPPED'}
        </span>
      `;
    }

    item.addEventListener('click', () => {
      jumpToDpCell(step.row, step.col);
    });

    list.appendChild(item);
  });
}

function jumpToDpCell(row, col) {
  if (!state.lastResult) return;
  const dpTable = state.lastResult.packing_result.dp_table;
  const prioritized = state.lastResult.prioritized_parcels || [];
  const maxCap = dpTable[0].length - 1;

  // If target column is outside the current window, shift the window to include it
  if (col < state.dpWindowStart || col > state.dpWindowEnd) {
    if (col === 0) {
      state.dpWindowMode = 'base';
    } else if (col === maxCap) {
      state.dpWindowMode = 'optimal';
    } else {
      state.dpWindowMode = 'custom';
      state.dpWindowStart = Math.max(0, col - 30);
      state.dpWindowEnd = Math.min(maxCap, col + 30);
    }
    renderDpMatrix(dpTable, state.lastResult.packing_result.backtrack_path);
  }

  // Query cell with row and col data attributes
  const cell = document.querySelector(`#dpGridTable td[data-row="${row}"][data-col="${col}"]`);
  if (cell) {
    cell.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
    highlightActiveDpCell(cell);
    inspectDpCell(row, col, dpTable[row][col], dpTable, prioritized);
  }
}

// ==========================================================================
// Parcel Pool Manager
// ==========================================================================
function renderParcelPoolTable() {
  const tbody = document.getElementById('parcelPoolBody');
  tbody.innerHTML = '';
  document.getElementById('poolCountBadge').textContent = state.parcels.length;

  state.parcels.forEach((p, idx) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${idx + 1}</td>
      <td><strong>${p.parcel_id}</strong></td>
      <td><span class="badge badge-neutral">${p.destination}</span></td>
      <td>${p.weight} kg</td>
      <td>${'★'.repeat(p.priority)}</td>
      <td>${p.deadline.toFixed(1)}h</td>
      <td>${p.value}</td>
      <td>${p.customer_name || '—'}</td>
      <td>
        <button class="btn btn-sm btn-danger delete-parcel-btn" data-id="${p.parcel_id}">Delete</button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  document.querySelectorAll('.delete-parcel-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const pid = e.target.getAttribute('data-id');
      state.parcels = state.parcels.filter(p => p.parcel_id !== pid);
      state.dataset = 'custom';
      document.getElementById('datasetSelect').value = 'custom';
      renderParcelPoolTable();
      runOptimization();
      showToast(`Removed parcel ${pid}`, 'info');
    });
  });
}

function handleAddParcelForm() {
  const id = document.getElementById('formParcelId').value.trim();
  const dest = document.getElementById('formDestination').value;
  const weight = parseInt(document.getElementById('formWeight').value, 10);
  const priority = parseInt(document.getElementById('formPriority').value, 10);
  const deadline = parseFloat(document.getElementById('formDeadline').value);
  const value = parseInt(document.getElementById('formValue').value, 10);
  const customer = document.getElementById('formCustomerName').value.trim();

  // Check unique ID
  if (state.parcels.some(p => p.parcel_id === id)) {
    showToast(`Parcel ID '${id}' already exists. Please choose a unique identifier.`, 'warning');
    return;
  }

  const newParcel = {
    parcel_id: id,
    destination: dest,
    weight: weight,
    priority: priority,
    deadline: deadline,
    value: value > 0 ? value : Math.max(1, priority * 15 + Math.max(0, Math.round((12 - Math.min(deadline, 12)) * 2))),
    customer_name: customer,
  };

  state.parcels.push(newParcel);
  state.dataset = 'custom';
  document.getElementById('datasetSelect').value = 'custom';

  renderParcelPoolTable();
  runOptimization();
  showToast(`Added parcel ${id} destined for ${dest}`, 'success');

  // Suggest next ID
  document.getElementById('formParcelId').value = `P${Math.floor(100 + Math.random() * 900)}`;
}

function generateRandomParcels(count = 5) {
  const nodes = (state.graph.nodes || []).filter(n => n.node_id !== state.depot_node);
  if (nodes.length === 0) {
    showToast('Cannot generate parcels: no delivery locations in graph.', 'warning');
    return;
  }

  for (let i = 0; i < count; i++) {
    const randNode = nodes[Math.floor(Math.random() * nodes.length)];
    const id = `P${Math.floor(100 + Math.random() * 900)}`;
    const weight = Math.floor(2 + Math.random() * 15);
    const priority = Math.floor(1 + Math.random() * 5);
    const deadline = parseFloat((1.0 + Math.random() * 10.0).toFixed(1));
    const value = priority * 16 + Math.floor((12 - Math.min(deadline, 12)) * 2);

    state.parcels.push({
      parcel_id: id,
      destination: randNode.node_id,
      weight: weight,
      priority: priority,
      deadline: deadline,
      value: Math.max(10, value),
      customer_name: `Express Client ${id}`,
    });
  }

  state.dataset = 'custom';
  document.getElementById('datasetSelect').value = 'custom';
  renderParcelPoolTable();
  runOptimization();
  showToast(`Generated ${count} random parcels in active pool!`, 'success');
}

function populateDepotAndDestDropdowns() {
  const nodes = state.graph.nodes || [];
  const depotSelect = document.getElementById('depotSelect');
  const destSelect = document.getElementById('formDestination');

  depotSelect.innerHTML = '';
  destSelect.innerHTML = '';

  nodes.forEach(n => {
    const isDepot = n.is_depot || n.node_id === 'Depot';

    const optDepot = document.createElement('option');
    optDepot.value = n.node_id;
    optDepot.textContent = `${n.node_id} ${isDepot ? '(Default Depot)' : ''}`;
    if (isDepot) optDepot.selected = true;
    depotSelect.appendChild(optDepot);

    if (!isDepot) {
      const optDest = document.createElement('option');
      optDest.value = n.node_id;
      optDest.textContent = `${n.node_id} - ${n.name || 'Location'}`;
      destSelect.appendChild(optDest);
    }
  });

  document.getElementById('formParcelId').value = `P${101 + state.parcels.length}`;
}

// ==========================================================================
// Custom Data Import (CSV / JSON)
// ==========================================================================
function importParcelsFromCsv(text) {
  const lines = text.trim().split(/\r?\n/);
  if (lines.length < 2) {
    showToast('CSV must have a header and at least one data row.', 'error');
    return;
  }

  const header = lines[0].split(',').map(h => h.trim().replace(/^["']|["']$/g, '').toLowerCase());
  const idIdx = header.indexOf('parcel_id');
  const destIdx = header.indexOf('destination');
  const weightIdx = header.indexOf('weight');
  const priorityIdx = header.indexOf('priority');
  const deadlineIdx = header.indexOf('deadline');
  const valIdx = header.indexOf('value');
  const custIdx = header.indexOf('customer_name');

  if (idIdx === -1 || destIdx === -1 || weightIdx === -1) {
    showToast('CSV missing required columns: parcel_id, destination, weight', 'error', 6000);
    return;
  }

  const validNodes = new Set((state.graph.nodes || []).map(n => n.node_id));
  const newParcels = [];
  const unknownDests = new Set();

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;

    const row = [];
    let inQuotes = false;
    let curr = '';
    for (let c = 0; c < line.length; c++) {
      const ch = line[c];
      if (ch === '"') inQuotes = !inQuotes;
      else if (ch === ',' && !inQuotes) {
        row.push(curr.trim().replace(/^["']|["']$/g, ''));
        curr = '';
      } else {
        curr += ch;
      }
    }
    row.push(curr.trim().replace(/^["']|["']$/g, ''));

    const pid = row[idIdx] || `P${i}`;
    const dest = row[destIdx] || 'C1';
    const weight = parseInt(row[weightIdx], 10) || 1;
    const priority = priorityIdx !== -1 ? (parseInt(row[priorityIdx], 10) || 1) : 1;
    const deadline = deadlineIdx !== -1 ? (parseFloat(row[deadlineIdx]) || 24.0) : 24.0;
    const rawVal = valIdx !== -1 ? parseInt(row[valIdx], 10) : 0;
    const cust = custIdx !== -1 ? (row[custIdx] || '') : '';

    if (!validNodes.has(dest) && validNodes.size > 0) {
      unknownDests.add(dest);
    }

    newParcels.push({
      parcel_id: pid,
      destination: dest,
      weight: Math.max(1, weight),
      priority: Math.max(1, Math.min(5, priority)),
      deadline: Math.max(0.5, deadline),
      value: rawVal > 0 ? rawVal : Math.max(1, priority * 15 + Math.round((12 - Math.min(deadline, 12)) * 2)),
      customer_name: cust,
    });
  }

  if (newParcels.length === 0) {
    showToast('No valid parcels extracted from CSV.', 'error');
    return;
  }

  if (unknownDests.size > 0) {
    showToast(`Warning: Destination nodes not found in road network: ${Array.from(unknownDests).join(', ')}.`, 'warning', 6000);
  }

  state.parcels = newParcels;
  state.dataset = 'custom';
  document.getElementById('datasetSelect').value = 'custom';
  renderParcelPoolTable();
  runOptimization();
  showToast(`Successfully imported ${newParcels.length} custom parcels!`, 'success');
}

function importGraphFromJson(jsonText) {
  try {
    const data = JSON.parse(jsonText);
    if (!data.nodes || !Array.isArray(data.nodes) || !data.edges || !Array.isArray(data.edges)) {
      throw new Error('Graph JSON must contain "nodes" and "edges" arrays.');
    }

    state.graph = {
      directed: Boolean(data.directed),
      nodes: data.nodes.map(n => ({
        node_id: String(n.node_id),
        name: String(n.name || n.node_id),
        x: parseFloat(n.x) || 0.0,
        y: parseFloat(n.y) || 0.0,
        is_depot: Boolean(n.is_depot)
      })),
      edges: data.edges.map(e => ({
        source: String(e.source),
        target: String(e.target),
        weight: parseFloat(e.weight) || 1.0
      }))
    };

    state.dataset = 'custom';
    document.getElementById('datasetSelect').value = 'custom';
    state.map.hasFitted = false;
    state.map.needsFit = true;

    populateDepotAndDestDropdowns();
    if (state.activeTab === 'tab-map') {
      resizeCanvas();
      fitMapToScreen();
      renderMap();
    }

    runOptimization();
    showToast(`Imported road network (${state.graph.nodes.length} nodes, ${state.graph.edges.length} edges)!`, 'success');
  } catch (err) {
    showToast(`Graph import failed: ${err.message}`, 'error', 6000);
  }
}

// ==========================================================================
// Benchmarks View
// ==========================================================================
function updateBenchmarkView(benchmarks) {
  if (!benchmarks) return;

  // Knapsack
  const k = benchmarks.knapsack;
  document.getElementById('benchDpValue').textContent = `${k.dp_value} pts`;
  document.getElementById('benchDpWeight').textContent = `Weight: ${k.dp_weight} kg`;
  document.getElementById('benchGreedyValue').textContent = `${k.greedy_value} pts`;
  document.getElementById('benchGreedyWeight').textContent = `Weight: ${k.greedy_weight} kg`;

  const optGap = k.optimality_gap_percent;
  document.getElementById('benchOptimalityGap').textContent = optGap > 0
    ? `+${optGap.toFixed(1)}% Higher Objective Value with DP`
    : `Both algorithms converged to identical optimal value`;

  // TSP
  const t = benchmarks.tsp;
  document.getElementById('benchRawDistance').textContent = `${t.raw_distance.toFixed(2)} km`;
  document.getElementById('benchOptDistance').textContent = `${t.optimized_distance.toFixed(2)} km`;
  document.getElementById('benchDistanceSaved').textContent = `${t.distance_saved_km.toFixed(2)} km (${t.reduction_percent.toFixed(1)}% reduction)`;
}

// ==========================================================================
// Export Utilities (JSON, CSV, Vector SVG)
// ==========================================================================
function downloadJsonManifest() {
  if (!state.lastResult) return;
  const blob = new Blob([JSON.stringify(state.lastResult, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `courier_dispatch_manifest_${state.dataset}.json`;
  a.click();
  URL.revokeObjectURL(url);
  showToast('Manifest JSON downloaded!', 'success');
}

function downloadCsvManifest() {
  if (!state.lastResult) return;
  const pack = state.lastResult.packing_result;
  const selectedIds = new Set(pack.selected_parcels.map(p => p.parcel_id));

  let csv = 'parcel_id,destination,weight,priority,deadline,value,customer_name,status\n';
  state.parcels.forEach(p => {
    const isSelected = selectedIds.has(p.parcel_id);
    const cleanCustomer = (p.customer_name || '').replace(/"/g, '""');
    csv += `"${p.parcel_id}","${p.destination}",${p.weight},${p.priority},${p.deadline},${p.value},"${cleanCustomer}","${isSelected ? 'PACKED' : 'DEFERRED'}"\n`;
  });

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `courier_manifest_${state.dataset}.csv`;
  a.click();
  URL.revokeObjectURL(url);
  showToast('Manifest CSV downloaded!', 'success');
}

function downloadItineraryCsv() {
  if (!state.lastResult || !state.lastResult.route_result.itinerary) {
    showToast('No active itinerary to export.', 'warning');
    return;
  }
  const itinerary = state.lastResult.route_result.itinerary;

  let csv = 'stop_number,node_id,location_name,is_depot,leg_distance_km,cumulative_distance_km,eta_minutes,parcels_dropped_count,parcels_dropped_ids\n';
  itinerary.forEach((step, idx) => {
    const cleanName = (step.node_name || '').replace(/"/g, '""');
    const droppedIds = (step.parcels_dropped || []).map(p => p.parcel_id).join(';');
    csv += `${idx + 1},"${step.node_id}","${cleanName}",${step.is_depot},${step.leg_distance_km},${step.cumulative_distance_km},${step.eta_minutes},${step.parcels_count},"${droppedIds}"\n`;
  });

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `delivery_itinerary_${state.dataset}.csv`;
  a.click();
  URL.revokeObjectURL(url);
  showToast('Turn-by-turn delivery itinerary CSV downloaded!', 'success');
}

function exportMapSvg() {
  const nodes = state.graph.nodes || [];
  if (nodes.length === 0) {
    showToast('No road network to export.', 'warning');
    return;
  }

  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  nodes.forEach(n => {
    if (n.x < minX) minX = n.x;
    if (n.x > maxX) maxX = n.x;
    if (n.y < minY) minY = n.y;
    if (n.y > maxY) maxY = n.y;
  });

  const padding = 50;
  const w = (maxX - minX) || 100;
  const h = (maxY - minY) || 100;
  const viewBox = `${minX - padding} ${minY - padding} ${w + padding * 2} ${h + padding * 2}`;

  const nodeMap = new Map();
  nodes.forEach(n => nodeMap.set(n.node_id, n));

  const orderedStops = state.lastResult?.route_result?.ordered_stops || [];
  const stopIndexMap = new Map();
  orderedStops.forEach((s, idx) => {
    if (!stopIndexMap.has(s)) stopIndexMap.set(s, idx + 1);
  });
  const selectedDests = new Set(
    (state.lastResult?.packing_result?.selected_parcels || []).map(p => p.destination)
  );

  let edgesSvg = '';
  (state.graph.edges || []).forEach(e => {
    const u = nodeMap.get(e.source);
    const v = nodeMap.get(e.target);
    if (!u || !v) return;
    edgesSvg += `<line x1="${u.x}" y1="${u.y}" x2="${v.x}" y2="${v.y}" stroke="#94a3b8" stroke-width="1.2" opacity="0.7" />\n`;
    const midX = (u.x + v.x) / 2;
    const midY = (u.y + v.y) / 2;
    edgesSvg += `<text x="${midX}" y="${midY - 2}" font-family="monospace" font-size="3" fill="#64748b" text-anchor="middle">${e.weight}km</text>\n`;
  });

  let routeSvg = '';
  const detailedPath = state.lastResult?.route_result?.detailed_path || [];
  if (detailedPath.length > 1) {
    const pointsStr = detailedPath.map(id => {
      const n = nodeMap.get(id);
      return n ? `${n.x},${n.y}` : '';
    }).filter(Boolean).join(' ');
    routeSvg = `<polyline points="${pointsStr}" fill="none" stroke="#0284c7" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />\n`;
  }

  let nodesSvg = '';
  nodes.forEach(n => {
    const isDepot = n.node_id === state.depot_node;
    const isDelivered = selectedDests.has(n.node_id);
    const fill = isDepot ? '#f59e0b' : (isDelivered ? '#10b981' : '#64748b');
    const radius = isDepot ? 6 : (isDelivered ? 4.5 : 3.5);

    nodesSvg += `<circle cx="${n.x}" cy="${n.y}" r="${radius}" fill="${fill}" stroke="#ffffff" stroke-width="1.2" />\n`;
    nodesSvg += `<text x="${n.x}" y="${n.y + radius + 4}" font-family="sans-serif" font-size="3.5" font-weight="bold" fill="#0f172a" text-anchor="middle">${n.node_id}</text>\n`;
    if (stopIndexMap.has(n.node_id) && !isDepot) {
      const stopNum = stopIndexMap.get(n.node_id);
      nodesSvg += `<text x="${n.x}" y="${n.y + 1.2}" font-family="monospace" font-size="2.6" font-weight="bold" fill="#ffffff" text-anchor="middle">${stopNum}</text>\n`;
    }
  });

  const svgContent = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="${viewBox}" width="1000" height="700">
  <rect x="${minX - padding}" y="${minY - padding}" width="${w + padding * 2}" height="${h + padding * 2}" fill="#ffffff" />
  <g id="road_edges">${edgesSvg}</g>
  <g id="tsp_route">${routeSvg}</g>
  <g id="network_nodes">${nodesSvg}</g>
  <text x="${minX - padding + 10}" y="${minY - padding + 15}" font-family="sans-serif" font-size="6" font-weight="bold" fill="#0f172a">Mini-Courier Planner - ${state.dataset.toUpperCase()} Delivery Route</text>
  <text x="${minX - padding + 10}" y="${minY - padding + 23}" font-family="sans-serif" font-size="4" fill="#64748b">Route Distance: ${state.lastResult?.route_result?.total_distance || 0} km | Vehicle Capacity: ${state.vehicle_capacity} kg | Packed: ${state.lastResult?.packing_result?.selected_parcels?.length || 0} parcels</text>
</svg>`;

  const blob = new Blob([svgContent], { type: 'image/svg+xml;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `courier_route_map_${state.dataset}.svg`;
  a.click();
  URL.revokeObjectURL(url);
  showToast('Vector route map SVG exported successfully!', 'success');
}
