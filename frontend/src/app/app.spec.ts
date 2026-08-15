import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { App } from './app';
import { AccessState, AuthService } from './core/auth.service';

describe('App', () => {
  const accessState = signal<AccessState>('checking');
  const idleTimeoutMs = signal(30 * 60 * 1000);
  const auth = {
    state: accessState,
    idleTimeoutMs,
    initialize: vi.fn(),
    logout: vi.fn(() => of(undefined)),
    keepAlive: vi.fn(),
    expireDueToInactivity: vi.fn(),
  };

  beforeEach(async () => {
    localStorage.removeItem('hermes-sidebar-hidden');
    accessState.set('checking');
    auth.initialize.mockClear();
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideRouter([]), { provide: AuthService, useValue: auth }],
    }).compileComponents();
  });

  it('checks application access state on startup', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();

    expect(auth.initialize).toHaveBeenCalledOnce();
    expect(fixture.nativeElement.textContent).toContain('Проверяем состояние');
  });

  it('renders the protected shell only for an authenticated owner', () => {
    accessState.set('authenticated');
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.brand')?.textContent).toContain('Hermes');
    expect(compiled.textContent).toContain('Настройки');
    expect(compiled.querySelector('.plan-label')?.textContent).toContain('План');
    expect(compiled.textContent).toContain('Календарь');
    expect(compiled.textContent).toContain('Прогноз');
  });

  it('lets the owner hide and restore the sidebar', () => {
    accessState.set('authenticated');
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();

    const toggle = fixture.nativeElement.querySelector('.sidebar-toggle') as HTMLButtonElement;
    toggle.click();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.app-shell').classList).toContain('sidebar-hidden');
    expect(localStorage.getItem('hermes-sidebar-hidden')).toBe('true');

    toggle.click();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.app-shell').classList).not.toContain(
      'sidebar-hidden',
    );
  });
});
