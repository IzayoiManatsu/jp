import { IsOptional, IsString, IsUUID } from 'class-validator';

export class CreateSessionDto {
  @IsOptional()
  @IsString()
  title?: string;
}

export class SendMessageDto {
  @IsString()
  content: string;

  @IsOptional()
  @IsString()
  model?: string;
}