import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CategoriesPage } from './categories';

describe('CategoriesPage', () => {
  let fixture: ComponentFixture<CategoriesPage>;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CategoriesPage],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    fixture = TestBed.createComponent(CategoriesPage);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('creates an expense category', () => {
    fixture.detectChanges();
    http.expectOne('/api/v1/categories').flush([]);
    fixture.detectChanges();
    const name = fixture.nativeElement.querySelector('#category-name') as HTMLInputElement;
    name.value = 'Food';
    name.dispatchEvent(new Event('input'));
    fixture.nativeElement.querySelector('form').dispatchEvent(new Event('submit'));
    const request = http.expectOne('/api/v1/categories');
    expect(request.request.method).toBe('POST');
    expect(request.request.body.type).toBe('expense');
    request.flush({});
    http.expectOne('/api/v1/categories').flush([]);
  });

  it('re-enables the parent selector when switching from a parent to a leaf', () => {
    fixture.detectChanges();
    http.expectOne('/api/v1/categories').flush([
      {
        id: 'parent',
        type: 'expense',
        name: 'Home',
        description: null,
        parent_id: null,
        archived: false,
      },
      {
        id: 'child',
        type: 'expense',
        name: 'Utilities',
        description: null,
        parent_id: 'parent',
        archived: false,
      },
    ]);
    fixture.detectChanges();

    const editButtons = Array.from(
      fixture.nativeElement.querySelectorAll(
        '.directory-item button',
      ) as NodeListOf<HTMLButtonElement>,
    ).filter((button) => button.textContent?.trim() === 'Изменить');
    editButtons[0].click();
    fixture.detectChanges();
    expect(
      (fixture.nativeElement.querySelector('#category-parent') as HTMLSelectElement).disabled,
    ).toBe(true);

    editButtons[1].click();
    fixture.detectChanges();
    expect(
      (fixture.nativeElement.querySelector('#category-parent') as HTMLSelectElement).disabled,
    ).toBe(false);
  });
});
