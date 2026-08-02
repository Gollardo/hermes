import { Injectable, signal } from '@angular/core';

import type { AccessState } from './auth.service';

@Injectable({ providedIn: 'root' })
export class AccessStateService {
  readonly state = signal<AccessState>('checking');
  readonly expiresAt = signal<string | null>(null);

  checking(): void {
    this.state.set('checking');
  }

  uninitialized(): void {
    this.expiresAt.set(null);
    this.state.set('uninitialized');
  }

  unauthenticated(): void {
    this.expiresAt.set(null);
    this.state.set('unauthenticated');
  }

  authenticated(expiresAt: string): void {
    this.expiresAt.set(expiresAt);
    this.state.set('authenticated');
  }

  unavailable(): void {
    this.state.set('unavailable');
  }
}
