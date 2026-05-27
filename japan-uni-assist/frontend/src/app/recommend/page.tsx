"use client";

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { api } from '@/lib/api';
import { Loader2, Target, Shield, Zap } from 'lucide-react';
import type { RecommendItem } from '@/types';

const schema = z.object({
  gpa: z.coerce.number().min(0).max(4),
  english_type: z.enum(['TOEFL', 'IELTS']),
  english_score: z.coerce.number().min(0),
  jlpt_level: z.enum(['N1', 'N2', 'N3', 'N4', 'N5']).optional(),
  bachelor_school: z.string().min(1),
  bachelor_major: z.string().min(1),
  budget_yen: z.coerce.number().min(0).optional(),
  target_major: z.string().optional(),
});

type FormData = z.infer<typeof schema>;

export default function RecommendPage() {
  const [result, setResult] = useState<RecommendItem[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    setLoading(true);
    setError('');
    try {
      const res = await api.recommend.submit(data);
      setResult(res.recommendations);
    } catch (e: any) {
      setError(e.message || '推荐失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const categories = {
    REACH: { label: '冲刺校', color: 'border-red-200 bg-red-50', icon: Zap, badge: 'bg-red-100 text-red-700' },
    TARGET: { label: '稳妥校', color: 'border-yellow-200 bg-yellow-50', icon: Target, badge: 'bg-yellow-100 text-yellow-700' },
    SAFETY: { label: '保底校', color: 'border-green-200 bg-green-50', icon: Shield, badge: 'bg-green-100 text-green-700' },
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">AI择校推荐</h1>

      {!result ? (
        <form onSubmit={handleSubmit(onSubmit)} className="card space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">GPA (0-4.0)</label>
              <input type="number" step="0.01" {...register('gpa')} className="w-full border rounded-lg px-3 py-2" />
              {errors.gpa && <p className="text-red-500 text-sm">{errors.gpa.message}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">英语考试类型</label>
              <select {...register('english_type')} className="w-full border rounded-lg px-3 py-2">
                <option value="TOEFL">TOEFL</option>
                <option value="IELTS">IELTS</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">英语成绩</label>
              <input type="number" step="0.1" {...register('english_score')} className="w-full border rounded-lg px-3 py-2" />
              {errors.english_score && <p className="text-red-500 text-sm">{errors.english_score.message}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">JLPT等级</label>
              <select {...register('jlpt_level')} className="w-full border rounded-lg px-3 py-2">
                <option value="">无</option>
                <option value="N1">N1</option>
                <option value="N2">N2</option>
                <option value="N3">N3</option>
                <option value="N4">N4</option>
                <option value="N5">N5</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">本科院校</label>
              <input {...register('bachelor_school')} className="w-full border rounded-lg px-3 py-2" placeholder="如：北京大学" />
              {errors.bachelor_school && <p className="text-red-500 text-sm">{errors.bachelor_school.message}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">本科专业</label>
              <input {...register('bachelor_major')} className="w-full border rounded-lg px-3 py-2" placeholder="如：计算机科学" />
              {errors.bachelor_major && <p className="text-red-500 text-sm">{errors.bachelor_major.message}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">目标专业（可选）</label>
              <input {...register('target_major')} className="w-full border rounded-lg px-3 py-2" placeholder="默认与本科相同" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">年预算（日元，可选）</label>
              <input type="number" {...register('budget_yen')} className="w-full border rounded-lg px-3 py-2" placeholder="如：1000000" />
            </div>
          </div>

          {error && <p className="text-red-500 text-sm">{error}</p>}

          <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2">
            {loading && <Loader2 className="w-4 h-4 animate-spin" />}
            生成推荐
          </button>
        </form>
      ) : (
        <div className="space-y-8">
          <button onClick={() => setResult(null)} className="btn-secondary">重新填写</button>
          {(Object.keys(categories) as Array<keyof typeof categories>).map((cat) => {
            const items = result.filter((r) => r.category === cat);
            const config = categories[cat];
            const Icon = config.icon;
            return (
              <div key={cat}>
                <div className="flex items-center gap-2 mb-4">
                  <Icon className="w-5 h-5" />
                  <h2 className="text-lg font-bold">{config.label}</h2>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${config.badge}`}>{items.length}所</span>
                </div>
                <div className="grid md:grid-cols-3 gap-4">
                  {items.map((item, idx) => (
                    <div key={idx} className={`card border-2 ${config.color}`}>
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-semibold">{item.university_name}</h3>
                        <span className="text-sm font-bold text-primary-600">{item.match_score}%</span>
                      </div>
                      <p className="text-sm text-gray-500 mb-1">{item.university_name_jp}</p>
                      <p className="text-sm text-gray-700 mb-3">{item.program_name}</p>
                      <p className="text-sm text-gray-600 mb-3 line-clamp-3">{item.reason}</p>
                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <span>置信度: {(item.confidence * 100).toFixed(0)}%</span>
                        {item.location && <span>{item.location}</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}