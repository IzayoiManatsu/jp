import { Module } from '@nestjs/common';
import { AuthModule } from '../auth/auth.module';
import { UniversitiesService } from './universities.service';
import { UniversitiesController } from './universities.controller';

@Module({
  imports: [AuthModule],
  providers: [UniversitiesService],
  controllers: [UniversitiesController],
})
export class UniversitiesModule {}