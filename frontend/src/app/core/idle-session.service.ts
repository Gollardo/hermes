import { DOCUMENT } from '@angular/common';
import { Injectable, inject } from '@angular/core';

export const SESSION_IDLE_TIMEOUT_MS = 30 * 60 * 1000;
const SESSION_HEARTBEAT_INTERVAL_MS = 5 * 60 * 1000;
const ACTIVITY_SHARE_INTERVAL_MS = 1000;
const DEADLINE_REFRESH_INTERVAL_MS = 1000;
const LAST_ACTIVITY_KEY = 'hermes-last-activity-at';
const ACTIVITY_EVENTS: readonly (keyof DocumentEventMap)[] = [
  'keydown',
  'pointerdown',
  'pointermove',
  'scroll',
  'touchstart',
];

@Injectable({ providedIn: 'root' })
export class IdleSessionService {
  private readonly document = inject(DOCUMENT);
  private readonly browserWindow = this.document.defaultView;
  private timeoutId: ReturnType<typeof setTimeout> | null = null;
  private heartbeatTimeoutId: ReturnType<typeof setTimeout> | null = null;
  private lastActivityAt = 0;
  private lastHeartbeatAt = 0;
  private lastSharedAt = 0;
  private lastDeadlineRefreshAt = 0;
  private idleTimeoutMs = SESSION_IDLE_TIMEOUT_MS;
  private heartbeatIntervalMs = SESSION_HEARTBEAT_INTERVAL_MS;
  private onIdle: (() => void) | null = null;
  private onHeartbeat: (() => void) | null = null;

  start(
    onIdle: () => void,
    onHeartbeat: () => void,
    idleTimeoutMs = SESSION_IDLE_TIMEOUT_MS,
  ): void {
    this.stop();
    this.onIdle = onIdle;
    this.onHeartbeat = onHeartbeat;
    this.idleTimeoutMs = idleTimeoutMs;
    this.heartbeatIntervalMs = Math.min(
      SESSION_HEARTBEAT_INTERVAL_MS,
      Math.max(1000, idleTimeoutMs / 3),
    );
    const now = Date.now();
    this.lastActivityAt = now;
    this.lastHeartbeatAt = now;
    this.lastDeadlineRefreshAt = now;
    this.shareActivity(now);
    for (const event of ACTIVITY_EVENTS) {
      this.document.addEventListener(event, this.recordActivity, { passive: true, capture: true });
    }
    this.document.addEventListener('visibilitychange', this.checkVisibility);
    this.browserWindow?.addEventListener('storage', this.acceptSharedActivity);
    this.scheduleCheck();
  }

  stop(): void {
    if (this.timeoutId !== null) clearTimeout(this.timeoutId);
    if (this.heartbeatTimeoutId !== null) clearTimeout(this.heartbeatTimeoutId);
    this.timeoutId = null;
    this.heartbeatTimeoutId = null;
    for (const event of ACTIVITY_EVENTS) {
      this.document.removeEventListener(event, this.recordActivity, { capture: true });
    }
    this.document.removeEventListener('visibilitychange', this.checkVisibility);
    this.browserWindow?.removeEventListener('storage', this.acceptSharedActivity);
    this.onIdle = null;
    this.onHeartbeat = null;
  }

  private readonly recordActivity = (): void => {
    if (!this.onIdle) return;
    const now = Date.now();
    this.lastActivityAt = now;
    if (now - this.lastSharedAt >= ACTIVITY_SHARE_INTERVAL_MS) this.shareActivity(now);
    this.queueHeartbeat(now);
    if (now - this.lastDeadlineRefreshAt >= DEADLINE_REFRESH_INTERVAL_MS) {
      this.lastDeadlineRefreshAt = now;
      this.scheduleCheck();
    }
  };

  private readonly acceptSharedActivity = (event: StorageEvent): void => {
    if (event.key !== LAST_ACTIVITY_KEY || event.newValue === null) return;
    const sharedAt = Number(event.newValue);
    if (!Number.isFinite(sharedAt) || sharedAt <= this.lastActivityAt) return;
    this.lastActivityAt = sharedAt;
    this.scheduleCheck();
  };

  private readonly checkVisibility = (): void => {
    if (this.document.visibilityState === 'visible' && this.onIdle) this.checkDeadline();
  };

  private shareActivity(at: number): void {
    this.lastSharedAt = at;
    try {
      this.browserWindow?.localStorage.setItem(LAST_ACTIVITY_KEY, String(at));
    } catch {
      // Storage may be unavailable in a hardened browser; the current tab still expires safely.
    }
  }

  private queueHeartbeat(now: number): void {
    if (!this.onHeartbeat || this.heartbeatTimeoutId !== null) return;
    const delay = Math.max(0, this.lastHeartbeatAt + this.heartbeatIntervalMs - now);
    this.heartbeatTimeoutId = setTimeout(() => {
      this.heartbeatTimeoutId = null;
      if (!this.onIdle || this.lastActivityAt <= this.lastHeartbeatAt) return;
      this.lastHeartbeatAt = Date.now();
      this.onHeartbeat?.();
    }, delay);
  }

  private scheduleCheck(): void {
    if (this.timeoutId !== null) clearTimeout(this.timeoutId);
    const remaining = Math.max(0, this.lastActivityAt + this.idleTimeoutMs - Date.now());
    this.timeoutId = setTimeout(() => this.checkDeadline(), remaining);
  }

  private checkDeadline(): void {
    const remaining = this.lastActivityAt + this.idleTimeoutMs - Date.now();
    if (remaining > 0) {
      this.scheduleCheck();
      return;
    }
    const callback = this.onIdle;
    this.stop();
    callback?.();
  }
}
