import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { BackendStatusPage } from './backend-status';

describe('BackendStatusPage', () => {
  let fixture: ComponentFixture<BackendStatusPage>;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [BackendStatusPage],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(BackendStatusPage);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('shows backend availability after a successful health check', () => {
    fixture.detectChanges();
    http.expectOne('/api/v1/health').flush({ status: 'ok' });
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Backend отвечает');
  });
});
