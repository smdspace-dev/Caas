import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { BehaviorSubject, Observable, throwError } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';

export interface User {
  id: string;
  email: string;
  name: string;
  plan: string;
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

export interface AuthResponse {
  message: string;
  user: User;
  access_token: string;
  refresh_token?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private baseUrl = 'http://localhost:5000/api/auth';
  private currentUserSubject = new BehaviorSubject<User | null>(null);
  private isLoggedInSubject = new BehaviorSubject<boolean>(false);

  public currentUser$ = this.currentUserSubject.asObservable();
  public isLoggedIn$ = this.isLoggedInSubject.asObservable();

  constructor(private http: HttpClient) {
    // Check if user is logged in on service initialization
    this.checkStoredAuth();
  }

  private checkStoredAuth(): void {
    const token = this.getToken();
    const userData = localStorage.getItem('user');
    
    if (token && userData) {
      try {
        const user = JSON.parse(userData);
        this.currentUserSubject.next(user);
        this.isLoggedInSubject.next(true);
        
        // Validate token with backend
        this.validateToken().subscribe({
          next: (response) => {
            // Token is valid, update user data
            this.currentUserSubject.next(response.user);
          },
          error: () => {
            // Token is invalid, clear stored data
            this.clearAuth();
          }
        });
      } catch (error) {
        // Invalid stored data
        this.clearAuth();
      }
    }
  }

  register(userData: RegisterRequest): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.baseUrl}/register`, userData)
      .pipe(
        tap(response => this.handleAuthSuccess(response)),
        catchError(this.handleError)
      );
  }

  login(credentials: LoginRequest): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.baseUrl}/login`, credentials)
      .pipe(
        tap(response => this.handleAuthSuccess(response)),
        catchError(this.handleError)
      );
  }

  logout(): Observable<any> {
    return this.http.post(`${this.baseUrl}/logout`, {})
      .pipe(
        tap(() => this.clearAuth()),
        catchError(this.handleError)
      );
  }

  refreshToken(): Observable<any> {
    const refreshToken = this.getRefreshToken();
    return this.http.post(`${this.baseUrl}/refresh`, {}, {
      headers: {
        'Authorization': `Bearer ${refreshToken}`
      }
    }).pipe(
      tap((response: any) => {
        localStorage.setItem('access_token', response.access_token);
        this.currentUserSubject.next(response.user);
      }),
      catchError(this.handleError)
    );
  }

  validateToken(): Observable<any> {
    return this.http.get(`${this.baseUrl}/validate`)
      .pipe(
        catchError(this.handleError)
      );
  }

  getCurrentUser(): Observable<any> {
    return this.http.get(`${this.baseUrl}/me`)
      .pipe(
        tap((response: any) => {
          this.currentUserSubject.next(response.user);
        }),
        catchError(this.handleError)
      );
  }

  private handleAuthSuccess(response: AuthResponse): void {
    // Store tokens and user data
    localStorage.setItem('access_token', response.access_token);
    if (response.refresh_token) {
      localStorage.setItem('refresh_token', response.refresh_token);
    }
    localStorage.setItem('user', JSON.stringify(response.user));

    // Update subjects
    this.currentUserSubject.next(response.user);
    this.isLoggedInSubject.next(true);
  }

  private clearAuth(): void {
    // Clear stored data
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');

    // Update subjects
    this.currentUserSubject.next(null);
    this.isLoggedInSubject.next(false);
  }

  // Utility methods
  getToken(): string | null {
    return localStorage.getItem('access_token');
  }

  getRefreshToken(): string | null {
    return localStorage.getItem('refresh_token');
  }

  isAuthenticated(): boolean {
    const token = this.getToken();
    return token !== null;
  }

  getCurrentUserValue(): User | null {
    return this.currentUserSubject.value;
  }

  private handleError(error: HttpErrorResponse) {
    let errorMessage = 'An unknown error occurred!';
    
    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Client Error: ${error.error.message}`;
    } else {
      // Server-side error
      if (error.error && error.error.error) {
        errorMessage = error.error.error;
      } else {
        errorMessage = `Server Error: ${error.status} - ${error.message}`;
      }
    }
    
    console.error('Auth Error:', errorMessage);
    return throwError(() => new Error(errorMessage));
  }
}