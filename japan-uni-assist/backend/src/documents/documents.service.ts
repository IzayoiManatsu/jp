import { Injectable } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { firstValueFrom } from 'rxjs';
import { PrismaService } from '../prisma.service';

const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://localhost:8000';

@Injectable()
export class DocumentsService {
  constructor(private http: HttpService, private prisma: PrismaService) {}

  async searchDocuments(query: string, topK = 5) {
    const { data } = await firstValueFrom(
      this.http.post(`${AI_SERVICE_URL}/rag/query`, { query, top_k: topK }),
    );
    return data;
  }

  async addDocument(title: string, content: string, sourceType: string, sourceUrl?: string) {
    const { data } = await firstValueFrom(
      this.http.post(`${AI_SERVICE_URL}/rag/documents`, null, {
        params: { title, content, source_type: sourceType, source_url: sourceUrl },
      }),
    );
    return data;
  }

  async listDocuments() {
    return this.prisma.document.findMany({
      orderBy: { createdAt: 'desc' },
      take: 100,
    });
  }
}