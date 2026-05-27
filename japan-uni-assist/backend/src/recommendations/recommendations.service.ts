import { Injectable } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { firstValueFrom } from 'rxjs';
import { PrismaService } from '../prisma.service';

const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://localhost:8000';

@Injectable()
export class RecommendationsService {
  constructor(private http: HttpService, private prisma: PrismaService) {}

  async generateRecommendation(userId: string, profileData: any) {
    const profile = await this.prisma.studentProfile.create({
      data: { ...profileData, userId },
    });

    const { data } = await firstValueFrom(
      this.http.post(`${AI_SERVICE_URL}/recommend`, {
        gpa: profile.gpa,
        english_type: profile.englishType,
        english_score: profile.englishScore,
        jlpt_level: profile.jlptLevel,
        bachelor_school: profile.bachelorSchool,
        bachelor_major: profile.bachelorMajor,
        budget_yen: profile.budgetYen,
        target_major: profile.targetMajor,
      }),
    );

    const saved = await Promise.all(
      data.recommendations.map((rec: any) =>
        this.prisma.recommendation.create({
          data: {
            userId,
            profileId: profile.id,
            category: rec.category,
            universityId: rec.university_name,
            reason: rec.reason,
            matchScore: rec.match_score,
            confidence: rec.confidence,
          },
        }),
      ),
    );

    return { profile, recommendations: data.recommendations, model_used: data.model_used };
  }

  async getRecommendations(userId: string) {
    return this.prisma.recommendation.findMany({
      where: { userId },
      orderBy: { createdAt: 'desc' },
    });
  }
}