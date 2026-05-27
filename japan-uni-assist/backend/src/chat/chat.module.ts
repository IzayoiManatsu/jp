import { Module } from '@nestjs/common';
import { HttpModule } from '@nestjs/axios';
import { ChatService } from './chat.service';
import { ChatController } from './chat.controller';

@Module({
  imports: [HttpModule],
  providers: [ChatService],
  controllers: [ChatController],
})
export class ChatModule {}