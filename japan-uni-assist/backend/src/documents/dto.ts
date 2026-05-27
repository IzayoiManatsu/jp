import { IsString, IsOptional, IsNumber, Min } from 'class-validator';

export class SearchDocumentsDto {
  @IsString()
  query: string;

  @IsOptional()
  @IsNumber()
  @Min(1)
  topK?: number;
}

export class AddDocumentDto {
  @IsString()
  title: string;

  @IsString()
  content: string;

  @IsString()
  sourceType: string;

  @IsOptional()
  @IsString()
  sourceUrl?: string;
}