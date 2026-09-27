// Camera: wrap content in a rig and move it with x / y / scale so a target lands in frame.
// Copyright (c) 向阳乔木 — MIT License.

export function rig(content) {
  const cam = document.createElement('div');
  cam.className = 'camera';
  cam.appendChild(content);
  return cam;
}

/**
 * Transform for the camera rig so that `target` (a descendant, measured untransformed)
 * is centred in `frame` at `scale`. Measure in view() before any tween touches the rig.
 * For 3D-tilted rigs measure at the actual time with screenCenterAt() instead.
 */
export function focusOn(cam, target, frame, scale = 2, anchor = { x: 0.5, y: 0.5 }) {
  const prev = cam.style.transform;
  cam.style.transform = 'none';
  const f = frame.getBoundingClientRect();
  const c = cam.getBoundingClientRect();
  const t = target.getBoundingClientRect();
  cam.style.transform = prev;
  const tx = t.left - c.left + t.width / 2;
  const ty = t.top - c.top + t.height / 2;
  // rig uses transform-origin 0 0
  return {
    x: f.width * anchor.x - tx * scale - (c.left - f.left),
    y: f.height * anchor.y - ty * scale - (c.top - f.top),
    scale,
  };
}
