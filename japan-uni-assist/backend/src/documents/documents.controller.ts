import { Controller, Post, Get, Body, Query, UseGuards } from '@nestjs/common';
import { JwtAuthGuard } from '../common/jwt-auth.guard';
import { DocumentsService } from './documents.service';
import { SearchDocumentsDto, AddDocumentDto } from './dto';

@Controller('documents')
export class DocumentsController {
  constructor(private documentsService: DocumentsService) {}

  @UseGuards(JwtAuthGuard)
  @Post('search')
  async search(@Body() dto: SearchDocumentsDto) {
    return this.documentsService.searchDocuments(dto.query, dto.topK);
  }

  @UseGuards(JwtAuthGuard)
  @Post()
  async add(@Body() dto: AddDocumentDto) {
    return this.documentsService.addDocument(dto.title, dto.content, dto.sourceType, dto.sourceUrl);
  }

  @UseGuards(JwtAuthGuard)
  @Get()
  async list() {
    return this.documentsService.listDocuments();
  }
}