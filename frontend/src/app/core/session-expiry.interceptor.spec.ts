import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { AccessStateService } from './access-state.service';
import { sessionExpiryInterceptor } from './session-expiry.interceptor';

describe('sessionExpiryInterceptor', () => {
  it('returns the shell to login when a protected request loses its session', () => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([sessionExpiryInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    const http = TestBed.inject(HttpClient);
    const controller = TestBed.inject(HttpTestingController);
    const access = TestBed.inject(AccessStateService);
    access.authenticated('2026-08-09T00:00:00Z');

    http.get('/api/v1/settings').subscribe({ error: () => undefined });
    controller
      .expectOne('/api/v1/settings')
      .flush(
        { detail: { code: 'authentication_required' } },
        { status: 401, statusText: 'Unauthorized' },
      );

    expect(access.state()).toBe('unauthenticated');
    controller.verify();
  });
});
