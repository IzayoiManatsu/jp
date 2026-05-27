import { IsNumber, IsString, IsOptional, IsEnum, Min, Max } from 'class-validator';

export class RecommendDto {
  @IsNumber()
  @Min(0)
  @Max(4)
  gpa: number;

  @IsEnum(['TOEFL', 'IELTS'])
  englishType: string;

  @IsNumber()
  @Min(0)
  englishScore: number;

  @IsOptional()
  @IsEnum(['N1', 'N2', 'N3', 'N4', 'N5'])
  jlptLevel?: string;

  @IsString()
  bachelorSchool: string;

  @IsString()
  bachelorMajor: string;

  @IsOptional()
  @IsNumber()
  @Min(0)
  budgetYen?: number;

  @IsOptional()
  @IsString()
  targetMajor?: string;
}