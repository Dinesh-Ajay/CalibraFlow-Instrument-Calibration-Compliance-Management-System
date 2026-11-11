import React, { useState } from 'react';
import { Bot, X, Send, Sparkles, AlertTriangle, CheckCircle, Clock } from 'lucide-react';
import api from '../services/api';

const AIAssistantDrawer = ({ isOpen, onClose }) => {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([
    {
      sender: 'assistant',
      text: "Hello! I am your CalibraFlow Compliance & Analytics Assistant. Ask me anything about overdue instruments, failed calibrations, open work orders, or impact assessments.",
      sources: []
    }
  ]);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const quickQueries = [
    "Which instruments are overdue?",
    "Which calibrations failed recently?",
    "Show open work orders",
    "Are any certificates missing or invalid?",
    "Which instruments require impact assessments?"
  ];

  const handleSend = async (qToSend) => {
    const text = qToSend || query;
    if (!text.trim() || loading) return;

    const userMsg = { sender: 'user', text };
    setMessages(prev => [...prev, userMsg]);
    setQuery('');
    setLoading(true);

    try {
      const res = await api.post('/assistant/query', { query: text });
      setMessages(prev => [
        ...prev,
        {
          sender: 'assistant',
          text: res.data.answer,
          sources: res.data.sources || []
        }
      ]);
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          sender: 'assistant',
          text: "I encountered an issue querying the operational database. Please check your backend connection.",
          sources: []
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/40 backdrop-blur-sm flex justify-end">
      <div className="w-full max-w-md bg-white h-full shadow-2xl flex flex-col transform transition-all duration-300">
        {/* Header */}
        <div className="px-5 py-4 border-b border-slate-200 bg-slate-900 text-white flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-sm">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold text-sm">CalibraFlow AI Assistant</h3>
              <p className="text-xs text-slate-300 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                Operational Intelligence
              </p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 rounded-md text-slate-400 hover:text-white hover:bg-slate-800">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Quick query chips */}
        <div className="p-3 bg-slate-50 border-b border-slate-200 overflow-x-auto whitespace-nowrap space-x-1.5">
          {quickQueries.map((q, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(q)}
              className="inline-block text-xs bg-white text-slate-700 px-2.5 py-1 rounded-full border border-slate-200 hover:border-blue-300 hover:bg-blue-50 transition-colors shadow-2xs"
            >
              {q}
            </button>
          ))}
        </div>

        {/* Chat message area */}
        <div className="flex-1 p-4 overflow-y-auto space-y-3">
          {messages.map((m, idx) => (
            <div key={idx} className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}>
              <div
                className={`max-w-[85%] rounded-lg px-3.5 py-2.5 text-xs sm:text-sm leading-relaxed whitespace-pre-line shadow-2xs ${
                  m.sender === 'user'
                    ? 'bg-blue-600 text-white rounded-br-none'
                    : 'bg-slate-100 text-slate-800 rounded-bl-none border border-slate-200'
                }`}
              >
                {m.text}
              </div>

              {m.sources && m.sources.length > 0 && (
                <div className="mt-1 flex flex-wrap gap-1 max-w-[85%]">
                  <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Referenced:</span>
                  {m.sources.map((src, sIdx) => (
                    <span key={sIdx} className="text-[10px] bg-slate-200 text-slate-700 px-1.5 py-0.5 rounded font-mono">
                      {src}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex items-center space-x-2 text-xs text-slate-500 bg-slate-100 p-2.5 rounded-lg w-fit">
              <Sparkles className="w-3.5 h-3.5 animate-spin text-blue-600" />
              <span>Analyzing live calibration telemetry...</span>
            </div>
          )}
        </div>

        {/* Input box */}
        <div className="p-3 border-t border-slate-200 bg-white">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask about compliance, overdue assets..."
              className="flex-1 text-xs sm:text-sm px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
          <p className="text-[10px] text-slate-400 mt-1 text-center">
            Adheres strictly to deterministic backend validation rules.
          </p>
        </div>
      </div>
    </div>
  );
};

export default AIAssistantDrawer;
