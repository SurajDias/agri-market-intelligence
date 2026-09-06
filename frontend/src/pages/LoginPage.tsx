import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Leaf, Lock, Mail, ArrowRight, ArrowLeft, ShieldCheck, Sparkles, TrendingUp, BarChart2 } from 'lucide-react';
import authBg from '../assets/hero/auth/generate_real_farmlands_3.jpg';
import './AuthPages.css';

const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('ravi.kumar@mandya-fpo.org');
  const [password, setPassword] = useState('demo1234');
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Mock authentication state storage
    localStorage.setItem('agrimark_token', 'mock_jwt_token_123');
    localStorage.setItem(
      'agrimark_user',
      JSON.stringify({
        id: 'usr-001',
        name: 'Ravi Kumar',
        email,
        organization: 'Mandya FPO',
        role: 'FPO',
      })
    );
    navigate('/dashboard');
  };

  return (
    <div className="auth-page" style={{ backgroundImage: `url(${authBg})` }}>
      <div className="auth-overlay"></div>
      
      <div className="auth-wrapper">
        {/* Left Branding Side */}
        <div className="auth-branding">
          <Link to="/" className="auth-brand-logo">
            <span className="brand-logo">🌱 AGRIMARK</span>
            <span className="brand-ai">AI</span>
          </Link>
          
          <div className="auth-branding-hero">
            <span className="auth-badge">
              <Sparkles size={13} /> B2B DECISION INTELLIGENCE
            </span>
            <h1 className="auth-branding-title">
              Smarter market decisions for every harvest.
            </h1>
            <p className="auth-branding-sub">
              Empowering FPOs, aggregators, and agri-traders across Karnataka with predictive APMC pricing and net-margin optimization.
            </p>

            <div className="auth-highlights">
              <div className="auth-highlight-item">
                <div className="auth-highlight-icon"><TrendingUp size={16} /></div>
                <span>7-Day ML Price Forecasting</span>
              </div>
              <div className="auth-highlight-item">
                <div className="auth-highlight-icon"><BarChart2 size={16} /></div>
                <span>24+ APMC Profit Analysis</span>
              </div>
              <div className="auth-highlight-item">
                <div className="auth-highlight-icon"><ShieldCheck size={16} /></div>
                <span>Perishability &amp; Risk Guardrails</span>
              </div>
            </div>
          </div>

          <div className="auth-branding-footer">
            <span>© 2026 AGRIMARK AI Platform • Enterprise Grade Agri-Tech</span>
          </div>
        </div>

        {/* Right Form Container */}
        <div className="auth-container">
          <div className="auth-card">
            <Link to="/" className="auth-back-link">
              <ArrowLeft size={15} /> Back to AGRIMARK AI
            </Link>

            <div className="auth-header">
              <div className="auth-logo">
                <Leaf size={22} />
              </div>
              <h2>Sign in to AGRIMARK AI</h2>
              <p>Enter your registered credentials to access your dashboard</p>
            </div>

            <form onSubmit={handleSubmit} className="auth-form">
              <div className="input-group">
                <label className="input-label" htmlFor="login-email">Email Address</label>
                <div className="input-with-icon">
                  <Mail size={16} className="input-icon" />
                  <input
                    id="login-email"
                    type="email"
                    className="input"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
              </div>

              <div className="input-group">
                <label className="input-label" htmlFor="login-password">Password</label>
                <div className="input-with-icon">
                  <Lock size={16} className="input-icon" />
                  <input
                    id="login-password"
                    type="password"
                    className="input"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                </div>
              </div>

              <button type="submit" className="btn btn-primary btn-lg w-full auth-submit-btn">
                Sign In <ArrowRight size={18} />
              </button>
            </form>

            <div className="auth-footer">
              <span>Don't have an account?</span>
              <Link to="/signup" className="auth-link">Create Account</Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
