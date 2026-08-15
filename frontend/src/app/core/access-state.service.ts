import { Injectable, signal } from '@angular/core';

import type { AccessState } from './auth.service';

@Injectable({ providedIn: 'root' })
export class AccessStateService {
  readonly state = signal<AccessState>('checking');
  readonly expiresAt = signal<string | null>(null);
  readonly idleTimeoutMs = signal<number | null>(null);

  checking(): void {
    this.state.set('checking');
  }

  uninitialized(): void {
    this.expiresAt.set(null);
    this.idleTimeoutMs.set(null);
    this.state.set('uninitialized');
  }

  unauthenticated(): void {
    this.expiresAt.set(null);
    this.idleTimeoutMs.set(null);
    this.state.set('unauthenticated');
  }

  authenticated(expiresAt: string, idleTimeoutSeconds = 30 * 60): void {
    this.expiresAt.set(expiresAt);
    this.idleTimeoutMs.set(idleTimeoutSeconds * 1000);
    this.state.set('authenticated');
  }

  unavailable(): void {
    this.state.set('unavailable');
  }
}
