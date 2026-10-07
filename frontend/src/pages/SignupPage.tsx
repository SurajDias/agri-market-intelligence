import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Leaf, Lock, Mail, User as UserIcon, Building, Phone, ArrowRight, ArrowLeft, ShieldCheck, Sparkles, TrendingUp, BarChart2 } from 'lucide-react';
import authBg from '../assets/hero/auth/generate_real_farmlands_3.jpg';
import './AuthPages.css';

const SignupPage: React.FC = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [org, setOrg] = useState('');
  const [role, setRole] = useState('FPO');
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.setItem('agrimark_token', 'mock_jwt_token_123');
    localStorage.setItem(
      'agrimark_user',
      JSON.stringify({
        id: 'usr-002',
        name,
        email,
        organization: org,
        role,
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
              <h2>Create Your Account</h2>
              <p>Join AGRIMARK AI for data-driven commodity selling</p>
            </div>

            <form onSubmit={handleSubmit} className="auth-form">
              <div className="input-group">
                <label className="input-label">Full Name</label>
                <div className="input-with-icon">
                  <UserIcon size={16} className="input-icon" />
                  <input
                    type="text"
                    className="input"
                    required
                    placeholder="Ravi Kumar"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                </div>
              </div>

              <div className="input-group">
                <label className="input-label">Organization / FPO Name</label>
                <div className="input-with-icon">
                  <Building size={16} className="input-icon" />
                  <input
                    type="text"
                    className="input"
                    required
                    placeholder="Mandya Farmer Producer Co."
                    value={org}
                    onChange={(e) => setOrg(e.target.value)}
                  />
                </div>
              </div>

              <div className="input-group">
                <label className="input-label">Role</label>
                <select className="select" value={role} onChange={(e) => setRole(e.target.value)}>
                  <option value="FPO">Farmer Producer Organisation (FPO)</option>
                  <option value="Trader">Agri Trader</option>
                  <option value="Aggregator">Commodity Aggregator</option>
                  <option value="Administrator">Platform Administrator</option>
                </select>
              </div>

              <div className="input-group">
                <label className="input-label">Email Address</label>
                <div className="input-with-icon">
                  <Mail size={16} className="input-icon" />
                  <input
                    type="email"
                    className="input"
                    required
                    placeholder="name@org.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
              </div>

              <button type="submit" className="btn btn-primary btn-lg w-full auth-submit-btn">
                Create Account <ArrowRight size={18} />
              </button>
            </form>

            <div className="auth-footer">
              <span>Already registered?</span>
              <Link to="/login" className="auth-link">Sign In</Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SignupPage;
