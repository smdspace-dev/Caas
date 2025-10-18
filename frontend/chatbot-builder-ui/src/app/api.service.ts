import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, retry } from 'rxjs/operators';

export interface ApiResponse {
  status?: string;
  message?: string;
  timestamp?: string;
  service?: string;
  version?: string;
  received?: any;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = 'http://localhost:5000/api';

  constructor(private http: HttpClient) { }

  // Health check endpoint
  healthCheck(): Observable<ApiResponse> {
    return this.http.get<ApiResponse>(`${this.baseUrl}/health`)
      .pipe(
        retry(2),
        catchError(this.handleError)
      );
  }

  // Hello world endpoint
  hello(): Observable<ApiResponse> {
    return this.http.get<ApiResponse>(`${this.baseUrl}/hello`)
      .pipe(
        retry(2),
        catchError(this.handleError)
      );
  }

  // Test POST endpoint
  testPost(data: any): Observable<ApiResponse> {
    return this.http.post<ApiResponse>(`${this.baseUrl}/test`, data)
      .pipe(
        retry(1),
        catchError(this.handleError)
      );
  }

  // Error handling
  private handleError(error: HttpErrorResponse) {
    let errorMessage = 'An unknown error occurred!';
    
    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Client Error: ${error.error.message}`;
    } else {
      // Server-side error
      errorMessage = `Server Error: ${error.status} - ${error.message}`;
    }
    
    console.error('API Error:', errorMessage);
    return throwError(() => new Error(errorMessage));
  }
}