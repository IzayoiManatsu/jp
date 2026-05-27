"use client";

import { useState } from 'react';
import { api } from '@/lib/api';
import { Search, Loader2, ExternalLink } from 'lucide-react';

interface Source {
  title: string;
  source_url?: string;
  content_snippet: string;
  similarity: number;
}

export default function KnowledgePage() {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState('');
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError('');
    try {
      const res = await api.documents.search(query, 5);
      setAnswer(res.answer);
      setSources(res.sources || []);
    } catch (e: any) {
      setError(e.message || '检索失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">RAG知识库检索</h1>

      <div className="flex gap-2 mb-8">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="搜索日本大学、专业、申请要求..."
          className="flex-1 border rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
        <button
          onClick={handleSearch}
          disabled={loading}
          className="btn-primary px-6 flex items-center gap-2"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
          检索
        </button>
      </div>

      {error && <p className="text-red-500 mb-4">{error}</p>}

      {answer && (
        <div className="card mb-6">
          <h2 className="text-lg font-semibold mb-3">AI回答</h2>
          <div className="prose max-w-none text-gray-700 whitespace-pre-wrap">{answer}</div>
        </div>
      )}

      {sources.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-3">参考来源</h2>
          <div className="space-y-3">
            {sources.map((s, i) => (
              <div key={i} className="card py-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium">{s.title}</span>
                  <span className="text-xs text-gray-400">相似度: {(s.similarity * 100).toFixed(1)}%</span>
                </div>
                <p className="text-sm text-gray-600 mb-2">{s.content_snippet}</p>
                {s.source_url && (
                  <a
                    href={s.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center text-sm text-primary-600 hover:underline"
                  >
                    查看原文 <ExternalLink className="w-3 h-3 ml-1" />
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}