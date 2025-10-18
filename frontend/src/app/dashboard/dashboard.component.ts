import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatTabsModule } from '@angular/material/tabs';
import { MatSnackBarModule, MatSnackBar } from '@angular/material/snack-bar';
import { MatDialogModule, MatDialog } from '@angular/material/dialog';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { AuthService } from '../auth.service';
import { FileUploadComponent } from '../file-upload/file-upload.component';
import { ChatInterfaceComponent } from '../chat-interface/chat-interface.component';

export interface Chatbot {
  id: string;
  name: string;
  description: string;
  theme: string;
  tone: string;
  is_active: boolean;
  created_at: string;
  document_count: number;
  query_count: number;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatButtonModule,
    MatIconModule,
    MatCardModule,
    MatSelectModule,
    MatFormFieldModule,
    MatTabsModule,
    MatSnackBarModule,
    MatDialogModule,
    FileUploadComponent,
    ChatInterfaceComponent
  ],
  template: `
    <div class="dashboard-container">
      <!-- Header -->
      <div class="dashboard-header">
        <h1>RAG Chatbot Builder</h1>
        <div class="header-actions">
          <mat-form-field appearance="outline" class="chatbot-selector">
            <mat-label>Select Chatbot</mat-label>
            <mat-select [(value)]="selectedChatbotId" (selectionChange)="onChatbotChange()">
              <mat-option *ngFor="let chatbot of chatbots" [value]="chatbot.id">
                {{ chatbot.name }}
                <span class="chatbot-stats">({{ chatbot.document_count }} docs)</span>
              </mat-option>
            </mat-select>
          </mat-form-field>
          
          <button mat-raised-button color="primary" (click)="createNewChatbot()">
            <mat-icon>add</mat-icon>
            New Chatbot
          </button>
          
          <button mat-button (click)="refreshData()">
            <mat-icon>refresh</mat-icon>
            Refresh
          </button>
        </div>
      </div>

      <!-- Main Content -->
      <div class="dashboard-content" *ngIf="selectedChatbotId">
        <mat-tab-group [(selectedIndex)]="selectedTabIndex" class="main-tabs">
          <!-- Documents Tab -->
          <mat-tab label="Documents">
            <ng-template matTabContent>
              <div class="tab-content">
                <app-file-upload 
                  [chatbotId]="selectedChatbotId"
                  (documentsChanged)="onDocumentsChanged($event)">
                </app-file-upload>
              </div>
            </ng-template>
          </mat-tab>

          <!-- Chat Tab -->
          <mat-tab label="Chat & Test">
            <ng-template matTabContent>
              <div class="tab-content">
                <app-chat-interface 
                  [chatbotId]="selectedChatbotId">
                </app-chat-interface>
              </div>
            </ng-template>
          </mat-tab>

          <!-- Settings Tab -->
          <mat-tab label="Settings">
            <ng-template matTabContent>
              <div class="tab-content">
                <div class="settings-container">
                  <mat-card>
                    <mat-card-header>
                      <mat-card-title>Chatbot Settings</mat-card-title>
                      <mat-card-subtitle>Configure your chatbot behavior</mat-card-subtitle>
                    </mat-card-header>
                    
                    <mat-card-content>
                      <div class="settings-form" *ngIf="selectedChatbot">
                        <mat-form-field appearance="outline" class="full-width">
                          <mat-label>Chatbot Name</mat-label>
                          <input matInput [(ngModel)]="selectedChatbot.name">
                        </mat-form-field>

                        <mat-form-field appearance="outline" class="full-width">
                          <mat-label>Description</mat-label>
                          <textarea matInput [(ngModel)]="selectedChatbot.description" rows="3"></textarea>
                        </mat-form-field>

                        <mat-form-field appearance="outline">
                          <mat-label>Theme</mat-label>
                          <mat-select [(value)]="selectedChatbot.theme">
                            <mat-option value="default">Default</mat-option>
                            <mat-option value="professional">Professional</mat-option>
                            <mat-option value="friendly">Friendly</mat-option>
                            <mat-option value="minimal">Minimal</mat-option>
                          </mat-select>
                        </mat-form-field>

                        <mat-form-field appearance="outline">
                          <mat-label>Response Tone</mat-label>
                          <mat-select [(value)]="selectedChatbot.tone">
                            <mat-option value="professional">Professional</mat-option>
                            <mat-option value="friendly">Friendly</mat-option>
                            <mat-option value="casual">Casual</mat-option>
                            <mat-option value="formal">Formal</mat-option>
                          </mat-select>
                        </mat-form-field>
                      </div>
                    </mat-card-content>

                    <mat-card-actions>
                      <button mat-raised-button color="primary" (click)="saveChatbotSettings()">
                        <mat-icon>save</mat-icon>
                        Save Settings
                      </button>
                      
                      <button mat-button color="warn" (click)="deleteChatbot()">
                        <mat-icon>delete</mat-icon>
                        Delete Chatbot
                      </button>
                    </mat-card-actions>
                  </mat-card>

                  <!-- API Integration -->
                  <mat-card class="api-card">
                    <mat-card-header>
                      <mat-card-title>API Integration</mat-card-title>
                      <mat-card-subtitle>Embed your chatbot in external applications</mat-card-subtitle>
                    </mat-card-header>
                    
                    <mat-card-content>
                      <div class="api-section">
                        <h4>API Endpoint</h4>
                        <div class="api-endpoint">
                          {{ getApiEndpoint() }}
                        </div>
                        
                        <h4>API Key</h4>
                        <div class="api-key">
                          <span class="key-display">{{ selectedChatbot?.api_key || 'Not available' }}</span>
                          <button mat-icon-button (click)="regenerateApiKey()" color="primary">
                            <mat-icon>refresh</mat-icon>
                          </button>
                        </div>
                        
                        <h4>Embed Code</h4>
                        <button mat-raised-button (click)="getEmbedCode()">
                          <mat-icon>code</mat-icon>
                          Generate Embed Code
                        </button>
                      </div>
                    </mat-card-content>
                  </mat-card>
                </div>
              </div>
            </ng-template>
          </mat-tab>
        </mat-tab-group>
      </div>

      <!-- Empty State -->
      <div class="empty-state" *ngIf="!selectedChatbotId">
        <mat-card>
          <mat-card-content>
            <div class="empty-content">
              <mat-icon class="empty-icon">smart_toy</mat-icon>
              <h2>Welcome to RAG Chatbot Builder</h2>
              <p>Create your first chatbot to get started</p>
              <button mat-raised-button color="primary" (click)="createNewChatbot()">
                <mat-icon>add</mat-icon>
                Create Your First Chatbot
              </button>
            </div>
          </mat-card-content>
        </mat-card>
      </div>
    </div>
  `,
  styles: [`
    .dashboard-container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 16px;
    }

    .dashboard-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
      padding: 16px 0;
      border-bottom: 1px solid #eee;
    }

    .dashboard-header h1 {
      margin: 0;
      color: #333;
    }

    .header-actions {
      display: flex;
      gap: 16px;
      align-items: center;
    }

    .chatbot-selector {
      min-width: 200px;
    }

    .chatbot-stats {
      font-size: 12px;
      color: #666;
      margin-left: 8px;
    }

    .dashboard-content {
      min-height: 600px;
    }

    .main-tabs {
      width: 100%;
    }

    .tab-content {
      padding: 24px 0;
    }

    .settings-container {
      max-width: 600px;
      margin: 0 auto;
    }

    .settings-form {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .full-width {
      width: 100%;
    }

    .api-card {
      margin-top: 24px;
    }

    .api-section h4 {
      margin: 16px 0 8px 0;
      color: #333;
    }

    .api-endpoint {
      background: #f5f5f5;
      border: 1px solid #ddd;
      border-radius: 4px;
      padding: 12px;
      font-family: monospace;
      font-size: 14px;
      word-break: break-all;
    }

    .api-key {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .key-display {
      background: #f5f5f5;
      border: 1px solid #ddd;
      border-radius: 4px;
      padding: 8px 12px;
      font-family: monospace;
      font-size: 14px;
      flex: 1;
    }

    .empty-state {
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 400px;
    }

    .empty-content {
      text-align: center;
      padding: 40px;
    }

    .empty-icon {
      font-size: 72px;
      width: 72px;
      height: 72px;
      color: #3f51b5;
      margin-bottom: 24px;
    }

    .empty-content h2 {
      margin: 16px 0;
      color: #333;
    }

    .empty-content p {
      color: #666;
      margin-bottom: 24px;
    }

    /* Responsive Design */
    @media (max-width: 768px) {
      .dashboard-header {
        flex-direction: column;
        gap: 16px;
        align-items: stretch;
      }

      .header-actions {
        flex-direction: column;
        gap: 8px;
      }

      .chatbot-selector {
        min-width: unset;
        width: 100%;
      }

      .dashboard-container {
        padding: 8px;
      }

      .settings-container {
        max-width: 100%;
      }
    }
  `]
})
export class DashboardComponent implements OnInit {
  chatbots: Chatbot[] = [];
  selectedChatbotId: string = '';
  selectedChatbot: Chatbot | null = null;
  selectedTabIndex: number = 0;

  constructor(
    private http: HttpClient,
    private authService: AuthService,
    private snackBar: MatSnackBar,
    private dialog: MatDialog
  ) {}

  ngOnInit() {
    this.loadChatbots();
  }

  loadChatbots() {
    const token = this.authService.getToken();
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);

    this.http.get<any>('http://localhost:5000/api/chatbots/', { headers })
      .subscribe({
        next: (response) => {
          this.chatbots = response.chatbots || [];
          if (this.chatbots.length > 0 && !this.selectedChatbotId) {
            this.selectedChatbotId = this.chatbots[0].id;
            this.onChatbotChange();
          }
        },
        error: (error) => {
          console.error('Failed to load chatbots:', error);
          this.snackBar.open('Failed to load chatbots', 'Close', { duration: 3000 });
        }
      });
  }

  onChatbotChange() {
    this.selectedChatbot = this.chatbots.find(bot => bot.id === this.selectedChatbotId) || null;
  }

  onDocumentsChanged(documents: any[]) {
    // Update document count for selected chatbot
    if (this.selectedChatbot) {
      this.selectedChatbot.document_count = documents.length;
      
      // Update in the chatbots array
      const index = this.chatbots.findIndex(bot => bot.id === this.selectedChatbotId);
      if (index !== -1) {
        this.chatbots[index].document_count = documents.length;
      }
    }
  }

  createNewChatbot() {
    const name = prompt('Enter chatbot name:');
    if (!name || !name.trim()) {
      return;
    }

    const token = this.authService.getToken();
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);

    this.http.post<any>('http://localhost:5000/api/chatbots/', {
      name: name.trim(),
      description: '',
      theme: 'default',
      tone: 'friendly'
    }, { headers }).subscribe({
      next: (response) => {
        this.snackBar.open('Chatbot created successfully', 'Close', { duration: 3000 });
        this.loadChatbots();
        this.selectedChatbotId = response.chatbot.id;
        this.onChatbotChange();
      },
      error: (error) => {
        console.error('Failed to create chatbot:', error);
        this.snackBar.open(
          error.error?.message || 'Failed to create chatbot', 
          'Close', 
          { duration: 5000 }
        );
      }
    });
  }

  saveChatbotSettings() {
    if (!this.selectedChatbot) return;

    const token = this.authService.getToken();
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);

    this.http.put<any>(`http://localhost:5000/api/chatbots/${this.selectedChatbotId}`, {
      name: this.selectedChatbot.name,
      description: this.selectedChatbot.description,
      theme: this.selectedChatbot.theme,
      tone: this.selectedChatbot.tone
    }, { headers }).subscribe({
      next: (response) => {
        this.snackBar.open('Settings saved successfully', 'Close', { duration: 3000 });
        this.loadChatbots();
      },
      error: (error) => {
        console.error('Failed to save settings:', error);
        this.snackBar.open(
          error.error?.message || 'Failed to save settings', 
          'Close', 
          { duration: 5000 }
        );
      }
    });
  }

  deleteChatbot() {
    if (!this.selectedChatbot) return;

    if (!confirm(`Are you sure you want to delete "${this.selectedChatbot.name}"? This action cannot be undone.`)) {
      return;
    }

    const token = this.authService.getToken();
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);

    this.http.delete(`http://localhost:5000/api/chatbots/${this.selectedChatbotId}`, { headers })
      .subscribe({
        next: () => {
          this.snackBar.open('Chatbot deleted successfully', 'Close', { duration: 3000 });
          this.selectedChatbotId = '';
          this.selectedChatbot = null;
          this.loadChatbots();
        },
        error: (error) => {
          console.error('Failed to delete chatbot:', error);
          this.snackBar.open('Failed to delete chatbot', 'Close', { duration: 5000 });
        }
      });
  }

  regenerateApiKey() {
    if (!this.selectedChatbotId) return;

    const token = this.authService.getToken();
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);

    this.http.post<any>(`http://localhost:5000/api/chatbots/${this.selectedChatbotId}/regenerate-api-key`, {}, { headers })
      .subscribe({
        next: (response) => {
          this.snackBar.open('API key regenerated successfully', 'Close', { duration: 3000 });
          if (this.selectedChatbot) {
            this.selectedChatbot.api_key = response.api_key;
          }
        },
        error: (error) => {
          console.error('Failed to regenerate API key:', error);
          this.snackBar.open('Failed to regenerate API key', 'Close', { duration: 5000 });
        }
      });
  }

  getEmbedCode() {
    if (!this.selectedChatbotId) return;

    const token = this.authService.getToken();
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);

    this.http.get<any>(`http://localhost:5000/api/chatbots/${this.selectedChatbotId}/embed-code`, { headers })
      .subscribe({
        next: (response) => {
          // Create a dialog or modal to show the embed code
          const embedCode = response.embed_code;
          
          // For now, copy to clipboard
          navigator.clipboard.writeText(embedCode).then(() => {
            this.snackBar.open('Embed code copied to clipboard', 'Close', { duration: 3000 });
          }).catch(() => {
            // Fallback: show in alert
            alert('Embed Code:\n\n' + embedCode);
          });
        },
        error: (error) => {
          console.error('Failed to get embed code:', error);
          this.snackBar.open('Failed to generate embed code', 'Close', { duration: 5000 });
        }
      });
  }

  getApiEndpoint(): string {
    if (!this.selectedChatbot?.api_key) {
      return 'No API key available';
    }
    return `http://localhost:5000/api/chat/public/${this.selectedChatbot.api_key}/query`;
  }

  refreshData() {
    this.loadChatbots();
    this.snackBar.open('Data refreshed', 'Close', { duration: 2000 });
  }
}