import { Module } from '@nestjs/common';
import { HttpModule } from '@nestjs/axios';
import { DocumentsService } from './documents.service';
import { DocumentsController } from './documents.controller';

@Module({
  imports: [HttpModule],
  providers: [DocumentsService],
  controllers: [DocumentsController],
})
export class DocumentsModule {}