import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from './components/layout/AppLayout';

// Pages
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import ExecutiveOverview from './pages/ExecutiveOverview';
import MarketComparisonPage from './pages/MarketComparison';
import ForecastingPage from './pages/Forecasting';
import OpportunityMapPage from './pages/OpportunityMap';
import DecisionSimulatorPage from './pages/DecisionSimulator';
import RecommendationDetails from './pages/RecommendationDetails';
import ReportsPage from './pages/Reports';
import DataQualityPage from './pages/DataQuality';
import CommodityTrendsPage from './pages/CommodityTrends';
import SettingsPage from './pages/SettingsPage';
import NotFoundPage from './pages/NotFoundPage';

// Protected Route Wrapper (Mock Auth Check)
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const token = localStorage.getItem('agrimark_token');
  // For demo convenience, allow access even if token missing, but set token on first visit
  if (!token) {
    localStorage.setItem('agrimark_token', 'mock_jwt_token_123');
  }
  return <AppLayout>{children}</AppLayout>;
};

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />

        {/* Application Protected Routes */}
        <Route path="/dashboard" element={<ProtectedRoute><ExecutiveOverview /></ProtectedRoute>} />
        <Route path="/markets" element={<ProtectedRoute><MarketComparisonPage /></ProtectedRoute>} />
        <Route path="/forecasts" element={<ProtectedRoute><ForecastingPage /></ProtectedRoute>} />
        <Route path="/market-map" element={<ProtectedRoute><OpportunityMapPage /></ProtectedRoute>} />
        <Route path="/simulator" element={<ProtectedRoute><DecisionSimulatorPage /></ProtectedRoute>} />
        <Route path="/recommendation/:id" element={<ProtectedRoute><RecommendationDetails /></ProtectedRoute>} />
        <Route path="/reports" element={<ProtectedRoute><ReportsPage /></ProtectedRoute>} />
        <Route path="/data-quality" element={<ProtectedRoute><DataQualityPage /></ProtectedRoute>} />
        <Route path="/trends" element={<ProtectedRoute><CommodityTrendsPage /></ProtectedRoute>} />
        <Route path="/settings" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />

        {/* 404 Fallback */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
