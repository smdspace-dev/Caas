import { Component, Input, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatCardModule } from '@angular/material/card';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBarModule, MatSnackBar } from '@angular/material/snack-bar';
import { MatMenuModule } from '@angular/material/menu';
import { MatDividerModule } from '@angular/material/divider';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { AuthService } from '../auth.service';

export interface ChatMessage {
  id?: string;
  message: string;
  response: string;
  timestamp: string;
  isUser: boolean;
  isBot: boolean;
}

export interface ChatQuery {
  id: string;
  message: string;
  response: string;
  created_at: string;
  response_time: number;
  context_used: boolean;
}

@Component({
  selector: 'app-chat-interface',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatButtonModule,
    MatIconModule,
    MatInputModule,
    MatFormFieldModule,
    MatCardModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
    MatMenuModule,
    MatDividerModule
  ],
  template: `
    <mat-card class="chat-card">
      <mat-card-header>
        <mat-card-title>Chat with your AI Assistant</mat-card-title>
        <mat-card-subtitle>Ask questions about your uploaded documents</mat-card-subtitle>
        
        <div class="header-actions">
          <button mat-icon-button [matMenuTriggerFor]="menu">
            <mat-icon>more_vert</mat-icon>
          </button>
          <mat-menu #menu="matMenu">
            <button mat-menu-item (click)="clearChat()">
              <mat-icon>clear_all</mat-icon>
              Clear Chat
            </button>
            <button mat-menu-item (click)="loadChatHistory()">
              <mat-icon>history</mat-icon>
              Load History
            </button>
            <mat-divider></mat-divider>
            <button mat-menu-item (click)="exportChat()">
              <mat-icon>download</mat-icon>
              Export Chat
            </button>
          </mat-menu>
        </div>
      </mat-card-header>

      <mat-card-content>
        <!-- Chat Messages Container -->
        <div class="chat-container" #chatContainer>
          <div class="messages-area">
            <!-- Welcome Message -->
            <div *ngIf="messages.length === 0" class="welcome-message">
              <mat-icon class="welcome-icon">chat</mat-icon>
              <h3>Welcome to your AI Assistant!</h3>
              <p>I can help you find information from your uploaded documents.</p>
              <p class="welcome-hint">Try asking questions like:</p>
              <ul class="example-questions">
                <li>"What is the main topic of the documents?"</li>
                <li>"Can you summarize the key points?"</li>
                <li>"Tell me about [specific topic]"</li>
              </ul>
            </div>

            <!-- Chat Messages -->
            <div *ngFor="let message of messages; trackBy: trackByMessage" class="message-wrapper">
              <!-- User Message -->
              <div class="message user-message">
                <div class="message-avatar">
                  <mat-icon>person</mat-icon>
                </div>
                <div class="message-content">
                  <div class="message-text">{{ message.message }}</div>
                  <div class="message-time">{{ formatTime(message.timestamp) }}</div>
                </div>
              </div>

              <!-- Bot Response -->
              <div class="message bot-message">
                <div class="message-avatar">
                  <mat-icon>smart_toy</mat-icon>
                </div>
                <div class="message-content">
                  <div class="message-text" [innerHTML]="formatBotResponse(message.response)"></div>
                  <div class="message-time">{{ formatTime(message.timestamp) }}</div>
                </div>
              </div>
            </div>

            <!-- Typing Indicator -->
            <div *ngIf="isTyping" class="message bot-message typing">
              <div class="message-avatar">
                <mat-icon>smart_toy</mat-icon>
              </div>
              <div class="message-content">
                <div class="typing-indicator">
                  <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  <span class="typing-text">AI is thinking...</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Input Area -->
        <div class="input-area">
          <mat-form-field class="message-input" appearance="outline">
            <mat-label>Type your message...</mat-label>
            <input 
              matInput 
              [(ngModel)]="currentMessage"
              (keydown.enter)="sendMessage()"
              [disabled]="isTyping || !chatbotId"
              #messageInput>
            <button 
              mat-icon-button 
              matSuffix 
              (click)="sendMessage()"
              [disabled]="isTyping || !currentMessage.trim() || !chatbotId"
              color="primary">
              <mat-icon>send</mat-icon>
            </button>
          </mat-form-field>
        </div>

        <!-- Status Bar -->
        <div class="status-bar" *ngIf="!chatbotId">
          <mat-icon color="warn">warning</mat-icon>
          <span>Please select a chatbot to start chatting</span>
        </div>
      </mat-card-content>
    </mat-card>
  `,
  styles: [`
    .chat-card {
      max-width: 800px;
      margin: 16px auto;
      height: 600px;
      display: flex;
      flex-direction: column;
    }

    .chat-card mat-card-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      padding: 0;
    }

    .header-actions {
      margin-left: auto;
    }

    .chat-container {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      padding: 16px;
    }

    .messages-area {
      flex: 1;
      overflow-y: auto;
      padding-right: 8px;
    }

    .messages-area::-webkit-scrollbar {
      width: 6px;
    }

    .messages-area::-webkit-scrollbar-track {
      background: #f1f1f1;
      border-radius: 3px;
    }

    .messages-area::-webkit-scrollbar-thumb {
      background: #c1c1c1;
      border-radius: 3px;
    }

    .welcome-message {
      text-align: center;
      padding: 40px 20px;
      color: #666;
    }

    .welcome-icon {
      font-size: 64px;
      width: 64px;
      height: 64px;
      color: #3f51b5;
      margin-bottom: 16px;
    }

    .welcome-message h3 {
      margin: 16px 0;
      color: #333;
    }

    .welcome-hint {
      margin: 24px 0 8px 0;
      font-weight: 500;
    }

    .example-questions {
      text-align: left;
      display: inline-block;
      margin: 8px 0;
    }

    .example-questions li {
      margin: 4px 0;
      font-style: italic;
    }

    .message-wrapper {
      margin-bottom: 24px;
    }

    .message {
      display: flex;
      margin-bottom: 8px;
      animation: fadeIn 0.3s ease-in;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .message-avatar {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-right: 12px;
      flex-shrink: 0;
    }

    .user-message .message-avatar {
      background-color: #3f51b5;
      color: white;
    }

    .bot-message .message-avatar {
      background-color: #4caf50;
      color: white;
    }

    .message-content {
      flex: 1;
      min-width: 0;
    }

    .message-text {
      background: #f5f5f5;
      border-radius: 18px;
      padding: 12px 16px;
      margin-bottom: 4px;
      word-wrap: break-word;
      line-height: 1.4;
    }

    .user-message .message-text {
      background: #3f51b5;
      color: white;
      margin-left: auto;
      max-width: 80%;
    }

    .bot-message .message-text {
      background: #f5f5f5;
      color: #333;
      max-width: 85%;
    }

    .message-time {
      font-size: 12px;
      color: #666;
      padding: 0 16px;
    }

    .user-message .message-time {
      text-align: right;
    }

    .typing-indicator {
      display: flex;
      align-items: center;
      padding: 12px 16px;
    }

    .typing-dots {
      display: flex;
      margin-right: 8px;
    }

    .typing-dots span {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background-color: #666;
      margin: 0 2px;
      animation: typing 1.4s infinite;
    }

    .typing-dots span:nth-child(2) {
      animation-delay: 0.2s;
    }

    .typing-dots span:nth-child(3) {
      animation-delay: 0.4s;
    }

    @keyframes typing {
      0%, 60%, 100% {
        transform: scale(0.8);
        opacity: 0.5;
      }
      30% {
        transform: scale(1);
        opacity: 1;
      }
    }

    .typing-text {
      font-style: italic;
      color: #666;
      font-size: 14px;
    }

    .input-area {
      padding: 16px;
      border-top: 1px solid #eee;
      background: #fafafa;
    }

    .message-input {
      width: 100%;
    }

    .status-bar {
      padding: 8px 16px;
      background: #fff3cd;
      border-top: 1px solid #ffeaa7;
      display: flex;
      align-items: center;
      gap: 8px;
      color: #856404;
      font-size: 14px;
    }

    /* Responsive Design */
    @media (max-width: 600px) {
      .chat-card {
        margin: 8px;
        height: calc(100vh - 100px);
      }

      .user-message .message-text,
      .bot-message .message-text {
        max-width: 90%;
      }

      .welcome-message {
        padding: 20px 16px;
      }

      .welcome-icon {
        font-size: 48px;
        width: 48px;
        height: 48px;
      }
    }
  `]
})
export class ChatInterfaceComponent implements AfterViewChecked {
  @Input() chatbotId: string = '';
  @ViewChild('chatContainer') chatContainer!: ElementRef;
  @ViewChild('messageInput') messageInput!: ElementRef;

  messages: ChatMessage[] = [];
  currentMessage: string = '';
  isTyping: boolean = false;
  private shouldScrollToBottom = false;

  constructor(
    private http: HttpClient,
    private authService: AuthService,
    private snackBar: MatSnackBar
  ) {}

  ngAfterViewChecked() {
    if (this.shouldScrollToBottom) {
      this.scrollToBottom();
      this.shouldScrollToBottom = false;
    }
  }

  ngOnChanges() {
    if (this.chatbotId) {
      this.clearChat();
      this.loadChatHistory();
    }
  }

  sendMessage() {
    if (!this.currentMessage.trim() || this.isTyping || !this.chatbotId) {
      return;
    }

    const message = this.currentMessage.trim();
    this.currentMessage = '';

    // Add user message
    const chatMessage: ChatMessage = {
      message: message,
      response: '',
      timestamp: new Date().toISOString(),
      isUser: true,
      isBot: false
    };

    this.messages.push(chatMessage);
    this.shouldScrollToBottom = true;
    this.isTyping = true;

    // Send to backend
    const token = this.authService.getToken();
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);

    this.http.post<any>(`http://localhost:5000/api/chat/${this.chatbotId}/query`, {
      message: message
    }, { headers }).subscribe({
      next: (response) => {
        chatMessage.response = response.response || response.message || 'Sorry, I couldn\'t generate a response.';
        chatMessage.isBot = true;
        this.isTyping = false;
        this.shouldScrollToBottom = true;
        
        // Focus input for next message
        setTimeout(() => {
          this.messageInput.nativeElement.focus();
        }, 100);
      },
      error: (error) => {
        console.error('Chat error:', error);
        chatMessage.response = 'Sorry, I encountered an error while processing your message. Please try again.';
        chatMessage.isBot = true;
        this.isTyping = false;
        this.shouldScrollToBottom = true;
        
        this.snackBar.open(
          error.error?.message || 'Failed to send message', 
          'Close', 
          { duration: 5000 }
        );
      }
    });
  }

  loadChatHistory() {
    if (!this.chatbotId) return;

    const token = this.authService.getToken();
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);

    this.http.get<any>(`http://localhost:5000/api/chat/${this.chatbotId}/history`, { headers })
      .subscribe({
        next: (response) => {
          const queries: ChatQuery[] = response.queries || [];
          this.messages = queries.map(query => ({
            id: query.id,
            message: query.message,
            response: query.response,
            timestamp: query.created_at,
            isUser: true,
            isBot: true
          }));
          this.shouldScrollToBottom = true;
        },
        error: (error) => {
          console.error('Failed to load chat history:', error);
        }
      });
  }

  clearChat() {
    this.messages = [];
    this.currentMessage = '';
    this.isTyping = false;
  }

  exportChat() {
    if (this.messages.length === 0) {
      this.snackBar.open('No messages to export', 'Close', { duration: 3000 });
      return;
    }

    const chatData = this.messages.map(msg => ({
      timestamp: msg.timestamp,
      user: msg.message,
      assistant: msg.response
    }));

    const blob = new Blob([JSON.stringify(chatData, null, 2)], { 
      type: 'application/json' 
    });
    
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat-export-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    window.URL.revokeObjectURL(url);

    this.snackBar.open('Chat exported successfully', 'Close', { duration: 3000 });
  }

  formatTime(timestamp: string): string {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  formatBotResponse(response: string): string {
    // Convert markdown-like formatting to HTML
    return response
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>')
      .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
  }

  trackByMessage(index: number, message: ChatMessage): string {
    return message.id || `${index}-${message.timestamp}`;
  }

  private scrollToBottom(): void {
    try {
      const container = this.chatContainer.nativeElement;
      container.scrollTop = container.scrollHeight;
    } catch (err) {
      console.error('Error scrolling to bottom:', err);
    }
  }
}