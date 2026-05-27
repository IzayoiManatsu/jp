import { Injectable } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { firstValueFrom } from 'rxjs';
import { PrismaService } from '../prisma.service';

const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://localhost:8000';

@Injectable()
export class ChatService {
  constructor(private http: HttpService, private prisma: PrismaService) {}

  async createSession(userId: string, title?: string) {
    return this.prisma.chatSession.create({
      data: { userId, title: title || '新会话' },
    });
  }

  async getSessions(userId: string) {
    return this.prisma.chatSession.findMany({
      where: { userId },
      orderBy: { updatedAt: 'desc' },
    });
  }

  async getMessages(sessionId: string) {
    return this.prisma.chatMessage.findMany({
      where: { sessionId },
      orderBy: { createdAt: 'asc' },
    });
  }

  async sendMessage(sessionId: string, content: string, model?: string) {
    await this.prisma.chatMessage.create({
      data: { sessionId, role: 'user', content },
    });

    const history = await this.prisma.chatMessage.findMany({
      where: { sessionId },
      orderBy: { createdAt: 'asc' },
      take: 20,
    });

    const messages = history.map((m) => ({ role: m.role, content: m.content }));

    const { data } = await firstValueFrom(
      this.http.post(`${AI_SERVICE_URL}/chat`, {
        messages,
        model: model || 'gpt-4o',
        temperature: 0.7,
        stream: false,
      }),
    );

    await this.prisma.chatMessage.create({
      data: {
        sessionId,
        role: 'assistant',
        content: data.content,
        modelUsed: data.model,
        tokenUsage: data.usage,
      },
    });

    await this.prisma.chatSession.update({
      where: { id: sessionId },
      data: { updatedAt: new Date() },
    });

    return data;
  }

  async streamMessage(sessionId: string, content: string, model?: string) {
    await this.prisma.chatMessage.create({
      data: { sessionId, role: 'user', content },
    });

    const history = await this.prisma.chatMessage.findMany({
      where: { sessionId },
      orderBy: { createdAt: 'asc' },
      take: 20,
    });

    const messages = history.map((m) => ({ role: m.role, content: m.content }));

    const response = await firstValueFrom(
      this.http.post(
        `${AI_SERVICE_URL}/chat/stream`,
        { messages, model: model || 'gpt-4o', temperature: 0.7, stream: true },
        { responseType: 'stream' },
      ),
    );

    return response.data;
  }

  async saveAssistantMessage(sessionId: string, content: string, model?: string) {
    await this.prisma.chatMessage.create({
      data: {
        sessionId,
        role: 'assistant',
        content,
        modelUsed: model || 'unknown',
      },
    });

    await this.prisma.chatSession.update({
      where: { id: sessionId },
      data: { updatedAt: new Date() },
    });
  }
}