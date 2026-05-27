import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma.service';

@Injectable()
export class UsersService {
  constructor(private prisma: PrismaService) {}

  async findById(id: string) {
    return this.prisma.user.findUnique({
      where: { id },
      select: { id: true, email: true, name: true, createdAt: true },
    });
  }

  async getProfiles(userId: string) {
    return this.prisma.studentProfile.findMany({
      where: { userId },
      orderBy: { createdAt: 'desc' },
    });
  }

  async createProfile(userId: string, data: any) {
    return this.prisma.studentProfile.create({
      data: { ...data, userId },
    });
  }
}