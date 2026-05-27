import { Controller, Get, Post, Body, Param, UseGuards } from '@nestjs/common';
import { JwtAuthGuard } from '../common/jwt-auth.guard';
import { UniversitiesService } from './universities.service';

@Controller('universities')
export class UniversitiesController {
  constructor(private universitiesService: UniversitiesService) {}

  @Get()
  async list() {
    return this.universitiesService.list();
  }

  @Get(':id')
  async getById(@Param('id') id: string) {
    return this.universitiesService.getById(id);
  }

  @UseGuards(JwtAuthGuard)
  @Post()
  async create(@Body() body: any) {
    return this.universitiesService.create(body);
  }
}