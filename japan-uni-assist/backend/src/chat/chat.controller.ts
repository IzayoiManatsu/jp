import { Controller, Post, Get, Body, Param, UseGuards, Request, Res } from '@nestjs/common';
import { Response } from 'express';
import { JwtAuthGuard } from '../common/jwt-auth.guard';
import { ChatService } from './chat.service';
import { CreateSessionDto, SendMessageDto } from './dto';

@Controller('chat')
export class ChatController {
  constructor(private chatService: ChatService) {}

  @UseGuards(JwtAuthGuard)
  @Post('sessions')
  async createSession(@Request() req, @Body() dto: CreateSessionDto) {
    return this.chatService.createSession(req.user.sub, dto.title);
  }

  @UseGuards(JwtAuthGuard)
  @Get('sessions')
  async listSessions(@Request() req) {
    return this.chatService.getSessions(req.user.sub);
  }

  @UseGuards(JwtAuthGuard)
  @Get('sessions/:id/messages')
  async getMessages(@Param('id') sessionId: string) {
    return this.chatService.getMessages(sessionId);
  }

  @UseGuards(JwtAuthGuard)
  @Post('sessions/:id/messages')
  async sendMessage(
    @Param('id') sessionId: string,
    @Body() dto: SendMessageDto,
  ) {
    return this.chatService.sendMessage(sessionId, dto.content, dto.model);
  }

  @UseGuards(JwtAuthGuard)
  @Post('sessions/:id/messages/stream')
  async streamMessage(
    @Param('id') sessionId: string,
    @Body() dto: SendMessageDto,
    @Res() res: Response,
  ) {
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');

    try {
      const stream = await this.chatService.streamMessage(sessionId, dto.content, dto.model);
      let fullContent = '';

      stream.on('data', (chunk: Buffer) => {
        const text = chunk.toString();
        res.write(text);

        // Parse SSE chunks to accumulate full response
        const lines = text.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6).trim();
            if (dataStr === '[DONE]') continue;
            try {
              const data = JSON.parse(dataStr);
              if (data.content) fullContent += data.content;
            } catch {
              // ignore parse errors for partial chunks
            }
          }
        }
      });

      stream.on('end', async () => {
        try {
          await this.chatService.saveAssistantMessage(sessionId, fullContent, dto.model);
        } catch (e) {
          // Log but don't fail the stream to client
          console.error('Failed to save assistant message:', e);
        }
        res.end();
      });

      stream.on('error', (err: Error) => {
        res.write(`data: ${JSON.stringify({ error: err.message })}\n\n`);
        res.end();
      });
    } catch (e: any) {
      res.write(`data: ${JSON.stringify({ error: e.message })}\n\n`);
      res.end();
    }
  }
}