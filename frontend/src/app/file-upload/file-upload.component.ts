import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSnackBarModule, MatSnackBar } from '@angular/material/snack-bar';
import { MatCardModule } from '@angular/material/card';
import { MatListModule } from '@angular/material/list';
import { HttpClient, HttpEventType, HttpHeaders } from '@angular/common/http';
import { AuthService } from '../auth.service';

export interface UploadedDocument {
  id: string;
  filename: string;
  original_filename: string;
  file_size: number;
  file_type: string;
  upload_date: string;
  chunk_count: number;
}

@Component({
  selector: 'app-file-upload',
  standalone: true,
  imports: [
    CommonModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatSnackBarModule,
    MatCardModule,
    MatListModule
  ],
  template: `
    <mat-card class="upload-card">
      <mat-card-header>
        <mat-card-title>Document Upload</mat-card-title>
        <mat-card-subtitle>Upload PDF, DOCX, or TXT files to train your chatbot</mat-card-subtitle>
      </mat-card-header>
      
      <mat-card-content>
        <!-- File Drop Zone -->
        <div 
          class="drop-zone"
          [class.dragover]="isDragOver"
          (dragover)="onDragOver($event)"
          (dragleave)="onDragLeave($event)"
          (drop)="onFileDrop($event)"
          (click)="fileInput.click()">
          
          <mat-icon class="upload-icon">cloud_upload</mat-icon>
          <p class="drop-text">
            Drag and drop files here or <span class="link-text">click to browse</span>
          </p>
          <p class="file-types">Supported: PDF, DOCX, TXT (Max 10MB each)</p>
          
          <input 
            #fileInput
            type="file"
            multiple
            accept=".pdf,.docx,.txt"
            (change)="onFileSelect($event)"
            style="display: none;">
        </div>

        <!-- Upload Progress -->
        <div *ngIf="uploadProgress.length > 0" class="upload-progress">
          <h4>Uploading Files</h4>
          <div *ngFor="let progress of uploadProgress" class="progress-item">
            <div class="progress-info">
              <span class="filename">{{ progress.filename }}</span>
              <span class="progress-text">{{ progress.progress }}%</span>
            </div>
            <mat-progress-bar 
              [value]="progress.progress"
              [color]="progress.error ? 'warn' : 'primary'">
            </mat-progress-bar>
            <div *ngIf="progress.error" class="error-message">
              {{ progress.error }}
            </div>
          </div>
        </div>

        <!-- Uploaded Documents List -->
        <div *ngIf="documents.length > 0" class="documents-list">
          <h4>Uploaded Documents ({{ documents.length }})</h4>
          <mat-list>
            <mat-list-item *ngFor="let doc of documents" class="document-item">
              <mat-icon matListItemIcon>description</mat-icon>
              <div matListItemTitle>{{ doc.original_filename }}</div>
              <div matListItemLine>
                {{ formatFileSize(doc.file_size) }} • 
                {{ doc.chunk_count }} chunks • 
                {{ formatDate(doc.upload_date) }}
              </div>
              <button 
                mat-icon-button 
                color="warn"
                (click)="deleteDocument(doc.id)"
                matListItemMeta>
                <mat-icon>delete</mat-icon>
              </button>
            </mat-list-item>
          </mat-list>
        </div>

        <!-- Empty State -->
        <div *ngIf="documents.length === 0 && uploadProgress.length === 0" class="empty-state">
          <mat-icon class="empty-icon">description</mat-icon>
          <p>No documents uploaded yet</p>
          <p class="empty-subtitle">Upload documents to start training your chatbot</p>
        </div>
      </mat-card-content>

      <mat-card-actions>
        <button 
          mat-raised-button 
          color="primary"
          (click)="fileInput.click()"
          [disabled]="isUploading">
          <mat-icon>add</mat-icon>
          Add Files
        </button>
        
        <button 
          mat-button
          (click)="refreshDocuments()"
          [disabled]="isUploading">
          <mat-icon>refresh</mat-icon>
          Refresh
        </button>
      </mat-card-actions>
    </mat-card>
  `,
  styles: [`
    .upload-card {
      max-width: 800px;
      margin: 16px auto;
    }

    .drop-zone {
      border: 2px dashed #ccc;
      border-radius: 8px;
      padding: 40px;
      text-align: center;
      cursor: pointer;
      transition: all 0.3s ease;
      margin-bottom: 24px;
    }

    .drop-zone:hover,
    .drop-zone.dragover {
      border-color: #3f51b5;
      background-color: #f5f5f5;
    }

    .upload-icon {
      font-size: 48px;
      width: 48px;
      height: 48px;
      color: #666;
      margin-bottom: 16px;
    }

    .drop-text {
      font-size: 16px;
      margin: 8px 0;
      color: #333;
    }

    .link-text {
      color: #3f51b5;
      text-decoration: underline;
    }

    .file-types {
      font-size: 14px;
      color: #666;
      margin: 8px 0 0 0;
    }

    .upload-progress {
      margin-bottom: 24px;
    }

    .progress-item {
      margin-bottom: 16px;
    }

    .progress-info {
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;
    }

    .filename {
      font-weight: 500;
    }

    .progress-text {
      color: #666;
      font-size: 14px;
    }

    .error-message {
      color: #f44336;
      font-size: 12px;
      margin-top: 4px;
    }

    .documents-list {
      margin-bottom: 24px;
    }

    .document-item {
      border-bottom: 1px solid #eee;
    }

    .document-item:last-child {
      border-bottom: none;
    }

    .empty-state {
      text-align: center;
      padding: 40px;
      color: #666;
    }

    .empty-icon {
      font-size: 64px;
      width: 64px;
      height: 64px;
      color: #ccc;
      margin-bottom: 16px;
    }

    .empty-subtitle {
      font-size: 14px;
      margin-top: 8px;
    }

    h4 {
      margin: 0 0 16px 0;
      color: #333;
    }
  `]
})
export class FileUploadComponent {
  @Input() chatbotId: string = '';
  @Output() documentsChanged = new EventEmitter<UploadedDocument[]>();

  documents: UploadedDocument[] = [];
  uploadProgress: any[] = [];
  isDragOver = false;
  isUploading = false;

  constructor(
    private http: HttpClient,
    private authService: AuthService,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit() {
    if (this.chatbotId) {
      this.loadDocuments();
    }
  }

  onDragOver(event: DragEvent) {
    event.preventDefault();
    this.isDragOver = true;
  }

  onDragLeave(event: DragEvent) {
    event.preventDefault();
    this.isDragOver = false;
  }

  onFileDrop(event: DragEvent) {
    event.preventDefault();
    this.isDragOver = false;
    
    const files = event.dataTransfer?.files;
    if (files) {
      this.handleFiles(Array.from(files));
    }
  }

  onFileSelect(event: any) {
    const files = event.target.files;
    if (files) {
      this.handleFiles(Array.from(files));
    }
    // Clear the input
    event.target.value = '';
  }

  handleFiles(files: File[]) {
    // Validate files
    const validFiles = files.filter(file => this.validateFile(file));
    
    if (validFiles.length === 0) {
      this.snackBar.open('No valid files selected', 'Close', { duration: 3000 });
      return;
    }

    // Upload files
    validFiles.forEach(file => this.uploadFile(file));
  }

  validateFile(file: File): boolean {
    // Check file type
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    const allowedExtensions = ['.pdf', '.docx', '.txt'];
    
    const hasValidType = allowedTypes.includes(file.type);
    const hasValidExtension = allowedExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
    
    if (!hasValidType && !hasValidExtension) {
      this.snackBar.open(`Invalid file type: ${file.name}. Only PDF, DOCX, and TXT files are allowed.`, 'Close', { duration: 5000 });
      return false;
    }

    // Check file size (10MB limit)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      this.snackBar.open(`File too large: ${file.name}. Maximum size is 10MB.`, 'Close', { duration: 5000 });
      return false;
    }

    return true;
  }

  uploadFile(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('chatbot_id', this.chatbotId);

    // Add progress tracking
    const progressItem = {
      filename: file.name,
      progress: 0,
      error: null
    };
    this.uploadProgress.push(progressItem);
    this.isUploading = true;

    const token = this.authService.getToken();
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);

    this.http.post('http://localhost:5000/api/documents/upload', formData, {
      headers,
      reportProgress: true,
      observe: 'events'
    }).subscribe({
      next: (event) => {
        if (event.type === HttpEventType.UploadProgress && event.total) {
          progressItem.progress = Math.round(100 * event.loaded / event.total);
        } else if (event.type === HttpEventType.Response) {
          progressItem.progress = 100;
          this.snackBar.open(`${file.name} uploaded successfully`, 'Close', { duration: 3000 });
          
          // Remove from progress and reload documents
          setTimeout(() => {
            this.uploadProgress = this.uploadProgress.filter(p => p !== progressItem);
            if (this.uploadProgress.length === 0) {
              this.isUploading = false;
            }
            this.loadDocuments();
          }, 1000);
        }
      },
      error: (error) => {
        progressItem.error = error.error?.message || 'Upload failed';
        this.snackBar.open(`Failed to upload ${file.name}: ${progressItem.error}`, 'Close', { duration: 5000 });
        
        setTimeout(() => {
          this.uploadProgress = this.uploadProgress.filter(p => p !== progressItem);
          if (this.uploadProgress.length === 0) {
            this.isUploading = false;
          }
        }, 3000);
      }
    });
  }

  loadDocuments() {
    if (!this.chatbotId) return;

    const token = this.authService.getToken();
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);

    this.http.get<any>(`http://localhost:5000/api/documents/${this.chatbotId}`, { headers })
      .subscribe({
        next: (response) => {
          this.documents = response.documents || [];
          this.documentsChanged.emit(this.documents);
        },
        error: (error) => {
          console.error('Failed to load documents:', error);
          this.snackBar.open('Failed to load documents', 'Close', { duration: 3000 });
        }
      });
  }

  deleteDocument(documentId: string) {
    if (!confirm('Are you sure you want to delete this document?')) {
      return;
    }

    const token = this.authService.getToken();
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);

    this.http.delete(`http://localhost:5000/api/documents/${documentId}`, { headers })
      .subscribe({
        next: () => {
          this.snackBar.open('Document deleted successfully', 'Close', { duration: 3000 });
          this.loadDocuments();
        },
        error: (error) => {
          console.error('Failed to delete document:', error);
          this.snackBar.open('Failed to delete document', 'Close', { duration: 3000 });
        }
      });
  }

  refreshDocuments() {
    this.loadDocuments();
  }

  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
}