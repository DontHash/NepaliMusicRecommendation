import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const EMOTIONS = ['joy', 'sadness', 'anger'];
const COLORS = { joy: 0x22c55e, sadness: 0x3b82f6, anger: 0xef4444, neutral: 0x64748b };
const CSS_COLORS = { joy: '#22c55e', sadness: '#3b82f6', anger: '#ef4444', neutral: '#64748b' };

const $ = (id) => document.getElementById(id);
const canvas = $('scene');
const tooltip = $('tooltip');
const resultsBox = $('results');
const searchInput = $('search');
const loading = $('loading');
const loadingText = $('loading-text');

let state = {
  payload: null,
  hovered: null,
  selected: null,
  lineHover: null,
  segments: [],
  spawnDone: false,
};

// ---------- Three.js scene ----------
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x05070f, 0.035);

const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
camera.position.set(0, 5.4, 7.8);

const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.enablePan = false;
controls.minDistance = 5.5;
controls.maxDistance = 15;
controls.minPolarAngle = 0.25;
controls.maxPolarAngle = Math.PI / 2.05;
controls.autoRotate = true;
controls.autoRotateSpeed = 0.7;
controls.target.set(0, 0.2, 0);

const ambient = new THREE.AmbientLight(0x8899bb, 0.75);
scene.add(ambient);
const key = new THREE.PointLight(0x8fb4ff, 90, 40);
key.position.set(6, 9, 6);
scene.add(key);
const rim = new THREE.PointLight(0x5b6bff, 45, 40);
rim.position.set(-7, 4, -6);
scene.add(rim);

const donutGroup = new THREE.Group();
scene.add(donutGroup);

// ambient particle field
const particleCount = 420;
const particlePositions = new Float32Array(particleCount * 3);
for (let i = 0; i < particleCount; i += 1) {
  const radius = 8 + Math.random() * 14;
  const theta = Math.random() * Math.PI * 2;
  const phi = Math.acos(2 * Math.random() - 1);
  particlePositions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
  particlePositions[i * 3 + 1] = (Math.random() - 0.3) * 10;
  particlePositions[i * 3 + 2] = radius * Math.sin(phi) * Math.sin(theta);
}
const particleGeometry = new THREE.BufferGeometry();
particleGeometry.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));
const particles = new THREE.Points(
  particleGeometry,
  new THREE.PointsMaterial({ color: 0x93a5d8, size: 0.05, transparent: true, opacity: 0.55, depthWrite: false })
);
scene.add(particles);

// ---------- donut geometry ----------
const INNER = 1.75;
const OUTER = 3.05;
const DEPTH = 0.72;
const GAP = 0.045;

function annularSector(inner, outer, a0, a1, depth) {
  const shape = new THREE.Shape();
  shape.moveTo(Math.cos(a0) * outer, Math.sin(a0) * outer);
  shape.absarc(0, 0, outer, a0, a1, false);
  shape.lineTo(Math.cos(a1) * inner, Math.sin(a1) * inner);
  shape.absarc(0, 0, inner, a1, a0, true);
  shape.closePath();
  return new THREE.ExtrudeGeometry(shape, {
    depth,
    curveSegments: 72,
    bevelEnabled: true,
    bevelThickness: 0.05,
    bevelSize: 0.05,
    bevelSegments: 3,
  });
}

function disposeDonut() {
  for (const segment of state.segments) {
    donutGroup.remove(segment);
    segment.geometry.dispose();
    segment.material.dispose();
  }
  state.segments = [];
}

function buildDonut(composition) {
  disposeDonut();
  let angle = Math.PI / 2;
  const now = performance.now();
  EMOTIONS.forEach((emotion, index) => {
    const share = composition[emotion] || 0;
    const sweep = share * Math.PI * 2;
    if (sweep < 0.015) {
      angle += sweep;
      return;
    }
    const geometry = annularSector(INNER, OUTER, angle + GAP / 2, angle + sweep - GAP / 2, DEPTH);
    const material = new THREE.MeshStandardMaterial({
      color: COLORS[emotion],
      emissive: COLORS[emotion],
      emissiveIntensity: 0.24,
      metalness: 0.35,
      roughness: 0.42,
      transparent: true,
      opacity: 1,
    });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.rotation.x = -Math.PI / 2;
    mesh.position.y = -DEPTH / 2;
    mesh.scale.z = 0.02;
    mesh.userData = {
      emotion,
      share,
      spawnAt: now + index * 130,
      hoverScale: 1,
    };
    donutGroup.add(mesh);
    state.segments.push(mesh);
    angle += sweep;
  });
  state.spawnDone = true;
}

// ---------- interactions ----------
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
let pointerDownAt = null;

function setPointer(event) {
  const rect = canvas.getBoundingClientRect();
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
}

canvas.addEventListener('pointermove', (event) => {
  setPointer(event);
  raycaster.setFromCamera(pointer, camera);
  const hits = raycaster.intersectObjects(state.segments, false);
  const hovered = hits.length ? hits[0].object.userData.emotion : null;
  state.hovered = hovered;
  if (hovered && !state.lineHover) {
    const segment = hits[0].object;
    const count = segmentCountLines(hovered);
    showTooltip(
      event,
      `<b style="color:${CSS_COLORS[hovered]}">${hovered}</b> — ${(segment.userData.share * 100).toFixed(1)}%<br>
       <span class="prob">${count} lyric line${count === 1 ? '' : 's'}</span>`
    );
    canvas.style.cursor = 'pointer';
  } else if (!state.lineHover) {
    hideTooltip();
    canvas.style.cursor = '';
  }
});

canvas.addEventListener('pointerdown', (event) => {
  pointerDownAt = { x: event.clientX, y: event.clientY };
});

canvas.addEventListener('pointerup', (event) => {
  if (!pointerDownAt) return;
  const moved = Math.hypot(event.clientX - pointerDownAt.x, event.clientY - pointerDownAt.y);
  pointerDownAt = null;
  if (moved > 6) return;
  setPointer(event);
  raycaster.setFromCamera(pointer, camera);
  const hits = raycaster.intersectObjects(state.segments, false);
  if (hits.length) {
    selectEmotion(hits[0].object.userData.emotion === state.selected ? null : hits[0].object.userData.emotion);
  } else {
    selectEmotion(null);
  }
});

canvas.addEventListener('pointerleave', () => {
  state.hovered = null;
  hideTooltip();
});

function segmentCountLines(emotion) {
  if (!state.payload) return 0;
  return state.payload.lines.filter((line) => line.dominant === emotion).length;
}

function showTooltip(event, html) {
  tooltip.innerHTML = html;
  tooltip.classList.remove('hidden');
  tooltip.style.left = `${event.clientX}px`;
  tooltip.style.top = `${event.clientY}px`;
}

function hideTooltip() {
  tooltip.classList.add('hidden');
}

function selectEmotion(emotion) {
  state.selected = emotion;
  const clearButton = $('clear-selection');
  clearButton.classList.toggle('hidden', !emotion);
  document.querySelectorAll('.legend-chip').forEach((chip) => {
    chip.classList.toggle('active', chip.dataset.emotion === emotion);
  });
  document.querySelectorAll('#lyrics .line').forEach((line) => {
    if (!emotion) {
      line.classList.remove('dimmed', 'active');
    } else if (line.dataset.emotion === emotion) {
      line.classList.add('active');
      line.classList.remove('dimmed');
    } else {
      line.classList.remove('active');
      line.classList.add('dimmed');
    }
  });
  if (emotion) {
    const first = document.querySelector(`#lyrics .line[data-emotion="${emotion}"]`);
    if (first) first.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
}

$('clear-selection').addEventListener('click', () => selectEmotion(null));
window.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') {
    selectEmotion(null);
    resultsBox.classList.add('hidden');
    $('paste-modal').classList.add('hidden');
  }
  if (event.key.toLowerCase() === 'r' && !event.target.matches('input, textarea')) {
    camera.position.set(0, 5.4, 7.8);
    controls.target.set(0, 0.2, 0);
  }
});

// ---------- rendering payload ----------
function renderPayload(payload) {
  state.payload = payload;
  state.selected = null;

  $('song-title').textContent = payload.title || 'Pasted lyrics';
  $('song-artist').textContent = payload.artist || (payload.source === 'text' ? 'ad-hoc analysis' : '');
  $('lyrics-title').textContent = payload.title || 'Lyrics';
  $('mood-phrase').textContent = payload.mood_phrase || '';

  const chip = $('confidence');
  if (payload.confidence) {
    chip.textContent = `confidence: ${payload.confidence}`;
    chip.classList.remove('hidden');
  } else {
    chip.classList.add('hidden');
  }

  buildDonut(payload.composition);
  renderLegend(payload);
  renderPolarity(payload.polarity);
  renderLyrics(payload.lines);
  selectEmotion(null);
}

function renderLegend(payload) {
  const legend = $('legend');
  legend.innerHTML = '';
  for (const emotion of EMOTIONS) {
    const share = payload.composition[emotion] || 0;
    const count = payload.lines.filter((line) => line.dominant === emotion).length;
    const chip = document.createElement('button');
    chip.className = 'legend-chip';
    chip.dataset.emotion = emotion;
    chip.innerHTML = `<span class="dot" style="background:${CSS_COLORS[emotion]}"></span>
      <span>${emotion}</span><span class="pct">${(share * 100).toFixed(0)}% · ${count} lines</span>`;
    chip.addEventListener('click', () =>
      selectEmotion(state.selected === emotion ? null : emotion)
    );
    legend.appendChild(chip);
  }
}

function renderPolarity(polarity) {
  const box = $('polarity');
  if (!polarity) {
    box.classList.add('hidden');
    return;
  }
  box.classList.remove('hidden');
  const score = Math.max(-1, Math.min(1, polarity.score ?? 0));
  $('polarity-marker').style.left = `${((score + 1) / 2) * 100}%`;
  $('polarity-label').textContent = `${polarity.label} (${score >= 0 ? '+' : ''}${score.toFixed(2)})`;
}

function renderLyrics(lines) {
  const container = $('lyrics');
  container.innerHTML = '';
  lines.forEach((line) => {
    const div = document.createElement('div');
    const color = CSS_COLORS[line.dominant] || CSS_COLORS.neutral;
    div.className = 'line';
    div.dataset.emotion = line.dominant;
    div.style.setProperty('--c', color);
    div.textContent = line.text;
    div.addEventListener('mouseenter', (event) => {
      state.lineHover = line.dominant !== 'neutral' ? line.dominant : null;
      const probs = Object.entries(line.probs)
        .map(([name, value]) => `${name} ${(value * 100).toFixed(0)}%`)
        .join(' · ');
      showTooltip(event, `<b style="color:${color}">${line.dominant}</b><br><span class="prob">${probs}</span>`);
    });
    div.addEventListener('mousemove', (event) => {
      tooltip.style.left = `${event.clientX}px`;
      tooltip.style.top = `${event.clientY}px`;
    });
    div.addEventListener('mouseleave', () => {
      state.lineHover = null;
      hideTooltip();
    });
    container.appendChild(div);
  });
}

// ---------- data loading ----------
async function loadSong(songId) {
  loading.classList.remove('hidden');
  loadingText.textContent = 'Analyzing song…';
  try {
    const response = await fetch(`/api/song/${songId}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    renderPayload(await response.json());
  } catch (error) {
    $('song-title').textContent = 'Could not load song';
    $('song-artist').textContent = String(error);
  } finally {
    loading.classList.add('hidden');
  }
}

let searchTimer = null;
searchInput.addEventListener('input', () => {
  clearTimeout(searchTimer);
  const query = searchInput.value.trim();
  if (query.length < 2) {
    resultsBox.classList.add('hidden');
    return;
  }
  searchTimer = setTimeout(async () => {
    try {
      const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
      const data = await response.json();
      resultsBox.innerHTML = '';
      for (const item of data.results) {
        const row = document.createElement('div');
        row.className = 'result';
        row.innerHTML = `<span>${item.title}</span><span class="artist">${item.artist}</span>`;
        row.addEventListener('click', () => {
          resultsBox.classList.add('hidden');
          searchInput.value = item.title;
          loadSong(item.song_id);
        });
        resultsBox.appendChild(row);
      }
      resultsBox.classList.toggle('hidden', data.results.length === 0);
    } catch {
      resultsBox.classList.add('hidden');
    }
  }, 180);
});

document.addEventListener('click', (event) => {
  if (!event.target.closest('.search-wrap')) resultsBox.classList.add('hidden');
});

$('paste-toggle').addEventListener('click', () => $('paste-modal').classList.remove('hidden'));
$('paste-cancel').addEventListener('click', () => $('paste-modal').classList.add('hidden'));
$('paste-run').addEventListener('click', async () => {
  const text = $('paste-text').value.trim();
  if (!text) return;
  $('paste-modal').classList.add('hidden');
  loading.classList.remove('hidden');
  loadingText.textContent = 'Analyzing lyrics…';
  try {
    const response = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, transliterate: true }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    renderPayload(await response.json());
  } catch (error) {
    $('song-title').textContent = 'Analysis failed';
    $('song-artist').textContent = String(error);
  } finally {
    loading.classList.add('hidden');
  }
});

// ---------- animation loop ----------
const clock = new THREE.Clock();

function easeOutCubic(t) {
  return 1 - Math.pow(1 - t, 3);
}

function animate() {
  requestAnimationFrame(animate);
  const dt = Math.min(clock.getDelta(), 0.05);
  const now = performance.now();

  for (const segment of state.segments) {
    const { emotion, spawnAt } = segment.userData;
    const growth = Math.max(0, Math.min(1, (now - spawnAt) / 750));
    const isHovered = state.hovered === emotion || state.lineHover === emotion;
    const isSelected = state.selected === emotion;
    const target = isHovered ? 1.5 : isSelected ? 1.3 : 1.0;
    segment.userData.hoverScale +=
      (target - segment.userData.hoverScale) * Math.min(1, dt * 9);
    segment.scale.z = Math.max(0.02, easeOutCubic(growth) * segment.userData.hoverScale);

    const dim = state.selected && !isSelected ? 0.16 : 1;
    segment.material.opacity += (dim - segment.material.opacity) * Math.min(1, dt * 8);
    const glow = isHovered ? 0.66 : isSelected ? 0.48 : 0.24 + Math.sin(now * 0.0016 + emotion.length) * 0.05;
    segment.material.emissiveIntensity += (glow - segment.material.emissiveIntensity) * Math.min(1, dt * 8);
  }

  particles.rotation.y += dt * 0.012;
  controls.update();
  renderer.render(scene, camera);
}

function resize() {
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  if (canvas.width !== width || canvas.height !== height) {
    renderer.setSize(width, height, false);
    camera.aspect = width / Math.max(1, height);
    camera.updateProjectionMatrix();
  }
}
window.addEventListener('resize', resize);
resize();
animate();

loadSong(4024);
