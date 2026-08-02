import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';

import { AccessStateService } from './access-state.service';

export const sessionExpiryInterceptor: HttpInterceptorFn = (request, next) => {
  const access = inject(AccessStateService);
  return next(request).pipe(
    catchError((error: unknown) => {
      if (error instanceof HttpErrorResponse && error.status === 401) {
        access.unauthenticated();
      }
      return throwError(() => error);
    }),
  );
};
