import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma.service';

@Injectable()
export class UniversitiesService {
  constructor(private prisma: PrismaService) {}

  async list() {
    return this.prisma.university.findMany({
      include: { programs: true },
      orderBy: { ranking: 'asc' },
    });
  }

  async getById(id: string) {
    return this.prisma.university.findUnique({
      where: { id },
      include: { programs: true, professors: true },
    });
  }

  async create(data: any) {
    return this.prisma.university.create({ data });
  }
}