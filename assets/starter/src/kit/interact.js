// Drive real components by time: set values like a user would, click only when state differs.
// Copyright (c) 向阳乔木 — MIT License.

/** Write a value into a real <input>/<textarea> so React/Vue onChange fires. */
export function setNativeValue(el, value) {
  const proto = el instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
  const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
  if (el.value === value) return false;
  setter.call(el, value);
  el.dispatchEvent(new Event('input', { bubbles: true }));
  return true;
}

/** Ensure a toggle-like state: calls click() only if isOn() !== want. Seek-safe in both directions. */
export async function ensure(isOn, want, el) {
  if (Boolean(isOn()) !== Boolean(want)) {
    el.click();
    await new Promise((r) => setTimeout(r, 0));
  }
}
