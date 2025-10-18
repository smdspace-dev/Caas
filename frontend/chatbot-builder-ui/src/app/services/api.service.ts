import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private readonly API_BASE_URL = 'http://localhost:5000/api';

  constructor(private http: HttpClient) { }

  private getHeaders(): HttpHeaders {
    return new HttpHeaders({
      'Content-Type': 'application/json'
    });
  }

  // Health check endpoint
  healthCheck(): Observable<any> {
    return this.http.get(`${this.API_BASE_URL}/health`);
  }

  // Hello world endpoint
  getHelloMessage(): Observable<any> {
    return this.http.get(`${this.API_BASE_URL}/hello`);
  }

  // Test POST endpoint
  testPost(data: any): Observable<any> {
    return this.http.post(`${this.API_BASE_URL}/test`, data, {
      headers: this.getHeaders()
    });
  }
}
