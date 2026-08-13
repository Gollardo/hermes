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
    const add = [...fixture.nativeElement.querySelectorAll('button')].find(
      (button: HTMLButtonElement) => button.textContent.trim() === 'Добавить категорию',
    ) as HTMLButtonElement;
    add.click();
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
      (fixture.nativeElement.querySelector('#category-parent') as HTMLInputElement).disabled,
    ).toBe(true);

    fixture.nativeElement.querySelector('button[aria-expanded="false"]').click();
    fixture.detectChanges();
    const childEdit = (
      [...fixture.nativeElement.querySelectorAll('.subcategory button')] as HTMLButtonElement[]
    ).find((button) => button.textContent.trim() === 'Изменить')!;
    childEdit.click();
    fixture.detectChanges();
    expect(
      (fixture.nativeElement.querySelector('#category-parent') as HTMLInputElement).disabled,
    ).toBe(false);
  });

  it('starts with children hidden and expands only one root per category type', () => {
    fixture.detectChanges();
    http.expectOne('/api/v1/categories').flush([
      {
        id: 'home',
        type: 'expense',
        name: 'Home',
        description: null,
        parent_id: null,
        archived: false,
      },
      {
        id: 'rent',
        type: 'expense',
        name: 'Rent',
        description: null,
        parent_id: 'home',
        archived: false,
      },
      {
        id: 'car',
        type: 'expense',
        name: 'Car',
        description: null,
        parent_id: null,
        archived: false,
      },
      {
        id: 'fuel',
        type: 'expense',
        name: 'Fuel',
        description: null,
        parent_id: 'car',
        archived: false,
      },
    ]);
    fixture.detectChanges();
    const toggles = [...fixture.nativeElement.querySelectorAll('button[aria-controls]')];
    expect(fixture.nativeElement.querySelectorAll('.subcategory-list')).toHaveLength(0);
    (toggles[0] as HTMLButtonElement).click();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Rent');
    (toggles[1] as HTMLButtonElement).click();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).not.toContain('Rent');
    expect(fixture.nativeElement.textContent).toContain('Fuel');
  });
});
