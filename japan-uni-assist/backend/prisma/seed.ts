import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
  const data = [
    {
      name: '东京大学',
      nameJp: '東京大学',
      location: '东京',
      ranking: 1,
      type: '国立',
      tuitionYen: 535800,
      website: 'https://www.u-tokyo.ac.jp',
      programs: [
        { name: '情報理工学系研究科', degree: '修士', language: '日语/英语', examType: '一般入试' },
        { name: '工学系研究科', degree: '修士', language: '日语', examType: '一般入试' },
      ] as const,
    },
    {
      name: '京都大学',
      nameJp: '京都大学',
      location: '京都',
      ranking: 2,
      type: '国立',
      tuitionYen: 535800,
      website: 'https://www.kyoto-u.ac.jp',
      programs: [
        { name: '情報学研究科', degree: '修士', language: '日语/英语', examType: '一般入试' },
        { name: '工学研究科', degree: '修士', language: '日语', examType: '一般入试' },
      ] as const,
    },
    {
      name: '大阪大学',
      nameJp: '大阪大学',
      location: '大阪',
      ranking: 3,
      type: '国立',
      tuitionYen: 535800,
      website: 'https://www.osaka-u.ac.jp',
      programs: [
        { name: '情報科学研究科', degree: '修士', language: '日语', examType: '一般入试' },
        { name: '基礎工学研究科', degree: '修士', language: '日语', examType: '一般入试' },
      ] as const,
    },
    {
      name: '早稻田大学',
      nameJp: '早稲田大学',
      location: '东京',
      ranking: 10,
      type: '私立',
      tuitionYen: 1000000,
      website: 'https://www.waseda.jp',
      programs: [
        { name: '基幹理工学研究科', degree: '修士', language: '日语/英语', examType: 'AO入试' },
        { name: '創造理工学研究科', degree: '修士', language: '日语', examType: '一般入试' },
      ] as const,
    },
    {
      name: '东北大学',
      nameJp: '東北大学',
      location: '仙台',
      ranking: 5,
      type: '国立',
      tuitionYen: 535800,
      website: 'https://www.tohoku.ac.jp',
      programs: [
        { name: '情報科学研究科', degree: '修士', language: '日语', examType: '一般入试' },
      ] as const,
    },
    {
      name: '名古屋大学',
      nameJp: '名古屋大学',
      location: '名古屋',
      ranking: 6,
      type: '国立',
      tuitionYen: 535800,
      website: 'https://www.nagoya-u.ac.jp',
      programs: [
        { name: '情報学研究科', degree: '修士', language: '日语', examType: '一般入试' },
      ] as const,
    },
    {
      name: '九州大学',
      nameJp: '九州大学',
      location: '福冈',
      ranking: 7,
      type: '国立',
      tuitionYen: 535800,
      website: 'https://www.kyushu-u.ac.jp',
      programs: [
        { name: 'システム情報科学府', degree: '修士', language: '日语', examType: '一般入试' },
      ] as const,
    },
    {
      name: '北海道大学',
      nameJp: '北海道大学',
      location: '札幌',
      ranking: 8,
      type: '国立',
      tuitionYen: 535800,
      website: 'https://www.hokudai.ac.jp',
      programs: [
        { name: '情報科学研究院', degree: '修士', language: '日语', examType: '一般入试' },
      ] as const,
    },
    {
      name: '庆应义塾大学',
      nameJp: '慶應義塾大学',
      location: '东京',
      ranking: 9,
      type: '私立',
      tuitionYen: 1200000,
      website: 'https://www.keio.ac.jp',
      programs: [
        { name: '理工学研究科', degree: '修士', language: '日语', examType: '一般入试' },
      ] as const,
    },
  ];

  for (const u of data) {
    const existing = await prisma.university.findFirst({ where: { name: u.name } });
    if (!existing) {
      await prisma.university.create({
        data: {
          name: u.name,
          nameJp: u.nameJp,
          location: u.location,
          ranking: u.ranking,
          type: u.type,
          tuitionYen: u.tuitionYen,
          website: u.website,
          programs: { create: u.programs.map((p) => ({ ...p })) },
        },
      });
    }
  }

  console.log('Seed completed');
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });