import { Component, OnInit } from '@angular/core';
import { RouterOutlet, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatIconModule } from '@angular/material/icon';
import { ApiService } from './api.service';
import { AuthService, User } from './auth.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    RouterOutlet, 
    CommonModule, 
    MatButtonModule, 
    MatCardModule,
    MatToolbarModule,
    MatIconModule
  ],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent implements OnInit {
  title = 'RAG Chatbot Builder';
  apiStatus = 'Checking...';
  helloMessage = '';
  isConnected = false;
  
  // Auth properties
  currentUser: User | null = null;
  isLoggedIn = false;

  constructor(
    private apiService: ApiService,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit() {
    this.testConnection();
    
    // Subscribe to auth state
    this.authService.currentUser$.subscribe(user => {
      this.currentUser = user;
    });
    
    this.authService.isLoggedIn$.subscribe(isLoggedIn => {
      this.isLoggedIn = isLoggedIn;
    });
  }

  testConnection() {
    // Test health endpoint
    this.apiService.healthCheck().subscribe({
      next: (response) => {
        this.apiStatus = response.message || 'Connected';
        this.isConnected = true;
        this.getHelloMessage();
      },
      error: (error: any) => {
        this.apiStatus = 'Connection failed - ' + error.message;
        this.isConnected = false;
      }
    });
  }

  getHelloMessage() {
    this.apiService.hello().subscribe({
      next: (response) => {
        this.helloMessage = response.message || 'Hello from backend!';
      },
      error: (error: any) => {
        console.error('Error getting hello message:', error);
      }
    });
  }

  testPost() {
    const testData = { message: 'Test from Angular', timestamp: new Date().toISOString() };
    this.apiService.testPost(testData).subscribe({
      next: (response) => {
        console.log('POST test successful:', response);
      },
      error: (error: any) => {
        console.error('POST test failed:', error);
      }
    });
  }

  // Navigation methods
  goToLogin(): void {
    this.router.navigate(['/login']);
  }

  goToRegister(): void {
    this.router.navigate(['/register']);
  }

  goToDashboard(): void {
    this.router.navigate(['/dashboard']);
  }

  logout(): void {
    this.authService.logout().subscribe({
      next: () => {
        this.router.navigate(['/login']);
      },
      error: (error) => {
        console.error('Logout error:', error);
      }
    });
  }
}
