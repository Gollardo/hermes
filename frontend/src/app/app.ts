import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { AuthService, apiErrorMessage } from './core/auth.service';
import { LoginPage } from './pages/login/login';
import { SetupPage } from './pages/setup/setup';

@Component({
  selector: 'app-root',
  imports: [RouterLink, RouterLinkActive, RouterOutlet, LoginPage, SetupPage],
  templateUrl: './app.html',
  styleUrl: './app.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class App implements OnInit {
  protected readonly auth = inject(AuthService);
  protected readonly actionError = signal<string | null>(null);
  protected readonly sidebarHidden = signal(readSidebarPreference());

  ngOnInit(): void {
    this.auth.initialize();
  }

  protected logout(): void {
    this.actionError.set(null);
    this.auth.logout().subscribe({
      error: (error: unknown) =>
        this.actionError.set(apiErrorMessage(error, 'Не удалось завершить сессию.')),
    });
  }

  protected toggleSidebar(): void {
    this.sidebarHidden.update((hidden) => !hidden);
    localStorage.setItem('hermes-sidebar-hidden', String(this.sidebarHidden()));
  }
}

function readSidebarPreference(): boolean {
  return (
    typeof localStorage !== 'undefined' && localStorage.getItem('hermes-sidebar-hidden') === 'true'
  );
}
