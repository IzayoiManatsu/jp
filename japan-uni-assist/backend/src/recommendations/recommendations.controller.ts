import { Controller, Post, Get, Body, UseGuards, Request } from '@nestjs/common';
import { JwtAuthGuard } from '../common/jwt-auth.guard';
import { RecommendationsService } from './recommendations.service';
import { RecommendDto } from './dto';

@Controller('recommendations')
export class RecommendationsController {
  constructor(private service: RecommendationsService) {}

  @UseGuards(JwtAuthGuard)
  @Post()
  async create(@Request() req, @Body() dto: RecommendDto) {
    return this.service.generateRecommendation(req.user.sub, dto);
  }

  @UseGuards(JwtAuthGuard)
  @Get()
  async list(@Request() req) {
    return this.service.getRecommendations(req.user.sub);
  }
}