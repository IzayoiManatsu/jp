import { Module } from '@nestjs/common';
import { HttpModule } from '@nestjs/axios';
import { AuthModule } from '../auth/auth.module';
import { DocumentsService } from './documents.service';
import { DocumentsController } from './documents.controller';

@Module({
  imports: [HttpModule, AuthModule],
  providers: [DocumentsService],
  controllers: [DocumentsController],
})
export class DocumentsModule {}