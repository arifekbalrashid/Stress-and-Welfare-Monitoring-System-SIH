import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { personnelAPI, chatAPI } from '../../services/api';
import { getRiskBadgeClass, formatRiskScore, getRiskColor, formatDateTime, formatDate } from '../../utils/formatters';
import { RISK_LEVEL_LABELS, TREND_LABELS } from '../../utils/constants';
import { TrendingUp, TrendingDown, Minus, ArrowUp, ArrowDown, MessageCircle, Info, BarChart3, List, CalendarCheck, HelpCircle, ChevronRight, Smile, X, MessageSquare, Send, Mic, MicOff } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

const TrendIcon = ({ trend }) => {
  if (trend === 'increasing') return <TrendingUp className="w-4 h-4 text-risk-elevated" />;
  if (trend === 'decreasing') return <TrendingDown className="w-4 h-4 text-risk-low" />;
  return <Minus className="w-4 h-4 text-surface-400" />;
};

const HelpWidget = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'ai', text: "Hi! I'm your SAATHI assistant. I'm here to support you and help you navigate the dashboard. How can I help today?" }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [voiceStatus, setVoiceStatus] = useState(''); // '', 'listening', 'processing', 'error'
  const recognitionRef = useRef(null);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const { t, i18n } = useTranslation();

  const getLangCode = () => {
    const lang = i18n.language || localStorage.getItem('i18nextLng') || 'en';
    const code = lang.split('-')[0];
    const map = { hi: 'hi-IN', bn: 'bn-IN', pa: 'pa-IN', en: 'en-US' };
    return map[code] || 'en-US';
  };

  const speakText = (text) => {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    const langCode = getLangCode();
    utterance.lang = langCode;
    utterance.rate = 0.95;
    utterance.pitch = 1.05; // Slightly higher pitch often sounds more natural

    // Try to find a high-quality voice
    const voices = window.speechSynthesis.getVoices();
    if (voices.length > 0) {
      // 1. Prioritize Google voices for the specific language
      let bestVoice = voices.find(v => v.lang.startsWith(langCode) && v.name.includes('Google'));
      
      // 2. Fallback to Premium/Enhanced OS voices
      if (!bestVoice) {
        bestVoice = voices.find(v => v.lang.startsWith(langCode) && (v.name.includes('Premium') || v.name.includes('Enhanced')));
      }
      
      // 3. Fallback to any voice matching the language
      if (!bestVoice) {
        bestVoice = voices.find(v => v.lang.startsWith(langCode));
      }

      if (bestVoice) {
        utterance.voice = bestVoice;
      }
    }

    window.speechSynthesis.speak(utterance);
  };

  const sendMessage = async (userText, isVoiceMode = false) => {
    if (!userText.trim() || isTyping) return;
    const newMessages = [...messages, { role: 'user', text: userText.trim() }];
    setMessages(newMessages);
    setInput('');
    setIsTyping(true);

    try {
      const payload = { messages: newMessages, is_voice: isVoiceMode };
      const res = await chatAPI.sendMessage(payload);
      const aiResponse = res.data.text;
      setMessages(prev => [...prev, { role: 'ai', text: aiResponse }]);
      
      if (isVoiceMode && res.data.audio) {
        const audio = new Audio("data:audio/mp3;base64," + res.data.audio);
        audio.play().catch(e => console.error("Audio play failed:", e));
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'ai', text: "Sorry, I'm having trouble connecting right now. Please try again later." }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    await sendMessage(input, false);
  };

  const stopListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.abort();
      recognitionRef.current = null;
    }
    setIsListening(false);
    setVoiceStatus('');
  };

  const handleMicClick = () => {
    // If already listening, stop
    if (isListening) {
      stopListening();
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setVoiceStatus('error');
      setMessages(prev => [...prev, { role: 'ai', text: '⚠️ Your browser does not support voice input. Please use Chrome or Edge.' }]);
      setTimeout(() => setVoiceStatus(''), 3000);
      return;
    }

    const recognition = new SpeechRecognition();
    recognitionRef.current = recognition;
    recognition.lang = getLangCode();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setIsListening(true);
      setVoiceStatus('listening');
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setVoiceStatus('processing');
      setIsListening(false);
      // Auto-send the voice message with voice reply enabled
      sendMessage(transcript, true);
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      setIsListening(false);
      recognitionRef.current = null;
      if (event.error === 'not-allowed') {
        setVoiceStatus('error');
        setMessages(prev => [...prev, { role: 'ai', text: '🎤 Microphone access denied. Please allow microphone permission in your browser settings and try again.' }]);
      } else if (event.error === 'no-speech') {
        setVoiceStatus('');
        setMessages(prev => [...prev, { role: 'ai', text: "🎤 I didn't hear anything. Please tap the mic and speak clearly." }]);
      } else if (event.error === 'network') {
        setVoiceStatus('error');
        setMessages(prev => [...prev, { role: 'ai', text: '🎤 Network error. Voice recognition requires an internet connection.' }]);
      } else {
        setVoiceStatus('error');
      }
      setTimeout(() => setVoiceStatus(''), 3000);
    };

    recognition.onend = () => {
      setIsListening(false);
      recognitionRef.current = null;
      if (voiceStatus === 'listening') setVoiceStatus('');
    };

    try {
      recognition.start();
    } catch (err) {
      console.error('Failed to start speech recognition:', err);
      setIsListening(false);
      setVoiceStatus('error');
      setTimeout(() => setVoiceStatus(''), 3000);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-[9999]">
      {isOpen && (
        <div className="bg-white rounded-2xl shadow-[0_10px_40px_rgba(0,0,0,0.15)] border border-surface-100 w-80 h-96 mb-4 overflow-hidden flex flex-col transform transition-all duration-300 origin-bottom-right animate-in fade-in slide-in-from-bottom-4">
          <div className="bg-accent-600 p-4 text-white flex justify-between items-center flex-shrink-0">
            <div className="flex items-center gap-2">
              <Smile className="w-5 h-5" />
              <span className="font-semibold text-sm">SAATHI Assistant</span>
            </div>
            <button onClick={() => { setIsOpen(false); stopListening(); window.speechSynthesis?.cancel(); }} className="text-accent-100 hover:text-white transition-colors">
              <X className="w-4 h-4" />
            </button>
          </div>
          
          <div className="flex-1 p-3 overflow-y-auto bg-surface-50 flex flex-col gap-3">
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] p-3 rounded-2xl text-sm ${
                  msg.role === 'user' 
                    ? 'bg-accent-600 text-white rounded-tr-sm' 
                    : 'bg-white border border-surface-200 text-surface-700 rounded-tl-sm'
                }`}>

                  {msg.text}
                </div>
              </div>
            ))}
            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-white border border-surface-200 text-surface-500 rounded-2xl rounded-tl-sm p-3 flex gap-1 items-center">
                  <div className="w-1.5 h-1.5 bg-surface-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-1.5 h-1.5 bg-surface-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-1.5 h-1.5 bg-surface-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            )}
            {isListening && (
              <div className="flex justify-start">
                <div className="bg-red-50 border border-red-200 text-red-600 rounded-2xl rounded-tl-sm p-3 flex gap-2 items-center text-sm">
                  <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                  Listening... Speak now
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={handleSend} className="p-3 bg-white border-t border-surface-100 flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask for help..."
              className="flex-1 bg-surface-50 border border-surface-200 rounded-full px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent-500/20 focus:border-accent-500 transition-all"
            />
            <button 
              type="button"
              onClick={handleMicClick}
              disabled={isTyping}
              className={`w-9 h-9 flex items-center justify-center rounded-full flex-shrink-0 transition-colors ${
                isListening ? 'bg-red-500 text-white animate-pulse' : 'bg-surface-100 text-surface-500 hover:bg-surface-200'
              }`}
            >
              {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
            </button>
            <button 
              type="submit"
              disabled={!input.trim() || isTyping}
              className="w-9 h-9 flex items-center justify-center bg-accent-600 text-white rounded-full flex-shrink-0 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-accent-700 transition-colors"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      )}
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-12 h-12 bg-accent-600 rounded-full shadow-lg flex items-center justify-center text-white hover:scale-110 hover:bg-accent-700 transition-all duration-300"
      >
        {isOpen ? <X className="w-6 h-6" /> : <Smile className="w-6 h-6" />}
      </button>
    </div>
  );
};

export default function PersonnelDashboard() {
  const [risk, setRisk] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();

  const fetchData = () => {
    setLoading(true);
    // Clear data so skeleton loader shows, making the text update appear all at once
    setRisk(null);
    setDashboard(null);
    Promise.all([
      personnelAPI.getMyRisk().then(r => setRisk(r.data.data)),
      personnelAPI.getDashboard().then(r => setDashboard(r.data.data)),
    ]).catch(() => {}).finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchData();
  }, [i18n.language]);



  if (loading && !risk) return (
    <div>
      <div className="page-header"><h1 className="page-title">Dashboard</h1></div>
      <div className="space-y-3">
        <div className="skeleton h-36 w-full rounded-[14px]" />
        <div className="skeleton h-20 w-full rounded-[14px]" />
        <div className="grid grid-cols-2 gap-3">
          <div className="skeleton h-48 w-full rounded-[14px]" />
          <div className="skeleton h-48 w-full rounded-[14px]" />
        </div>
      </div>
      <HelpWidget />
    </div>
  );

  if (!risk) return (
    <div>
      <div className="page-header"><h1 className="page-title">Dashboard</h1></div>
      <div className="card text-center py-10">
        <Info className="w-7 h-7 text-surface-300 mx-auto mb-2" />
        <p className="text-sm text-surface-500">No risk assessment available yet.</p>
        <p className="text-xs text-surface-400 mt-1">Complete a wellness check-in to get started.</p>
      </div>
      <HelpWidget />
    </div>
  );

  const factors = risk.shap_factors?.factors || [];
  const riskHistory = dashboard?.risk_history || [];
  const recentChanges = dashboard?.recent_changes || [];
  const checkinStatus = dashboard?.checkin_status;

  // Format chart data
  const chartData = riskHistory.map(h => ({
    date: new Date(h.date).toLocaleDateString('en-IN', { month: 'short' }),
    score: Math.round(h.score),
  }));

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
      </div>

      {/* ── Current Welfare Status ── */}
      <div className="card mb-3">
        <div className="section-label">
          <div className="section-label-icon"><BarChart3 /></div>
          {t('dashboard.current_welfare', 'Current welfare status')}
        </div>
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3">
              <span className="text-2xl font-semibold text-surface-900 tabular-nums">{formatRiskScore(risk.risk_score)}</span>
              <span className={getRiskBadgeClass(risk.risk_level)}>{RISK_LEVEL_LABELS[risk.risk_level]}</span>
            </div>
            <div className="flex items-center gap-1.5 mt-1.5">
              <TrendIcon trend={risk.trend} />
              <span className="text-sm text-surface-500">{TREND_LABELS[risk.trend]}</span>
            </div>
          </div>
          <div className="text-right">
            <p className="text-xs text-surface-400">Last assessed</p>
            <p className="text-xs text-surface-500">{formatDateTime(risk.created_at)}</p>
          </div>
        </div>

        {/* Risk scale bar */}
        <div className="mt-4">
          <div className="risk-score-bar">
            <div className="risk-score-fill" style={{ width: `${risk.risk_score}%`, backgroundColor: getRiskColor(risk.risk_level) }} />
          </div>
          <div className="flex justify-between mt-1.5">
            {['Low', 'Moderate', 'Elevated', 'High'].map(label => (
              <span key={label} className="text-[0.6rem] text-surface-400">{label}</span>
            ))}
          </div>
        </div>

        {/* Data source */}
        <p className="text-xs text-surface-400 mt-3">
          {risk.has_wellness_data
            ? ''
            : 'Based on operational data only'}
          <br/>
          <button 
            onClick={() => navigate('/p/support', { state: { category: 'data_correction' } })}
            className="text-[0.65rem] text-accent-600 hover:underline mt-1"
          >
            Think your operational data is incorrect? Request a correction.
          </button>
        </p>
      </div>

      {/* ── Recent Changes ── */}
      {recentChanges.length > 0 && (
        <div className="card mb-3">
          <div className="section-label">
            <div className="section-label-icon"><TrendingUp /></div>
            {t('dashboard.recent_changes', 'Recent changes')}
          </div>
          <div className="grid grid-cols-2 gap-2">
            {recentChanges.map((c, i) => (
              <div key={i} className="flex items-center gap-2 py-1.5">
                {c.direction === 'up'
                  ? <ArrowUp className={`w-3.5 h-3.5 ${c.negative ? 'text-risk-elevated' : 'text-risk-low'}`} />
                  : <ArrowDown className={`w-3.5 h-3.5 ${c.negative ? 'text-risk-elevated' : 'text-risk-low'}`} />
                }
                <span className="text-sm text-surface-600">{c.label}</span>
                <span className={`text-sm font-medium ${c.negative ? 'text-risk-elevated' : 'text-risk-low'}`}>
                  {c.direction === 'up' ? '↑' : '↓'} {c.value}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
        {/* ── Welfare Trend ── */}
        {chartData.length > 1 && (
          <div className="card">
            <div className="section-label">
              <div className="section-label-icon"><TrendingUp /></div>
              {t('dashboard.welfare_trend', 'Welfare trend')}
            </div>
            <ResponsiveContainer width="100%" height={140}>
              <LineChart data={chartData}>
                <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#999' }} />
                <YAxis domain={[0, 100]} axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#999' }} width={28} />
                <Tooltip
                  contentStyle={{ fontSize: 12, border: '1px solid #eee', borderRadius: 8, boxShadow: 'none' }}
                  formatter={(v) => [`${v}/100`, 'Score']}
                />
                <ReferenceLine y={50} stroke="#e5e7eb" strokeDasharray="3 3" />
                <Line type="monotone" dataKey="score" stroke="var(--color-accent-600)" strokeWidth={2} dot={{ r: 3, fill: 'var(--color-accent-600)' }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* ── Contributing Factors ── */}
        <div className="card">
          <div className="section-label">
            <div className="section-label-icon"><List /></div>
            {t('dashboard.factors', 'Contributing factors to this prediction')}
          </div>
          {factors.length === 0 ? (
            <p className="text-xs text-surface-400">No factor data available.</p>
          ) : (
            <div className="space-y-2.5">
              {factors.slice(0, 4).map((f, i) => (
                <div key={i}>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm text-surface-600">{f.label}</span>
                    <span className="text-xs text-surface-400 tabular-nums">{(f.impact * 100).toFixed(0)}%</span>
                  </div>
                  <div className="h-1.5 bg-surface-100 rounded-full overflow-hidden">
                    <div className="h-full bg-accent-500 rounded-full transition-all" style={{ width: `${Math.min(f.impact * 300, 100)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          )}

        </div>
      </div>

      {/* ── Recommendations ── */}
      {(risk.recommendations || []).length > 0 && (
        <div className="card mb-3">
          <p className="text-xs font-medium text-surface-400 uppercase tracking-wide mb-2.5">{t('dashboard.recommendations', 'Recommendations')}</p>
          <div className="space-y-2">
            {risk.recommendations.map((r, i) => (
              <div key={i} className="flex gap-3 p-2.5 bg-surface-50 rounded-lg">
                <span className="badge badge-neutral text-[0.6rem] flex-shrink-0 mt-0.5">{r.category}</span>
                <p className="text-sm text-surface-600">{r.text}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {/* ── Weekly Check-in Status ── */}
        <div
          className="action-card"
          onClick={() => navigate('/p/checkin')}
          role="button"
          tabIndex={0}
        >
          <div className="action-card-left">
            <div className="action-card-icon"><CalendarCheck /></div>
            <div>
              <p className="text-sm font-medium text-surface-700">Weekly wellbeing check-in</p>
              {checkinStatus ? (
                <p className="text-xs text-surface-400 mt-0.5">Completed {formatDate(checkinStatus.submitted_at)}</p>
              ) : (
                <p className="text-xs text-surface-400 mt-0.5">Takes about one minute</p>
              )}
            </div>
          </div>
          <ChevronRight className="w-4 h-4 text-surface-300" />
        </div>

        {/* ── Support Shortcut ── */}
        <div
          className="action-card"
          onClick={() => navigate('/p/support')}
          role="button"
          tabIndex={0}
        >
          <div className="action-card-left">
            <div className="action-card-icon"><HelpCircle /></div>
            <div>
              <p className="text-sm font-medium text-surface-700">Need support?</p>
              <p className="text-xs text-surface-400 mt-0.5">Request confidential support</p>
            </div>
          </div>
          <ChevronRight className="w-4 h-4 text-surface-300" />
        </div>
      </div>

      <HelpWidget />
    </div>
  );
}
