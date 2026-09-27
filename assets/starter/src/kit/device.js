// Device frames: neutral browser window and phone shells. No third-party brand chrome.
// Copyright (c) 向阳乔木 — MIT License.

export function browserWindow(content, { title = '' } = {}) {
  const w = document.createElement('div');
  w.className = 'dev-window';
  w.innerHTML = `<div class="dev-bar"><i></i><i></i><i></i><span class="dev-title"></span></div><div class="dev-body"></div>`;
  w.querySelector('.dev-title').textContent = title; // keep neutral: no URL unless allowed
  w.querySelector('.dev-body').appendChild(content);
  return w;
}

export function phone(content) {
  const p = document.createElement('div');
  p.className = 'dev-phone';
  p.innerHTML = '<div class="dev-screen"></div>';
  p.querySelector('.dev-screen').appendChild(content);
  return p;
}
