import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './styles.css';

function HomePage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }

    // Verify token is valid
    fetch('http://localhost:8000/verify-token', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    .then(response => {
      if (!response.ok) {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        navigate('/login');
        return;
      }
      return response.json();
    })
    .then(data => {
      if (data) {
        setUsername(data.username);
      }
    })
    .catch(() => {
      localStorage.removeItem('token');
      localStorage.removeItem('username');
      navigate('/login');
    })
    .finally(() => {
      setIsLoading(false);
    });
  }, [navigate]);

  const handleModeSelect = (mode) => {
    navigate(`/upload/${mode}`);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    navigate('/login');
  };

  if (isLoading) {
    return (
      <div className="homepage-container">
        <div className="loading">Loading...</div>
      </div>
    );
  }

  return (
    <div className="homepage-container">
      <div className="header">
        <div className="logo">CompLite</div>
        <div className="user-info">
          <span>Welcome, {username}!</span>
          <button onClick={handleLogout} className="logout-button">Logout</button>
        </div>
      </div>
      
      <div className="subtitle">Comprehensive Compliance AI Assistant</div>
      
      <div className="mode-selection">
        <h2>Select Compliance Mode</h2>
        <div className="mode-buttons">
          <button 
            className="mode-button sox-button"
            onClick={() => handleModeSelect('sox')}
          >
            <div className="mode-icon">📊</div>
            <div className="mode-title">SOX Compliance</div>
            <div className="mode-description">
              Financial controls, internal controls, and audit compliance
            </div>
          </button>
          
          <button 
            className="mode-button esg-button"
            onClick={() => handleModeSelect('esg')}
          >
            <div className="mode-icon">🌱</div>
            <div className="mode-title">ESG Compliance</div>
            <div className="mode-description">
              Environmental, Social, and Governance metrics
            </div>
          </button>

          <button 
            className="mode-button soc2-button"
            onClick={() => handleModeSelect('soc2')}
          >
            <div className="mode-icon">🔒</div>
            <div className="mode-title">SOC 2 Compliance</div>
            <div className="mode-description">
              System and Organization Controls for security, availability, and privacy
            </div>
          </button>

          <button 
            className="mode-button iso27001-button"
            onClick={() => handleModeSelect('iso27001')}
          >
            <div className="mode-icon">🛡️</div>
            <div className="mode-title">ISO 27001</div>
            <div className="mode-description">
              Information Security Management (Annex A)
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}

export default HomePage; 