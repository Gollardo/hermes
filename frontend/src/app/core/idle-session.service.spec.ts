import { TestBed } from '@angular/core/testing';

import { IdleSessionService, SESSION_IDLE_TIMEOUT_MS } from './idle-session.service';

describe('IdleSessionService', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-08-15T10:00:00Z'));
  });

  afterEach(() => {
    TestBed.inject(IdleSessionService).stop();
    vi.useRealTimers();
  });

  it('expires an authenticated screen after thirty minutes without interaction', () => {
    const idle = TestBed.inject(IdleSessionService);
    const onIdle = vi.fn();
    idle.start(onIdle, vi.fn());

    vi.advanceTimersByTime(SESSION_IDLE_TIMEOUT_MS);

    expect(onIdle).toHaveBeenCalledOnce();
  });

  it('extends the deadline and heartbeats while the owner is active', () => {
    const idle = TestBed.inject(IdleSessionService);
    const onIdle = vi.fn();
    const onHeartbeat = vi.fn();
    idle.start(onIdle, onHeartbeat);

    vi.advanceTimersByTime(29 * 60 * 1000);
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'a' }));
    vi.advanceTimersByTime(0);
    expect(onHeartbeat).toHaveBeenCalledOnce();

    vi.advanceTimersByTime(2 * 60 * 1000);
    expect(onIdle).not.toHaveBeenCalled();
    vi.advanceTimersByTime(28 * 60 * 1000);
    expect(onIdle).toHaveBeenCalledOnce();
  });

  it('persists an early isolated interaction before the server idle deadline', () => {
    const idle = TestBed.inject(IdleSessionService);
    const onHeartbeat = vi.fn();
    idle.start(vi.fn(), onHeartbeat);

    vi.advanceTimersByTime(60 * 1000);
    document.dispatchEvent(new PointerEvent('pointermove'));
    expect(onHeartbeat).not.toHaveBeenCalled();

    vi.advanceTimersByTime(4 * 60 * 1000);
    expect(onHeartbeat).toHaveBeenCalledOnce();
  });
});
