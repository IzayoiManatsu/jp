import Link from 'next/link';
import { GraduationCap, MessageSquare, ArrowRight } from 'lucide-react';

export default function HomePage() {
  const features = [
    {
      title: 'AI择校推荐',
      desc: '输入你的GPA、语言成绩和背景，AI为你智能匹配冲刺校、稳妥校和保底校。',
      icon: GraduationCap,
      href: '/recommend',
      color: 'bg-blue-50 text-blue-600',
    },
    {
      title: 'AI聊天顾问',
      desc: '多轮对话，上下文记忆，流式输出。随时咨询日本留学相关问题。',
      icon: MessageSquare,
      href: '/chat',
      color: 'bg-green-50 text-green-600',
    },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 py-12">
      <section className="text-center mb-16">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          AI日本考学推荐系统
        </h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          基于大语言模型的日本大学院择校推荐与留学顾问平台。
          支持 OpenAI、Claude、DeepSeek、Gemini、火山引擎多模型切换。
        </p>
      </section>

      <section className="grid md:grid-cols-2 gap-6">
        {features.map((f) => {
          const Icon = f.icon;
          return (
            <Link
              key={f.href}
              href={f.href}
              className="card hover:shadow-md transition group"
            >
              <div className={`w-12 h-12 rounded-lg ${f.color} flex items-center justify-center mb-4`}>
                <Icon className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-semibold mb-2 group-hover:text-primary-600 transition">
                {f.title}
              </h3>
              <p className="text-gray-600 mb-4">{f.desc}</p>
              <span className="inline-flex items-center text-sm font-medium text-primary-600">
                立即体验 <ArrowRight className="w-4 h-4 ml-1" />
              </span>
            </Link>
          );
        })}
      </section>

      <section className="mt-16 card">
        <h2 className="text-2xl font-bold mb-4">支持的AI模型</h2>
        <div className="flex flex-wrap gap-3">
          {['OpenAI GPT-4o', 'Claude Sonnet 4', 'DeepSeek Chat', 'Gemini 1.5 Pro', '火山引擎'].map((m) => (
            <span key={m} className="px-3 py-1.5 bg-gray-100 rounded-full text-sm text-gray-700">
              {m}
            </span>
          ))}
        </div>
      </section>
    </div>
  );
}