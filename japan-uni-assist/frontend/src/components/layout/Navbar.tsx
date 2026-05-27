"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { GraduationCap, MessageSquare, Search, Home, User } from 'lucide-react';
import { useEffect, useState } from 'react';

export default function Navbar() {
  const pathname = usePathname();
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    setToken(localStorage.getItem('token'));
  }, []);

  const nav = [
    { href: '/', label: '首页', icon: Home },
    { href: '/recommend', label: '择校推荐', icon: GraduationCap },
    { href: '/chat', label: 'AI顾问', icon: MessageSquare },
    { href: '/knowledge', label: '知识库', icon: Search },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        <Link href="/" className="text-xl font-bold text-primary-700 flex items-center gap-2">
          <GraduationCap className="w-6 h-6" />
          AI日本考学
        </Link>
        <div className="flex items-center gap-1">
          {nav.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition ${
                  active
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
              >
                <Icon className="w-4 h-4" />
                {item.label}
              </Link>
            );
          })}
        </div>
        <div className="flex items-center gap-2">
          {token ? (
            <button
              onClick={() => {
                localStorage.removeItem('token');
                setToken(null);
                window.location.reload();
              }}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              退出
            </button>
          ) : (
            <Link
              href="/login"
              className="flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-primary-700 hover:bg-primary-50 rounded-lg transition"
            >
              <User className="w-4 h-4" />
              登录
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}