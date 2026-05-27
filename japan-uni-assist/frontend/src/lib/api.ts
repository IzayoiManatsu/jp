const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';

function getToken() {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('token');
  }
  return null;
}

async function fetchApi(path: string, options: RequestInit = {}) {
  const token = getToken();
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: 'Unknown error' }));
    throw new Error(err.message || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  auth: {
    login: (email: string, password: string) =>
      fetchApi('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
    register: (email: string, password: string, name?: string) =>
      fetchApi('/auth/register', { method: 'POST', body: JSON.stringify({ email, password, name }) }),
  },
  user: {
    me: () => fetchApi('/users/me'),
    profiles: () => fetchApi('/users/profiles'),
    createProfile: (data: any) => fetchApi('/users/profiles', { method: 'POST', body: JSON.stringify(data) }),
  },
  recommend: {
    submit: (data: any) => fetchApi('/recommendations', { method: 'POST', body: JSON.stringify(data) }),
    list: () => fetchApi('/recommendations'),
  },
  chat: {
    sessions: () => fetchApi('/chat/sessions'),
    createSession: (title?: string) => fetchApi('/chat/sessions', { method: 'POST', body: JSON.stringify({ title }) }),
    messages: (sessionId: string) => fetchApi(`/chat/sessions/${sessionId}/messages`),
    send: (sessionId: string, content: string, model?: string) =>
      fetchApi(`/chat/sessions/${sessionId}/messages`, { method: 'POST', body: JSON.stringify({ content, model }) }),
    sendStream: (sessionId: string, content: string, model?: string) => {
      const token = getToken();
      return fetch(`${API_URL}/chat/sessions/${sessionId}/messages/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ content, model }),
      });
    },
  },
  documents: {
    search: (query: string, topK?: number) =>
      fetchApi('/documents/search', { method: 'POST', body: JSON.stringify({ query, topK }) }),
    list: () => fetchApi('/documents'),
  },
  universities: {
    list: () => fetchApi('/universities'),
    get: (id: string) => fetchApi(`/universities/${id}`),
  },
};

export function streamChat(
  sessionId: string,
  content: string,
  onChunk: (text: string) => void,
  onDone?: () => void,
  onError?: (err: string) => void,
  model?: string
) {
  let finished = false;
  api.chat.sendStream(sessionId, content, model)
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) {
        throw new Error('No response body');
      }

      function read() {
        reader.read()
          .then(({ done, value }) => {
            if (done || finished) {
              if (!finished) {
                finished = true;
                onDone?.();
              }
              return;
            }
            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const dataStr = line.slice(6).trim();
                if (dataStr === '[DONE]') {
                  if (!finished) {
                    finished = true;
                    onDone?.();
                  }
                  return;
                }
                try {
                  const data = JSON.parse(dataStr);
                  if (data.content) onChunk(data.content);
                  if (data.error) throw new Error(data.error);
                } catch (e: any) {
                  if (e.message !== 'Unexpected end of JSON input') {
                    // ignore partial JSON parse errors
                  }
                }
              }
            }
            read();
          })
          .catch((err) => {
            finished = true;
            onError?.(err.message || 'Stream error');
          });
      }
      read();
    })
    .catch((err) => {
      finished = true;
      onError?.(err.message || 'Request failed');
    });
}