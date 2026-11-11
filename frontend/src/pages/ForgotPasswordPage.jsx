import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { ShieldCheck, Mail, ArrowRight, AlertCircle } from 'lucide-react';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    setError(''); setMessage(''); setSubmitting(true);
    try {
      const res = await api.post('/auth/forgot-password', { email: email.trim() });
      setMessage(res.data?.message || 'If the email is registered, a password recovery message has been sent.');
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to process request.');
    } finally { setSubmitting(false); }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
      <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#38bdf8_1px,transparent_1px)] [background-size:16px_16px]"></div>
      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        <div className="flex justify-center"><div className="w-12 h-12 rounded-xl bg-blue-600 flex items-center justify-center text-white"><ShieldCheck className="w-7 h-7" /></div></div>
        <h2 className="mt-4 text-center text-xl font-bold text-white">Forgot password</h2>
        <p className="mt-1 text-center text-xs text-slate-400">Enter your registered email to receive a recovery token.</p>
      </div>
      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        <div className="bg-slate-900 border border-slate-800 py-8 px-6 shadow-2xl rounded-2xl">
          {error && <div className="mb-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-2"><AlertCircle className="w-4 h-4" />{error}</div>}
          {message && <div className="mb-4 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs">{message}</div>}
          <form className="space-y-4" onSubmit={onSubmit}>
            <div>
              <label className="block text-xs font-medium text-slate-300">Email address</label>
              <div className="mt-1 relative"><Mail className="h-4 w-4 absolute left-3 top-2.5 text-slate-500" />
                <input type="email" required value={email} onChange={(e)=>setEmail(e.target.value)} className="block w-full pl-9 pr-3 py-2 text-sm bg-slate-950 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="name@example.com" />
              </div>
            </div>
            <button type="submit" disabled={submitting} className="w-full flex justify-center items-center py-2.5 px-4 rounded-lg text-sm font-semibold text-white bg-blue-600 hover:bg-blue-500 disabled:opacity-50">{submitting?'Submitting...':'Send recovery message'}<ArrowRight className="ml-2 w-4 h-4"/></button>
          </form>
          <div className="mt-5 text-xs text-slate-400 flex justify-between"><Link to="/login" className="text-blue-400 hover:text-blue-300">Back to sign in</Link><Link to="/reset-password" className="text-blue-400 hover:text-blue-300">Have a token?</Link></div>
        </div>
      </div>
    </div>
  );
}
