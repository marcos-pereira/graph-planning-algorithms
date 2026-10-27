//    This code is distributed WITHOUT ANY WARRANTY, without the implied
//   warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
//   See the GNU Lesser General Public License for more details.

//   The license is distributed along with this repository or you can check
//   <http://www.gnu.org/licenses/> for more details.

// Contributors:
// marcos-pereira (https://github.com/marcos-pereira)

// ── State ──────────────────────────────────────────────────────────────────
let app = null;           // PIXI.Application
let planData = null;      // last response from /plan
let cellIndex = 0;        // how many explored cells have been drawn
let isAnimating = false;

// PixiJS objects created per run
let renderTexture = null; // accumulates drawn cells efficiently
let exploredSprite = null; // sprite backed by renderTexture
let tempGraphics = null;  // re-used each frame to draw a batch of cells
let overlayGraphics = null; // path + start/goal circles drawn after animation

// Preview state — shows the map + start/goal markers before any planning has run,
// and lets the user click the canvas to set them instead of typing coordinates.
let previewActive = false;
let mapWidth = 0;
let mapHeight = 0;
let canvasScale = 1;
let placeMode = null; // null | 'start' | 'goal' — which point the next click sets
let previewGeneration = 0; // guards against overlapping initPreview() calls (rapid map switches)

// ── DOM refs ───────────────────────────────────────────────────────────────
const runBtn        = document.getElementById('run-btn');
const setStartBtn   = document.getElementById('set-start-btn');
const setGoalBtn    = document.getElementById('set-goal-btn');
const statusEl      = document.getElementById('status');
const mapSelect     = document.getElementById('map-name');
const plannerSelect = document.getElementById('planner');
const neighborhoodSelect = document.getElementById('neighborhood');
const speedInput    = document.getElementById('speed');
const speedLabel    = document.getElementById('speed-label');
const canvasEl      = document.getElementById('canvas-container');
const placeholder   = document.getElementById('placeholder');
const placeholderText = placeholder.querySelector('p');
const x0Input       = document.getElementById('x0');
const y0Input       = document.getElementById('y0');
const xgInput       = document.getElementById('xg');
const ygInput       = document.getElementById('yg');

// ── Startup ────────────────────────────────────────────────────────────────
async function loadMapList() {
    try {
        const resp = await fetch('/maps-list');
        const maps = await resp.json();
        maps.forEach(name => {
            const opt = document.createElement('option');
            opt.value = name;
            opt.textContent = name;
            if (name === 'simplemaze.png') opt.selected = true;
            mapSelect.appendChild(opt);
        });
    } catch {
        setStatus('⚠️ Could not load map list.');
    }
}

// ── Helpers ────────────────────────────────────────────────────────────────
function setStatus(msg) { statusEl.textContent = msg; }

// Short label of the selected algorithm, e.g. BFS or DFS
function plannerLabel() { return plannerSelect.value.toUpperCase(); }

function getParams() {
    return {
        planner: plannerSelect.value,
        neighborhood: neighborhoodSelect.value,
        map_name: mapSelect.value,
        x0: parseInt(x0Input.value),
        y0: parseInt(y0Input.value),
        xg: parseInt(xgInput.value),
        yg: parseInt(ygInput.value),
    };
}

// Start/goal markers scale with the map so they stay visible on large maps
function markerRadius() {
    return Math.max(4, Math.round(Math.min(mapWidth, mapHeight) / 80));
}

function destroyApp() {
    if (!app) return;
    app.ticker.remove(animationStep);
    app.view.removeEventListener('click', onCanvasClick);
    // texture:false — the map sprite's texture is managed by PIXI.Assets; destroying
    // it here (instead of via Assets.unload()) corrupts the Assets cache for future
    // loads of the same map. renderTexture (explored-cell accumulation) is NOT
    // Assets-managed, so it's destroyed explicitly below instead.
    app.destroy(true, { children: true, texture: false });
    if (renderTexture) renderTexture.destroy(true);
    app = renderTexture = exploredSprite = tempGraphics = overlayGraphics = null;
    previewActive = false;
    setPlaceMode(null);
    // Remove the canvas element the old app appended
    const old = canvasEl.querySelector('canvas');
    if (old) old.remove();
}

// ── Preview (click-to-place start/goal) ───────────────────────────────────
// Shows just the map and the start/goal markers — no search, no path — so the
// user can set start/goal either by clicking here or by typing coordinates,
// before ever running the planner.
async function initPreview() {
    const myGeneration = ++previewGeneration;
    destroyApp();
    placeholder.style.display = 'block';
    placeholderText.textContent = 'Loading map...';
    setStatus('Ready — select a map and click Run.');

    const mapName = mapSelect.value;
    if (!mapName) {
        placeholderText.textContent = 'No map selected.';
        return;
    }

    // Everything below can throw for reasons unrelated to the map fetch itself
    // (e.g. WebGL unavailable when constructing the PIXI.Application) — wrapping
    // the whole thing, not just the texture load, ensures a failure here always
    // shows a clear message instead of leaving "Loading map..." stuck forever.
    try {
        const texture = await PIXI.Assets.load(`/maps/${mapName}`);
        if (myGeneration !== previewGeneration) return; // superseded by a newer call

        mapWidth = texture.width;
        mapHeight = texture.height;

        const containerW = canvasEl.clientWidth  || 800;
        const containerH = canvasEl.clientHeight || 600;
        canvasScale = Math.min(containerW / mapWidth, containerH / mapHeight, 1);
        const canvasW = Math.floor(mapWidth  * canvasScale);
        const canvasH = Math.floor(mapHeight * canvasScale);

        app = new PIXI.Application({
            width: canvasW,
            height: canvasH,
            backgroundColor: 0xF5F5F5,
            antialias: true,
        });
        canvasEl.appendChild(app.view);
        app.stage.scale.set(canvasScale);

        const mapSprite = new PIXI.Sprite(texture);
        app.stage.addChild(mapSprite);

        overlayGraphics = new PIXI.Graphics();
        app.stage.addChild(overlayGraphics);

        app.view.style.cursor = 'crosshair';
        app.view.addEventListener('click', onCanvasClick);

        placeholder.style.display = 'none';
        previewActive = true;
        planData = null;
        updateMarkersFromInputs();
    } catch (e) {
        if (myGeneration !== previewGeneration) return; // superseded by a newer call
        console.error('Failed to show the map preview:', e);
        placeholder.style.display = 'block';
        placeholderText.textContent = '⚠️ Could not load the map.';
        setStatus(`⚠️ Could not load map: ${e.message || e}`);
    }
}

function onCanvasClick(event) {
    if (!placeMode) return;

    const rect = app.view.getBoundingClientRect();
    const clickX = (event.clientX - rect.left) / canvasScale;
    const clickY = (event.clientY - rect.top) / canvasScale;
    // Cells are indexed by the pixel that contains the click
    const mapX = Math.floor(Math.min(Math.max(clickX, 0), mapWidth - 1));
    const mapY = Math.floor(Math.min(Math.max(clickY, 0), mapHeight - 1));

    if (placeMode === 'start') {
        x0Input.value = mapX;
        y0Input.value = mapY;
    } else {
        xgInput.value = mapX;
        ygInput.value = mapY;
    }

    updateMarkersFromInputs();
    setPlaceMode(null);
}

function setPlaceMode(mode) {
    // Clicking the already-active tool's button turns it back off.
    placeMode = (placeMode === mode) ? null : mode;
    setStartBtn.classList.toggle('active', placeMode === 'start');
    setGoalBtn.classList.toggle('active', placeMode === 'goal');
}

function updateMarkersFromInputs() {
    if (!overlayGraphics || !previewActive) return;

    const x0 = parseFloat(x0Input.value) || 0;
    const y0 = parseFloat(y0Input.value) || 0;
    const xg = parseFloat(xgInput.value) || 0;
    const yg = parseFloat(ygInput.value) || 0;

    overlayGraphics.clear();
    drawMarkers(overlayGraphics, [x0, y0], [xg, yg], 0x5CD676);
}

// Draw the goal and start circles centered on their cells
function drawMarkers(graphics, start, goal, goalColor) {
    const radius = markerRadius();
    graphics.lineStyle(0);
    graphics.beginFill(goalColor);
    graphics.drawCircle(goal[0] + 0.5, goal[1] + 0.5, radius);
    graphics.endFill();
    graphics.beginFill(0xFFCF58);
    graphics.drawCircle(start[0] + 0.5, start[1] + 0.5, radius);
    graphics.endFill();
}

async function ensurePreview() {
    if (!previewActive) await initPreview();
}

// ── Main flow ──────────────────────────────────────────────────────────────
async function run() {
    runBtn.disabled = true;
    destroyApp();
    placeholder.style.display = 'block';

    const params = getParams();
    setStatus(`⏳ Running ${plannerLabel()} (this may take a moment)...`);

    const url = new URL('/plan', window.location.origin);
    Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));

    let data;
    try {
        const resp = await fetch(url);
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({ detail: resp.statusText }));
            throw new Error(err.detail || resp.statusText);
        }
        data = await resp.json();
    } catch (e) {
        runBtn.disabled = false;
        await initPreview();
        // Set after initPreview(), which resets the status to "Ready"
        setStatus(`❌ ${e.message}`);
        return;
    }

    planData = data;
    mapWidth = data.map_width;
    mapHeight = data.map_height;
    placeholder.style.display = 'none';
    setStatus(`🎨 Animating ${data.explored_count} explored cells...`);

    await initCanvas(data);
    startAnimation();
}

// ── Canvas init (run) ─────────────────────────────────────────────────────
async function initCanvas(data) {
    // Fit the map into the available container while preserving aspect ratio
    const containerW = canvasEl.clientWidth  || 800;
    const containerH = canvasEl.clientHeight || 600;
    const scale = Math.min(containerW / data.map_width, containerH / data.map_height, 1);
    const canvasW = Math.floor(data.map_width  * scale);
    const canvasH = Math.floor(data.map_height * scale);
    canvasScale = scale;

    app = new PIXI.Application({
        width: canvasW,
        height: canvasH,
        backgroundColor: 0xF5F5F5,
        antialias: true,
    });
    canvasEl.appendChild(app.view);

    // Scale the stage so cell coordinates map 1-to-1 with map pixels
    app.stage.scale.set(scale);

    // Background: the original map PNG
    // PixiJS y-axis goes DOWN (top-left origin) — same as image coords, so no flip needed.
    const texture = await PIXI.Assets.load(`/maps/${data.map_name}`);
    const mapSprite = new PIXI.Sprite(texture);
    app.stage.addChild(mapSprite);

    // RenderTexture accumulates explored cells each frame without recalculating all geometry
    renderTexture = PIXI.RenderTexture.create({ width: data.map_width, height: data.map_height });
    exploredSprite = new PIXI.Sprite(renderTexture);
    exploredSprite.alpha = 0.35;
    app.stage.addChild(exploredSprite);

    // Temporary Graphics object re-used every frame to draw one batch
    tempGraphics = new PIXI.Graphics();

    // Overlay sits on top: path line + start/goal circles
    overlayGraphics = new PIXI.Graphics();
    app.stage.addChild(overlayGraphics);
}

// ── Animation ──────────────────────────────────────────────────────────────
function startAnimation() {
    cellIndex = 0;
    isAnimating = true;
    app.ticker.add(animationStep);
}

function animationStep() {
    if (!isAnimating || !planData) return;

    const speed    = parseInt(speedInput.value);
    // explored is a flat [x0, y0, x1, y1, ...] list in the planner's discovery order
    const explored = planData.explored;
    const cellCount = explored.length / 2;
    const count    = Math.min(speed, cellCount - cellIndex);

    if (count > 0) {
        // Draw `count` new cells into tempGraphics, then bake into renderTexture
        tempGraphics.clear();
        tempGraphics.beginFill(0xC400B7, 1);

        for (let i = 0; i < count; i++) {
            tempGraphics.drawRect(explored[2 * cellIndex], explored[2 * cellIndex + 1], 1, 1);
            cellIndex++;
        }

        tempGraphics.endFill();
        // clear:false accumulates without erasing previous cells
        app.renderer.render(tempGraphics, { renderTexture, clear: false });
    }

    if (cellIndex >= cellCount) {
        isAnimating = false;
        app.ticker.remove(animationStep);
        drawOverlay();
        runBtn.disabled = false;

        const timeText = `${(planData.planning_time * 1000).toFixed(0)} ms`;
        if (planData.path_found) {
            setStatus(
                `✅ Done — Path: ${planData.path.length} nodes (${planData.path.length - 1} steps) | ` +
                `Explored: ${planData.explored_count} | Time: ${timeText}`
            );
        } else {
            setStatus(
                `⚠️ Goal unreachable, no path found | Explored: ${planData.explored_count} | Time: ${timeText}`
            );
        }
    }
}

// ── Overlay (path + circles) ───────────────────────────────────────────────
function drawOverlay() {
    const d = planData;
    overlayGraphics.clear();

    // Path (blue) through the cell centers
    if (d.path.length > 1) {
        overlayGraphics.lineStyle(Math.max(2, markerRadius() / 2), 0x0B27DB, 1);
        overlayGraphics.moveTo(d.path[0][0] + 0.5, d.path[0][1] + 0.5);
        for (let i = 1; i < d.path.length; i++) {
            overlayGraphics.lineTo(d.path[i][0] + 0.5, d.path[i][1] + 0.5);
        }
    }

    drawMarkers(overlayGraphics, d.x_init, d.x_goal, d.path_found ? 0x0AD676 : 0x5CD676);
}

// ── Events ─────────────────────────────────────────────────────────────────
function updateRunButtonLabel() {
    runBtn.textContent = `▶ Run ${plannerLabel()}`;
}
plannerSelect.addEventListener('change', updateRunButtonLabel);

speedInput.addEventListener('input', () => {
    speedLabel.textContent = `${speedInput.value} cells / frame`;
});

runBtn.addEventListener('click', run);

setStartBtn.addEventListener('click', async () => {
    await ensurePreview();
    setPlaceMode('start');
});

setGoalBtn.addEventListener('click', async () => {
    await ensurePreview();
    setPlaceMode('goal');
});

mapSelect.addEventListener('change', () => {
    initPreview();
});

// Typing coordinates directly still works — keep the preview markers in sync.
[x0Input, y0Input, xgInput, ygInput].forEach(input => {
    input.addEventListener('input', updateMarkersFromInputs);
});

// ── Init ───────────────────────────────────────────────────────────────────
loadMapList().then(initPreview);
