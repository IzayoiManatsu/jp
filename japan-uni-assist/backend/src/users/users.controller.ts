import { Controller, Get, Post, Body, UseGuards, Request } from '@nestjs/common';
import { JwtAuthGuard } from '../common/jwt-auth.guard';
import { UsersService } from './users.service';

@Controller('users')
export class UsersController {
  constructor(private usersService: UsersService) {}

  @UseGuards(JwtAuthGuard)
  @Get('me')
  async me(@Request() req) {
    return this.usersService.findById(req.user.sub);
  }

  @UseGuards(JwtAuthGuard)
  @Get('profiles')
  async profiles(@Request() req) {
    return this.usersService.getProfiles(req.user.sub);
  }

  @UseGuards(JwtAuthGuard)
  @Post('profiles')
  async createProfile(@Request() req, @Body() body: any) {
    return this.usersService.createProfile(req.user.sub, body);
  }
}