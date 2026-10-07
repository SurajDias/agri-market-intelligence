import React from 'react';
import { Link } from 'react-router-dom';
import {
  TrendingUp, Shield, BarChart3, MapPin, Award, CheckCircle,
  ArrowRight, Sparkles, Sliders, ChevronRight, XCircle, AlertTriangle,
  TrendingDown, Clock, Truck, ShieldCheck, Database, FileText, CheckCircle2,
  Sprout, AlertOctagon
} from 'lucide-react';
import heroBg from '../assets/hero/Use_this_Google_Whisk_prompt_C_1.jpg';
import img1 from '../assets/hero/hero1/img1.jpg';
import img2 from '../assets/hero/hero1/img2.jpg';
import img3 from '../assets/hero/hero1/img3.jpg';
import img4 from '../assets/hero/hero1/img4.jpg';
import img5 from '../assets/hero/hero1/img5.jpg';
import pic1 from '../assets/hero/feature/pic1.jpg';
import pic2 from '../assets/hero/feature/pic2.jpg';
import pic3 from '../assets/hero/feature/pic3.jpg';
import pic4 from '../assets/hero/feature/pic4.jpg';
import pic5 from '../assets/hero/feature/pic5.jpg';
import pic6 from '../assets/hero/feature/pic6.jpg';
import traditionalBg from '../assets/hero/challenges/traditional.jpg';
import agrimarkBg from '../assets/hero/challenges/agrimark.jpg';
import AccordionGallery, { AccordionItem } from '../components/ui/AccordionGallery';
import CircularGallery, { CircularGalleryItem } from '../components/ui/CircularGallery';
import ChromaGrid, { ChromaGridItem } from '../components/ui/ChromaGrid';
import './LandingPage.css';

const WORKFLOW_ITEMS: AccordionItem[] = [
  {
    image: img1,
    label: 'Data Aggregation',
    step: '01',
    desc: 'Collect mandi prices, arrivals, road distances & weather from AGMARKNET & official APIs.',
    alt: 'Data Aggregation'
  },
  {
    image: img2,
    label: 'Data Cleaning',
    step: '02',
    desc: 'Automated anomaly detection, duplicate removal & outlier filtering.',
    alt: 'Data Cleaning'
  },
  {
    image: img3,
    label: 'AI Price Forecast',
    step: '03',
    desc: 'Time-series predictive ML models generate 7-day to 10-day price trajectories.',
    alt: 'AI Price Forecast'
  },
  {
    image: img4,
    label: 'Multi-Market Analysis',
    step: '04',
    desc: 'Evaluate net revenue = (Forecast Price × Qty) - (Transport Cost + Mandi Fees).',
    alt: 'Multi-Market Analysis'
  },
  {
    image: img5,
    label: 'Actionable Recommendation',
    step: '05',
    desc: 'Synthesise optimal market, date window & risk rating into plain-language advice.',
    alt: 'Actionable Recommendation'
  },
];

const FEATURE_ITEMS: CircularGalleryItem[] = [
  { image: pic1, text: 'Price Forecasting' },
  { image: pic2, text: 'Market Comparison' },
  { image: pic3, text: 'Transport Analysis' },
  { image: pic4, text: 'Risk & Confidence' },
  { image: pic5, text: 'Decision Simulator' },
  { image: pic6, text: 'Explainable AI' },
];

const FEATURE_CARDS_DATA: ChromaGridItem[] = [
  {
    icon: <TrendingUp size={24} />,
    title: 'Price Forecasting',
    desc: 'Predict mandi prices 7–10 days ahead with confidence interval bands.',
    borderColor: '#1B5E20',
    spotlightColor: 'rgba(27, 94, 32, 0.14)',
    accentGradient: 'linear-gradient(135deg, rgba(232, 245, 233, 0.7) 0%, rgba(255, 255, 255, 1) 100%)',
  },
  {
    icon: <BarChart3 size={24} />,
    title: 'Market Comparison',
    desc: 'Rank top regional markets by expected net profit after logistics.',
    borderColor: '#558B2F',
    spotlightColor: 'rgba(85, 139, 47, 0.14)',
    accentGradient: 'linear-gradient(135deg, rgba(241, 248, 233, 0.7) 0%, rgba(255, 255, 255, 1) 100%)',
  },
  {
    icon: <MapPin size={24} />,
    title: 'Transport Analysis',
    desc: 'Calculate exact road distance and transport overhead per quintal.',
    borderColor: '#7CB342',
    spotlightColor: 'rgba(124, 179, 66, 0.14)',
    accentGradient: 'linear-gradient(135deg, rgba(244, 249, 238, 0.7) 0%, rgba(255, 255, 255, 1) 100%)',
  },
  {
    icon: <Shield size={24} />,
    title: 'Risk & Confidence',
    desc: 'Quantify market volatility and model certainty before shipping.',
    borderColor: '#F59E0B',
    spotlightColor: 'rgba(245, 158, 11, 0.14)',
    accentGradient: 'linear-gradient(135deg, rgba(254, 243, 199, 0.6) 0%, rgba(255, 255, 255, 1) 100%)',
  },
  {
    icon: <Sliders size={24} />,
    title: 'Decision Simulator',
    desc: 'Simulate what-if scenarios across date, volume, and crop grade.',
    borderColor: '#2E7D32',
    spotlightColor: 'rgba(46, 125, 50, 0.14)',
    accentGradient: 'linear-gradient(135deg, rgba(232, 245, 233, 0.7) 0%, rgba(255, 255, 255, 1) 100%)',
  },
  {
    icon: <Award size={24} />,
    title: 'Explainable AI',
    desc: 'Understand exact factor weights driving every recommendation.',
    borderColor: '#D97706',
    spotlightColor: 'rgba(217, 119, 6, 0.14)',
    accentGradient: 'linear-gradient(135deg, rgba(254, 243, 199, 0.6) 0%, rgba(255, 255, 255, 1) 100%)',
  },
];

const LandingPage: React.FC = () => {
  return (
    <div className="landing-page">
      {/* Header / Nav */}
      <nav className="landing-nav">
        <div className="landing-nav__container">
          <div className="landing-nav__brand">
            <span className="brand-logo">🌱 AGRIMARK</span>
            <span className="brand-ai">AI</span>
          </div>
          <div className="landing-nav__links">
            <a href="#problem">Problem</a>
            <a href="#how-it-works">How It Works</a>
            <a href="#features">Features</a>
            <a href="#data-sources">Data Sources</a>
          </div>
          <div className="landing-nav__actions">
            <Link to="/login" className="btn btn-ghost btn-sm">Sign In</Link>
            <Link to="/signup" className="btn btn-primary btn-sm">Get Started</Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section
        className="hero-section"
        style={{
          backgroundImage: `linear-gradient(90deg, rgba(247, 245, 240, 0.75) 0%, rgba(247, 245, 240, 0.40) 35%, rgba(247, 245, 240, 0.05) 60%, rgba(247, 245, 240, 0) 100%), url(${heroBg})`,
        }}
      >
        <div className="hero-container">
          <div className="hero-content animate-fade-in-up">
            <div className="hero-badge">
              <Sparkles size={14} /> AI-POWERED AGRI-MARKET DECISION PLATFORM
            </div>
            <h1 className="hero-title">
              Make Every Market Decision <span className="text-highlight">More Profitable.</span>
            </h1>
            <p className="hero-subtitle">
              AI-powered market intelligence that helps FPOs, traders and aggregators decide where, when and how to sell agricultural produce.
            </p>
            <div className="hero-ctas">
              <Link to="/dashboard" className="btn btn-primary btn-xl">
                Explore Dashboard <ArrowRight size={18} />
              </Link>
              <Link to="/simulator" className="btn btn-secondary btn-xl">
                Try Decision Simulator
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Problem Section */}
      <section id="problem" className="problem-section">
        {/* Background ambient gradient blurs */}
        <div className="prob-ambient-blur prob-ambient-blur--left"></div>
        <div className="prob-ambient-blur prob-ambient-blur--right"></div>

        <div className="section-container">
          <div className="text-center mb-12">
            <span className="badge badge-primary mb-2">THE CHALLENGE</span>
            <h2 className="section-heading">Farmers &amp; Aggregators Don’t Just Need Prices.<br />They Need Decisions.</h2>
            <p className="section-desc">Raw mandi prices miss crucial variables like transport, shelf-life, and multi-day price shifts.</p>
          </div>

          <div className="problem-comparison-wrapper">
            {/* Center Transition Indicator */}
            <div className="prob-transition-arrow">
              <div className="prob-arrow-circle">
                <ArrowRight size={20} />
              </div>
              <span className="prob-arrow-label">AI PARADIGM SHIFT</span>
            </div>

            {/* Traditional Approach Glass Card */}
            <div className="prob-panel prob-panel--traditional">
              {/* Atmospheric background image */}
              <div 
                className="prob-panel__bg-img prob-panel__bg-img--traditional" 
                style={{ backgroundImage: `url(${traditionalBg})` }}
              ></div>

              {/* Abstract background SVG elements inside traditional glass */}
              <div className="prob-bg-art prob-bg-art--traditional">
                <svg className="prob-svg-chart-down" viewBox="0 0 300 200" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M10 30 Q 70 50, 120 110 T 280 180" stroke="#EF4444" strokeWidth="2.5" strokeDasharray="4 4" opacity="0.25" />
                  <path d="M140 100 L130 115 L150 115 Z" fill="#EF4444" opacity="0.3" />
                  <path d="M270 165 L260 180 L280 180 Z" fill="#EF4444" opacity="0.3" />
                </svg>
              </div>

              <div className="prob-panel__header">
                <div className="prob-panel__title-wrap">
                  <div className="prob-icon-badge prob-icon-badge--warning">
                    <AlertOctagon size={20} />
                  </div>
                  <div>
                    <h3 className="prob-panel__title">Traditional Approach</h3>
                    <span className="prob-panel__sub">Reactive &amp; Intuition-Based</span>
                  </div>
                </div>
                <span className="prob-risk-tag">
                  <TrendingDown size={12} /> Higher Risk
                </span>
              </div>

              <div className="prob-panel__rows">
                <div className="prob-row prob-row--traditional">
                  <div className="prob-row__icon">
                    <MapPin size={18} />
                  </div>
                  <div className="prob-row__content">
                    <span className="prob-row__title">Nearest Mandi Blindspot</span>
                    <p className="prob-row__desc">Selling at local markets without visibility into prices at nearby APMCs.</p>
                  </div>
                </div>

                <div className="prob-row prob-row--traditional">
                  <div className="prob-row__icon">
                    <TrendingDown size={18} />
                  </div>
                  <div className="prob-row__content">
                    <span className="prob-row__title">Ignores Future Trajectories</span>
                    <p className="prob-row__desc">Missing 7-day price movement trends and optimal selling windows.</p>
                  </div>
                </div>

                <div className="prob-row prob-row--traditional">
                  <div className="prob-row__icon">
                    <Truck size={18} />
                  </div>
                  <div className="prob-row__content">
                    <span className="prob-row__title">Uncalculated Logistics Loss</span>
                    <p className="prob-row__desc">Transport costs and fuel surge fees consuming unexpected margins.</p>
                  </div>
                </div>

                <div className="prob-row prob-row--traditional">
                  <div className="prob-row__icon">
                    <Clock size={18} />
                  </div>
                  <div className="prob-row__content">
                    <span className="prob-row__title">Quality &amp; Perishability Risk</span>
                    <p className="prob-row__desc">Spoilage losses caused by transport delays and non-optimized post-harvest timing.</p>
                  </div>
                </div>
              </div>

              {/* Bottom Quote Artwork */}
              <div className="prob-traditional-footer">
                <span className="prob-handwritten-quote">“Good produce. Poor returns.”</span>
              </div>
            </div>

            {/* AGRIMARK AI Approach Glass Card */}
            <div className="prob-panel prob-panel--agrimark">
              {/* Atmospheric background image */}
              <div 
                className="prob-panel__bg-img prob-panel__bg-img--agrimark" 
                style={{ backgroundImage: `url(${agrimarkBg})` }}
              ></div>

              {/* Abstract background SVG elements inside AGRIMARK glass */}
              <div className="prob-bg-art prob-bg-art--agrimark">
                <svg className="prob-svg-chart-up" viewBox="0 0 300 200" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M10 170 Q 90 150, 160 80 T 280 20" stroke="#16A34A" strokeWidth="2.5" opacity="0.3" />
                  <circle cx="160" cy="80" r="4" fill="#16A34A" opacity="0.5" />
                  <circle cx="280" cy="20" r="5" fill="#16A34A" opacity="0.7" />
                </svg>
              </div>

              <div className="prob-panel__header">
                <div className="prob-panel__title-wrap">
                  <div className="prob-icon-badge prob-icon-badge--agrimark">
                    <Sprout size={20} />
                  </div>
                  <div>
                    <h3 className="prob-panel__title">AGRIMARK AI Approach</h3>
                    <span className="prob-panel__sub">Predictive &amp; Net-Profit Optimized</span>
                  </div>
                </div>
                <span className="prob-recommended-tag">
                  <Sparkles size={12} /> Recommended
                </span>
              </div>

              <div className="prob-panel__rows">
                <div className="prob-row prob-row--agrimark">
                  <div className="prob-row__icon">
                    <BarChart3 size={18} />
                  </div>
                  <div className="prob-row__content">
                    <span className="prob-row__title">24+ APMC Net-Profit Comparison</span>
                    <p className="prob-row__desc">Simultaneously evaluates gross price minus exact haulage &amp; mandi fees.</p>
                  </div>
                </div>

                <div className="prob-row prob-row--agrimark">
                  <div className="prob-row__icon">
                    <TrendingUp size={18} />
                  </div>
                  <div className="prob-row__content">
                    <span className="prob-row__title">ML Price Trajectory Forecasting</span>
                    <p className="prob-row__desc">Time-series forecasting models with high accuracy (MAPE &lt; 8%).</p>
                  </div>
                </div>

                <div className="prob-row prob-row--agrimark">
                  <div className="prob-row__icon">
                    <Truck size={18} />
                  </div>
                  <div className="prob-row__content">
                    <span className="prob-row__title">Transport &amp; Spoilage Optimization</span>
                    <p className="prob-row__desc">Dynamic route distance &amp; shelf-life risk calculation before dispatch.</p>
                  </div>
                </div>

                <div className="prob-row prob-row--agrimark">
                  <div className="prob-row__icon">
                    <ShieldCheck size={18} />
                  </div>
                  <div className="prob-row__content">
                    <span className="prob-row__title">Confidence &amp; Risk Guardrails</span>
                    <p className="prob-row__desc">Actionable recommendations backed by clear confidence ratings &amp; reasoning.</p>
                  </div>
                </div>
              </div>

              {/* Bottom Visual Decision Transformation Result */}
              <div className="prob-transformation-result">
                <span className="prob-result-label">DECISION ADVANTAGE PIPELINE</span>
                <div className="prob-pipeline-flow">
                  <div className="prob-pipeline-step">
                    <FileText size={13} />
                    <span>Price Data</span>
                  </div>
                  <ChevronRight size={13} className="prob-pipeline-arrow" />
                  <div className="prob-pipeline-step">
                    <TrendingUp size={13} />
                    <span>Forecast</span>
                  </div>
                  <ChevronRight size={13} className="prob-pipeline-arrow" />
                  <div className="prob-pipeline-step">
                    <Truck size={13} />
                    <span>Logistics</span>
                  </div>
                  <ChevronRight size={13} className="prob-pipeline-arrow" />
                  <div className="prob-pipeline-step">
                    <ShieldCheck size={13} />
                    <span>Risk</span>
                  </div>
                  <ChevronRight size={13} className="prob-pipeline-arrow" />
                  <div className="prob-pipeline-step prob-pipeline-step--active">
                    <Sprout size={13} />
                    <span>Best Decision</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="how-section">
        <div className="section-container">
          <div className="text-center mb-12">
            <span className="badge badge-primary mb-2">METHODOLOGY</span>
            <h2 className="section-heading">How AGRIMARK AI Works</h2>
            <p className="section-desc">Hover or click any panel to explore our 5-step decision intelligence workflow.</p>
          </div>

          <div className="how-it-works-gallery">
            <AccordionGallery
              items={WORKFLOW_ITEMS}
              defaultIndex={2}
              expandRatio={0.52}
              trigger="hover"
              height={440}
              gap={12}
              radius={16}
            />
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="features-section">
        <div className="section-container">
          <div className="text-center mb-6">
            <h2 className="section-heading">Platform Features</h2>
            <p className="section-desc">Drag horizontally or use arrow keys to navigate through core platform capabilities.</p>
          </div>

          <div className="circular-gallery-wrapper mb-12">
            <CircularGallery
              items={FEATURE_ITEMS}
              bend={3}
              textColor="#111827"
              borderRadius={0.05}
              scrollSpeed={2}
              scrollEase={0.05}
            />
          </div>

          <ChromaGrid
            items={FEATURE_CARDS_DATA}
            radius={280}
            damping={0.45}
            fadeOut={0.6}
            ease="power3.out"
          />
        </div>
      </section>

      {/* Final CTA */}
      <section className="cta-section">
        <div className="section-container text-center">
          <h2 className="cta-heading">Turn Market Data into Your Next Best Decision.</h2>
          <p className="cta-sub">Empowering FPOs, Traders and Aggregators across Karnataka & South India.</p>
          <Link to="/dashboard" className="btn btn-primary btn-xl">
            Enter AGRIMARK AI <ArrowRight size={20} />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="section-container text-center">
          <p>© 2026 AGRIMARK AI — Agricultural Market Intelligence Platform. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
