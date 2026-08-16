import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { OperationCreateMenu } from './operation-create-menu';

describe('OperationCreateMenu', () => {
  let fixture: ComponentFixture<OperationCreateMenu>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [OperationCreateMenu],
      providers: [provideRouter([])],
    }).compileComponents();
    fixture = TestBed.createComponent(OperationCreateMenu);
    fixture.detectChanges();
  });

  afterEach(() => vi.useRealTimers());

  it('supports arrow navigation and returns focus to the trigger on Escape', () => {
    vi.useFakeTimers();
    const trigger = fixture.nativeElement.querySelector(
      '.create-menu-trigger',
    ) as HTMLButtonElement;
    trigger.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true }));
    fixture.detectChanges();
    vi.runAllTimers();

    const items = Array.from(
      fixture.nativeElement.querySelectorAll('[role="menuitem"]'),
    ) as HTMLButtonElement[];
    expect(document.activeElement).toBe(items[0]);
    items[0].dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true }));
    expect(document.activeElement).toBe(items[1]);
    items[1].dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    fixture.detectChanges();
    expect(document.activeElement).toBe(trigger);
    expect(fixture.nativeElement.querySelector('[role="menu"]')).toBeNull();
  });
});
