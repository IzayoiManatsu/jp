"use client";

import { useState, useEffect, useRef } from 'react';
import { api, streamChat } from '@/lib/api';
import { Send, Loader2, Plus, MessageSquare } from 'lucide-react';
import type { ChatSession, ChatMessage } from '@/types';

export default function ChatPage() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSession, setCurrentSession] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [streamingText, setStreamingText] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.chat.sessions().then(setSessions).catch(() => {});
  }, []);

  useEffect(() => {
    if (currentSession) {
      api.chat.messages(currentSession).then(setMessages).catch(() => {});
    }
  }, [currentSession]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingText]);

  const createSession = async () => {
    const session = await api.chat.createSession();
    setSessions([session, ...sessions]);
    setCurrentSession(session.id);
    setMessages([]);
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const content = input.trim();
    setInput('');
    setLoading(true);
    setStreamingText('');

    if (!currentSession) {
      const session = await api.chat.createSession();
      setSessions([session, ...sessions]);
      setCurrentSession(session.id);
      await sendToSession(session.id, content);
    } else {
      await sendToSession(currentSession, content);
    }
  };

  const sendToSession = async (sessionId: string, content: string) => {
    setMessages((prev) => [
      ...prev,
      { id: Date.now().toString(), role: 'user', content, createdAt: new Date().toISOString() },
    ]);

    let assistantText = '';
    streamChat(
      sessionId,
      content,
      (chunk) => {
        assistantText += chunk;
        setStreamingText(assistantText);
      },
      async () => {
        setLoading(false);
        setStreamingText('');
        const updated = await api.chat.messages(sessionId);
        setMessages(updated);
      },
      (err) => {
        setLoading(false);
        setStreamingText('');
        setMessages((prev) => [
          ...prev,
          { id: Date.now().toString(), role: 'assistant', content: `错误: ${err}`, createdAt: new Date().toISOString() },
        ]);
      }
    );
  };

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <button onClick={createSession} className="btn-primary w-full flex items-center justify-center gap-2">
            <Plus className="w-4 h-4" /> 新建会话
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {sessions.map((s) => (
            <button
              key={s.id}
              onClick={() => setCurrentSession(s.id)}
              className={`w-full text-left px-3 py-2 rounded-lg text-sm flex items-center gap-2 transition ${
                currentSession === s.id ? 'bg-primary-50 text-primary-700' : 'hover:bg-gray-50'
              }`}
            >
              <MessageSquare className="w-4 h-4 shrink-0" />
              <span className="truncate">{s.title}</span>
            </button>
          ))}
        </div>
      </aside>

      <div className="flex-1 flex flex-col bg-gray-50">
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && !streamingText && (
            <div className="text-center text-gray-400 mt-20">
              <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>开始与AI顾问对话</p>
            </div>
          )}
          {messages.map((m) => (
            <div key={m.id} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm ${
                  m.role === 'user'
                    ? 'bg-primary-600 text-white rounded-br-none'
                    : 'bg-white border border-gray-200 rounded-bl-none'
                }`}
              >
                <div className="whitespace-pre-wrap">{m.content}</div>
                {m.modelUsed && (
                  <div className="text-xs opacity-60 mt-2">{m.modelUsed}</div>
                )}
              </div>
            </div>
          ))}
          {streamingText && (
            <div className="flex justify-start">
              <div className="max-w-[80%] px-4 py-3 rounded-2xl text-sm bg-white border border-gray-200 rounded-bl-none">
                <div className="whitespace-pre-wrap">{streamingText}</div>
                <div className="text-xs text-gray-400 mt-2 flex items-center gap-1">
                  <Loader2 className="w-3 h-3 animate-spin" /> 生成中...
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="p-4 bg-white border-t border-gray-200">
          <div className="flex gap-2 max-w-3xl mx-auto">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
              placeholder="输入问题..."
              className="flex-1 border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
              disabled={loading}
            />
            <button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              className="btn-primary px-4 disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}