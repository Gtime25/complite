import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import './styles.css';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, CartesianGrid, Cell
} from 'recharts';

function UploadPage() {
  const { mode } = useParams();
  const navigate = useNavigate();
  
  const [file, setFile] = useState(null);
  const [prompt, setPrompt] = useState('');
  const [response, setResponse] = useState('');
  const [generatePdf, setGeneratePdf] = useState(true);
  const [isDragging, setIsDragging] = useState(false);
  const [dashboardData, setDashboardData] = useState(null);
  const [anomalies, setAnomalies] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [showAlertPanel, setShowAlertPanel] = useState(false);
  const [panelType, setPanelType] = useState(null);
  const [panelItems, setPanelItems] = useState([]);
  const [showAnomalyPanel, setShowAnomalyPanel] = useState(false);
  const [auditTrail, setAuditTrail] = useState([]);
  const [showAuditPanel, setShowAuditPanel] = useState(false);
  const [showAnalytics, setShowAnalytics] = useState(false);
  const [analyticsTab, setAnalyticsTab] = useState('trends');
  const [analyticsData, setAnalyticsData] = useState({});
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [analyticsModal, setAnalyticsModal] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const isSOX = mode === 'sox';
  const isESG = mode === 'esg';
  const isSOC2 = mode === 'soc2';
  const isISO = mode === 'iso27001';

  const samplePrompts = isSOX ? [
    'Summarize risks by control owner',
    'Which controls failed last quarter?',
    'What are the high-risk, overdue controls?',
    'Generate evidence package for failed controls',
    'Highlight controls with rare testing frequencies'
  ] : isESG ? [
    'Summarize ESG metrics by factor',
    'Which ESG metrics are below threshold?',
    'What are the high-priority ESG issues?',
    'Generate ESG compliance report',
    'Highlight environmental impact metrics'
  ] : isSOC2 ? [
    'Summarize SOC 2 controls by Trust Service Criteria',
    'Which controls have failed status?',
    'What are the overdue control tests?',
    'Generate SOC 2 compliance report',
    'Highlight missing Trust Service Criteria coverage'
  ] : [
    'Summarize ISO 27001 controls by Annex A section',
    'Which controls are not implemented?',
    'What are the overdue control reviews?',
    'Generate ISO 27001 compliance report',
    'Highlight missing evidence or Annex A references'
  ];

  const logAudit = async (action) => {
    const timestamp = new Date().toLocaleString();
    const entry = `${timestamp}: ${action}`;
    setAuditTrail(prev => [entry, ...prev]);
  };

  const parseDashboard = async (uploadFile) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const csv = e.target.result;
        const rows = csv.split('\n').map(row => row.split(','));
        const headers = rows[0];
        const dataRows = rows.slice(1);

        if (isSOX) {
          // SOX dashboard parsing
          const riskIndex = headers.findIndex(h => h.toLowerCase().includes('risk'));
          const resultIndex = headers.findIndex(h => h.toLowerCase().includes('result'));
          const dueIndex = headers.findIndex(h => h.toLowerCase().includes('due'));
          const descIndex = headers.findIndex(h => h.toLowerCase().includes('description'));

          let total = dataRows.length;
          let high = 0, failed = 0, overdue = 0;
          let highList = [], failedList = [], overdueList = [];

          const now = new Date();
          for (let row of dataRows) {
            const desc = row[descIndex] || 'Unnamed control';

            if (row[riskIndex]?.toLowerCase().includes('high')) {
              high++;
              highList.push(desc);
            }

            if (row[resultIndex]?.toLowerCase().includes('fail')) {
              failed++;
              failedList.push(desc);
            }

            if (dueIndex >= 0) {
              let due = new Date(row[dueIndex]);
              if (!isNaN(due) && due < now) {
                overdue++;
                overdueList.push(desc);
              }
            }
          }

          setDashboardData({ total, high, failed, overdue, highList, failedList, overdueList });
        } else if (isESG) {
          // ESG dashboard parsing
          const factorIndex = headers.findIndex(h => h.toLowerCase().includes('factor'));
          const statusIndex = headers.findIndex(h => h.toLowerCase().includes('status'));
          const dueIndex = headers.findIndex(h => h.toLowerCase().includes('due'));
          const metricIndex = headers.findIndex(h => h.toLowerCase().includes('metric'));

          let total = dataRows.length;
          let critical = 0, failed = 0, overdue = 0;
          let criticalList = [], failedList = [], overdueList = [];

          const now = new Date();
          for (let row of dataRows) {
            const metric = row[metricIndex] || 'Unnamed metric';

            if (row[factorIndex]?.toLowerCase().includes('critical')) {
              critical++;
              criticalList.push(metric);
            }

            if (row[statusIndex]?.toLowerCase().includes('fail')) {
              failed++;
              failedList.push(metric);
            }

            if (dueIndex >= 0) {
              let due = new Date(row[dueIndex]);
              if (!isNaN(due) && due < now) {
                overdue++;
                overdueList.push(metric);
              }
            }
          }

          setDashboardData({ total, critical, failed, overdue, criticalList, failedList, overdueList });
        } else if (isSOC2) {
          // SOC 2 dashboard parsing
          const tscIndex = headers.findIndex(h => h.toLowerCase().includes('trust service criteria'));
          const statusIndex = headers.findIndex(h => h.toLowerCase().includes('status'));
          const testDateIndex = headers.findIndex(h => h.toLowerCase().includes('last test date'));
          const descIndex = headers.findIndex(h => h.toLowerCase().includes('description'));

          let total = dataRows.length;
          let critical = 0, failed = 0, overdue = 0;
          let criticalList = [], failedList = [], overdueList = [];

          const now = new Date();
          const ninetyDaysAgo = new Date(now.getTime() - (90 * 24 * 60 * 60 * 1000));
          
          for (let row of dataRows) {
            const desc = row[descIndex] || 'Unnamed control';

            if (row[tscIndex]?.toLowerCase().includes('cc')) {
              critical++;
              criticalList.push(desc);
            }

            if (row[statusIndex]?.toLowerCase().includes('fail')) {
              failed++;
              failedList.push(desc);
            }

            if (testDateIndex >= 0) {
              let testDate = new Date(row[testDateIndex]);
              if (!isNaN(testDate) && testDate < ninetyDaysAgo) {
                overdue++;
                overdueList.push(desc);
              }
            }
          }

          setDashboardData({ total, critical, failed, overdue, criticalList, failedList, overdueList });
        } else {
          // ISO 27001 dashboard parsing
          const statusIndex = headers.findIndex(h => h.toLowerCase().includes('status'));
          const reviewIndex = headers.findIndex(h => h.toLowerCase().includes('review date'));
          const ownerIndex = headers.findIndex(h => h.toLowerCase().includes('owner'));
          const evidenceIndex = headers.findIndex(h => h.toLowerCase().includes('evidence'));
          const annexIndex = headers.findIndex(h => h.toLowerCase().includes('annex'));
          const descIndex = headers.findIndex(h => h.toLowerCase().includes('name'));

          let total = dataRows.length;
          let failed = 0, overdue = 0, missingOwner = 0, missingEvidence = 0, missingAnnex = 0;
          let failedList = [], overdueList = [], missingOwnerList = [], missingEvidenceList = [], missingAnnexList = [];

          const now = new Date();
          const oneYearAgo = new Date(now.getTime() - (365 * 24 * 60 * 60 * 1000));

          for (let row of dataRows) {
            const desc = row[descIndex] || 'Unnamed control';
            if (row[statusIndex]?.toLowerCase().includes('fail') || row[statusIndex]?.toLowerCase().includes('not implemented')) {
              failed++;
              failedList.push(desc);
            }
            if (reviewIndex >= 0) {
              let review = new Date(row[reviewIndex]);
              if (!isNaN(review) && review < oneYearAgo) {
                overdue++;
                overdueList.push(desc);
              }
            }
            if (ownerIndex >= 0 && (!row[ownerIndex] || row[ownerIndex].trim() === '')) {
              missingOwner++;
              missingOwnerList.push(desc);
            }
            if (evidenceIndex >= 0 && (!row[evidenceIndex] || row[evidenceIndex].trim() === '')) {
              missingEvidence++;
              missingEvidenceList.push(desc);
            }
            if (annexIndex >= 0 && (!row[annexIndex] || row[annexIndex].trim() === '')) {
              missingAnnex++;
              missingAnnexList.push(desc);
            }
          }

          setDashboardData({ total, failed, overdue, missingOwner, missingEvidence, missingAnnex, failedList, overdueList, missingOwnerList, missingEvidenceList, missingAnnexList });
        }
      } catch {
        setDashboardData(null);
      }
    };
    reader.readAsText(uploadFile);
  };

  const autoEmbed = async (uploadFile) => {
    const formData = new FormData();
    formData.append('file', uploadFile);
    formData.append('mode', mode);
    
    const token = localStorage.getItem('token');
    const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
    
    try {
      await fetch('http://localhost:8000/auto-embed/', {
        method: 'POST',
        body: formData,
        headers
      });

      const res2 = await fetch('http://localhost:8000/detect-anomalies/', {
        method: 'POST',
        body: formData,
        headers
      });
      const json2 = await res2.json();
      setAnomalies(json2.anomalies || []);
      if (json2.anomalies && json2.anomalies.length > 0) {
        await logAudit(`Detected anomalies in uploaded ${mode.toUpperCase()} file.`);
      }

      const res3 = await fetch('http://localhost:8000/detect-alerts/', {
        method: 'POST',
        body: formData,
        headers
      });
      const json3 = await res3.json();
      if (json3.alerts && json3.alerts.length > 0 && json3.alerts[0] !== "No urgent alerts detected.") {
        setAlerts(json3.alerts);
        setShowAlertPanel(true);
        await logAudit(`Detected real-time alerts in ${mode.toUpperCase()} file.`);

        await fetch('http://localhost:8000/send-slack-alert/', {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            ...headers
          },
          body: JSON.stringify({ alerts: json3.alerts, mode })
        });
        await logAudit("Sent Slack alert.");
      } else {
        setAlerts([]);
        setShowAlertPanel(false);
      }

    } catch {
      alert(`Failed to embed or detect anomalies for ${mode.toUpperCase()} data.`);
    }
  };

  const handleFileChange = async (e) => {
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
    setPrompt('');
    setResponse('');
    await logAudit(`Uploaded ${mode.toUpperCase()} file: ${selectedFile.name}`);
    await autoEmbed(selectedFile);
    await parseDashboard(selectedFile);
  };

  const handlePromptClick = (sample) => {
    setPrompt(sample);
    setResponse('');
  };

  const handleSubmit = async () => {
    setIsLoading(true);
    setError('');
    setResponse('');
    
    try {
      const formData = new FormData();
      formData.append('prompt', prompt || '');
      formData.append('generate_pdf', generatePdf);
      formData.append('mode', mode);
      
      if (file) {
        formData.append('file', file);
      }

      const response = await fetch('http://localhost:8000/ask-ai/', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        if (generatePdf) {
          // Handle PDF response
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = `complite_report_${mode}_${new Date().toISOString().split('T')[0]}.pdf`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          window.URL.revokeObjectURL(url);
          
          // Set a success message since we can't get the text response with PDF
          setResponse('PDF report generated and downloaded successfully! Check your downloads folder.');
        } else {
          // Handle JSON response
          const data = await response.json();
          setResponse(data.response);
        }
        logAudit(`AI prompt submitted: "${prompt ? prompt.substring(0, 50) : 'No prompt'}"`);
      } else {
        // Handle error response
        try {
          const data = await response.json();
          // Handle specific error cases
          if (data.detail && data.detail.includes('quota') || data.detail && data.detail.includes('429')) {
            setError('OpenAI API quota exceeded. Please check your OpenAI account billing or try again later. You can also contact your administrator to upgrade the API plan.');
          } else if (data.detail && data.detail.includes('401')) {
            setError('OpenAI API key is invalid or expired. Please contact your administrator to update the API configuration.');
          } else if (data.detail && data.detail.includes('500')) {
            setError('Server error occurred. Please try again or contact support if the issue persists.');
          } else {
            setError(data.detail || 'An error occurred while processing your request. Please try again.');
          }
        } catch (jsonError) {
          // If we can't parse JSON, it might be a different type of error
          setError(`Server error (${response.status}): ${response.statusText}`);
        }
      }
    } catch (err) {
      console.error('Error:', err);
      if (err.message.includes('Failed to fetch')) {
        setError('Unable to connect to the server. Please check your internet connection and try again.');
      } else {
        setError('An unexpected error occurred. Please try again or contact support.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const openPanel = (type) => {
    if (!dashboardData) return;
    setPanelType(type);
    if (isSOX) {
      if (type === "high") setPanelItems(dashboardData.highList || []);
      if (type === "failed") setPanelItems(dashboardData.failedList || []);
      if (type === "overdue") setPanelItems(dashboardData.overdueList || []);
    } else if (isESG) {
      if (type === "critical") setPanelItems(dashboardData.criticalList || []);
      if (type === "failed") setPanelItems(dashboardData.failedList || []);
      if (type === "overdue") setPanelItems(dashboardData.overdueList || []);
    } else if (isSOC2) {
      if (type === "critical") setPanelItems(dashboardData.criticalList || []);
      if (type === "failed") setPanelItems(dashboardData.failedList || []);
      if (type === "overdue") setPanelItems(dashboardData.overdueList || []);
    } else {
      if (type === "failed") setPanelItems(dashboardData.failedList || []);
      if (type === "overdue") setPanelItems(dashboardData.overdueList || []);
    }
  };

  const getModeTitle = () => {
    return isSOX ? "SOX Compliance Assistant" : isESG ? "ESG Compliance Assistant" : isSOC2 ? "SOC 2 Compliance Assistant" : "ISO 27001 Compliance Assistant";
  };

  const getModeIcon = () => {
    return isSOX ? "📊" : isESG ? "🌱" : isSOC2 ? "🔒" : "🛡️";
  };

  // Helper for heatmap colors
  const getHeatColor = (value) => {
    if (value > 80) return '#007BA7';
    if (value > 60) return '#4FC3F7';
    if (value > 40) return '#81D4FA';
    if (value > 20) return '#B3E5FC';
    return '#E1F5FE';
  };

  // Fetch analytics data when tab or file changes
  useEffect(() => {
    if (!showAnalytics || !file) return;
    const fetchAnalytics = async () => {
      setAnalyticsLoading(true);
      let endpoint = '';
      switch (analyticsTab) {
        case 'trends': endpoint = '/analytics/trends/'; break;
        case 'owner': endpoint = '/analytics/owner-performance/'; break;
        case 'benchmarks': endpoint = '/analytics/benchmarks/'; break;
        case 'root': endpoint = '/analytics/root-cause/'; break;
        case 'heatmap': endpoint = '/analytics/heatmap/'; break;
        case 'cross': endpoint = '/analytics/cross-framework/'; break;
        default: endpoint = '/analytics/trends/';
      }
      const formData = new FormData();
      formData.append('file', file);
      formData.append('mode', mode);
      const res = await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST',
        body: formData,
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await res.json();
      setAnalyticsData(data);
      setAnalyticsLoading(false);
    };
    fetchAnalytics();
  }, [showAnalytics, analyticsTab, file, mode]);

  return (
    <div className="upload-container">
      {/* Header */}
      <div className="upload-header">
        <div className="header-left">
          <button className="back-button" onClick={() => navigate('/')}>
            ← Back to Home
          </button>
          <div className="logo">CompLite</div>
        </div>
        <div className="header-right">
          <div className="mode-badge">{mode.toUpperCase()}</div>
          <div className="user-info">
            <span>Welcome back!</span>
            <button onClick={() => navigate('/')} className="logout-button">Logout</button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="upload-content">
        {/* Left Column - File Upload & Dashboard */}
        <div className="upload-section">
          <h2>📁 File Upload</h2>
          
          <div
            className={`upload-area ${isDragging ? 'dragover' : ''}`}
            onDrop={(e) => {
              e.preventDefault();
              setIsDragging(false);
              const droppedFile = e.dataTransfer.files[0];
              handleFileChange({ target: { files: [droppedFile] } });
            }}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onClick={() => document.getElementById('file-input').click()}
          >
            {!file ? (
              <>
                <div className="upload-icon">📄</div>
                <div className="upload-text">Drag & Drop CSV/Excel file here</div>
                <div className="upload-hint">or click to browse files</div>
                <input 
                  id="file-input"
                  type="file" 
                  accept=".csv,.xlsx,.xls" 
                  onChange={handleFileChange} 
                  className="file-input" 
                />
              </>
            ) : (
              <div className="file-info">
                <div className="upload-icon">✅</div>
                <div>
                  <div className="file-name">{file.name}</div>
                  <div className="file-size">{(file.size / 1024 / 1024).toFixed(2)} MB</div>
                </div>
                <button 
                  className="remove-file"
                  onClick={(e) => {
                    e.stopPropagation();
                    setFile(null);
                    setDashboardData(null);
                    setResponse('');
                  }}
                >
                  Remove
                </button>
              </div>
            )}
          </div>

          {/* Dashboard Cards */}
          {dashboardData && (
            <div className="dashboard-grid">
              <div className="dashboard-card">
                <div className="card-icon">📊</div>
                <div className="card-content">
                  <div className="card-value">{dashboardData.total}</div>
                  <div className="card-label">Total Items</div>
                </div>
              </div>
              
              {isSOX ? (
                <>
                  <div className="dashboard-card clickable" onClick={() => openPanel("high")}>
                    <div className="card-icon">⚠️</div>
                    <div className="card-content">
                      <div className="card-value">{dashboardData.high}</div>
                      <div className="card-label">High Risk</div>
                    </div>
                  </div>
                  <div className="dashboard-card clickable" onClick={() => openPanel("failed")}>
                    <div className="card-icon">❌</div>
                    <div className="card-content">
                      <div className="card-value">{dashboardData.failed}</div>
                      <div className="card-label">Failed</div>
                    </div>
                  </div>
                  <div className="dashboard-card clickable" onClick={() => openPanel("overdue")}>
                    <div className="card-icon">⏰</div>
                    <div className="card-content">
                      <div className="card-value">{dashboardData.overdue}</div>
                      <div className="card-label">Overdue</div>
                    </div>
                  </div>
                </>
              ) : isESG ? (
                <>
                  <div className="dashboard-card clickable" onClick={() => openPanel("critical")}>
                    <div className="card-icon">🚨</div>
                    <div className="card-content">
                      <div className="card-value">{dashboardData.critical}</div>
                      <div className="card-label">Critical</div>
                    </div>
                  </div>
                  <div className="dashboard-card clickable" onClick={() => openPanel("failed")}>
                    <div className="card-icon">❌</div>
                    <div className="card-content">
                      <div className="card-value">{dashboardData.failed}</div>
                      <div className="card-label">Failed</div>
                    </div>
                  </div>
                  <div className="dashboard-card clickable" onClick={() => openPanel("overdue")}>
                    <div className="card-icon">⏰</div>
                    <div className="card-content">
                      <div className="card-value">{dashboardData.overdue}</div>
                      <div className="card-label">Overdue</div>
                    </div>
                  </div>
                </>
              ) : isSOC2 ? (
                <>
                  <div className="dashboard-card clickable" onClick={() => openPanel("critical")}>
                    <div className="card-icon">🔒</div>
                    <div className="card-content">
                      <div className="card-value">{dashboardData.critical}</div>
                      <div className="card-label">Critical (CC)</div>
                    </div>
                  </div>
                  <div className="dashboard-card clickable" onClick={() => openPanel("failed")}>
                    <div className="card-icon">❌</div>
                    <div className="card-content">
                      <div className="card-value">{dashboardData.failed}</div>
                      <div className="card-label">Failed</div>
                    </div>
                  </div>
                  <div className="dashboard-card clickable" onClick={() => openPanel("overdue")}>
                    <div className="card-icon">⏰</div>
                    <div className="card-content">
                      <div className="card-value">{dashboardData.overdue}</div>
                      <div className="card-label">Overdue</div>
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <div className="dashboard-card clickable" onClick={() => openPanel("failed")}>
                    <div className="card-icon">❌</div>
                    <div className="card-content">
                      <div className="card-value">{dashboardData.failed}</div>
                      <div className="card-label">Failed</div>
                    </div>
                  </div>
                  <div className="dashboard-card clickable" onClick={() => openPanel("overdue")}>
                    <div className="card-icon">⏰</div>
                    <div className="card-content">
                      <div className="card-value">{dashboardData.overdue}</div>
                      <div className="card-label">Overdue</div>
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {/* Anomaly Alert */}
          {anomalies.length > 0 && (
            <div className="alert-banner">
              <div className="alert-icon">⚠️</div>
              <div className="alert-content">
                <div className="alert-title">Anomalies Detected</div>
                <div className="alert-description">{anomalies.length} anomalies found in your data</div>
              </div>
              <button 
                className="alert-button"
                onClick={() => setShowAnomalyPanel(true)}
              >
                View Details
              </button>
            </div>
          )}

          {/* Real-time Alerts */}
          {alerts.length > 0 && (
            <div className="alerts-section">
              <h3>⚡ Real-time Alerts</h3>
              <div className="alerts-list">
                {alerts.map((alert, i) => (
                  <div key={i} className="alert-item">
                    <div className="alert-dot"></div>
                    <span>{alert}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column - AI Chat */}
        <div className="chat-section">
          <h2>🤖 AI Assistant</h2>
          
          {file && (
            <>
              {/* Prompt Suggestions */}
              <div className="prompt-suggestions">
                <h4>Quick Prompts</h4>
                <div className="suggestions-grid">
                  {samplePrompts.map((text, i) => (
                    <button 
                      key={i} 
                      className="suggestion-button"
                      onClick={() => handlePromptClick(text)}
                    >
                      {text}
                    </button>
                  ))}
                </div>
              </div>

              {/* Chat Messages */}
              <div className="chat-messages">
                {response && (
                  <div className="message assistant">
                    <div className="message-header">
                      <span className="message-avatar">🤖</span>
                      <span className="message-sender">AI Assistant</span>
                    </div>
                    <div className="message-content">{response}</div>
                  </div>
                )}
                {error && (
                  <div className="message error">
                    <div className="message-header">
                      <span className="message-avatar">⚠️</span>
                      <span className="message-sender">Error</span>
                    </div>
                    <div className="message-content">
                      <div className="error-message-content">
                        <p>{error}</p>
                        {error.includes('quota') && (
                          <div className="error-help">
                            <h5>What you can do:</h5>
                            <ul>
                              <li>Check your OpenAI account billing at <a href="https://platform.openai.com/account/billing" target="_blank" rel="noopener noreferrer">platform.openai.com</a></li>
                              <li>Upgrade your OpenAI plan to increase usage limits</li>
                              <li>Wait until your quota resets (usually monthly)</li>
                              <li>Contact your system administrator</li>
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Chat Input */}
              <div className="chat-input-container">
                <div className="input-help">
                  💡 <strong>Tip:</strong> You can generate a comprehensive PDF report without entering a prompt, or ask specific questions for targeted analysis.
                </div>
                <textarea
                  className="chat-input"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder={`Ask a question about your ${mode.toUpperCase()} data (optional)...`}
                  rows={3}
                />
                <div className="chat-controls">
                  <label className="pdf-checkbox">
                    <input
                      type="checkbox"
                      checked={generatePdf}
                      onChange={(e) => setGeneratePdf(e.target.checked)}
                    />
                    <span>Generate PDF</span>
                  </label>
                  <button 
                    className="send-button"
                    onClick={handleSubmit}
                    disabled={isLoading}
                  >
                    {isLoading ? 'Processing...' : (generatePdf ? 'Generate Report' : 'Send')}
                  </button>
                </div>
              </div>
            </>
          )}

          {!file && (
            <div className="empty-state">
              <div className="empty-icon">📁</div>
              <div className="empty-title">Upload a file to start</div>
              <div className="empty-description">
                Upload your compliance data to begin analyzing with AI
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Advanced Analytics Section */}
      {file && (
        <div className="analytics-section">
          <div className="analytics-header">
            <h2>📈 Advanced Analytics</h2>
            <button 
              className="analytics-toggle"
              onClick={() => setShowAnalytics(v => !v)}
            >
              {showAnalytics ? 'Hide Analytics' : 'Show Analytics'}
            </button>
          </div>
          
          {showAnalytics && (
            <div className="analytics-content">
              <div className="analytics-tabs">
                <button 
                  className={`tab-button ${analyticsTab === 'trends' ? 'active' : ''}`}
                  onClick={() => setAnalyticsTab('trends')}
                >
                  Trends
                </button>
                <button 
                  className={`tab-button ${analyticsTab === 'owner' ? 'active' : ''}`}
                  onClick={() => setAnalyticsTab('owner')}
                >
                  Owner Performance
                </button>
                <button 
                  className={`tab-button ${analyticsTab === 'benchmarks' ? 'active' : ''}`}
                  onClick={() => setAnalyticsTab('benchmarks')}
                >
                  Benchmarks
                </button>
                <button 
                  className={`tab-button ${analyticsTab === 'root' ? 'active' : ''}`}
                  onClick={() => setAnalyticsTab('root')}
                >
                  Root Cause
                </button>
                <button 
                  className={`tab-button ${analyticsTab === 'heatmap' ? 'active' : ''}`}
                  onClick={() => setAnalyticsTab('heatmap')}
                >
                  Heatmap
                </button>
                <button 
                  className={`tab-button ${analyticsTab === 'cross' ? 'active' : ''}`}
                  onClick={() => setAnalyticsTab('cross')}
                >
                  Cross-Framework
                </button>
              </div>

              <div className="analytics-panel">
                {analyticsLoading ? (
                  <div className="loading">Loading analytics...</div>
                ) : (
                  <>
                    {/* Trends Tab */}
                    {analyticsTab === 'trends' && analyticsData.trends && (
                      <div className="trends-content">
                        <h4>Trend Analysis</h4>
                        <div className="trends-grid">
                          {Object.keys(analyticsData.trends).map(key => {
                            const trendArr = Object.entries(analyticsData.trends[key]).map(([k, v]) => ({ name: k, value: v }));
                            return (
                              <div key={key} className="trend-card">
                                <div className="trend-header">
                                  <span className="trend-title">{key.replace(/_/g, ' ')}</span>
                                  <button 
                                    className="trend-details-button"
                                    onClick={() => setAnalyticsModal({ type: 'trends', key })}
                                  >
                                    Details
                                  </button>
                                </div>
                                <ResponsiveContainer width="100%" height={60}>
                                  <LineChart data={trendArr} margin={{ left: 0, right: 0, top: 5, bottom: 5 }}>
                                    <Line type="monotone" dataKey="value" stroke="var(--primary-blue)" strokeWidth={2} dot={false} />
                                    <XAxis dataKey="name" hide />
                                    <YAxis hide />
                                  </LineChart>
                                </ResponsiveContainer>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Owner Performance Tab */}
                    {analyticsTab === 'owner' && analyticsData.owner_performance && (
                      <div className="owner-content">
                        <h4>Owner Performance Analysis</h4>
                        <div className="chart-container">
                          <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={Object.entries(analyticsData.owner_performance).map(([owner, stats]) => ({ owner, ...stats }))}>
                              <CartesianGrid strokeDasharray="3 3" stroke="var(--neutral-200)" />
                              <XAxis dataKey="owner" stroke="var(--neutral-600)" />
                              <YAxis stroke="var(--neutral-600)" />
                              <Tooltip />
                              <Bar dataKey="total" fill="var(--primary-blue)" name="Total" />
                              <Bar dataKey="failed" fill="var(--error-red)" name="Failed" />
                              <Bar dataKey="overdue" fill="var(--warning-amber)" name="Overdue" />
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                        <div className="owner-list">
                          {Object.entries(analyticsData.owner_performance).map(([owner, stats]) => (
                            <div key={owner} className="owner-card">
                              <div className="owner-info">
                                <span className="owner-name">{owner}</span>
                                <span className="owner-stats">
                                  Total: {stats.total} | Failed: {stats.failed} | Overdue: {stats.overdue}
                                </span>
                              </div>
                              <button 
                                className="owner-details-button"
                                onClick={() => setAnalyticsModal({ type: 'owner', owner })}
                              >
                                View Details
                              </button>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Other tabs with clean styling */}
                    {analyticsTab === 'benchmarks' && analyticsData.benchmarks && (
                      <div className="benchmarks-content">
                        <h4>Benchmark Analysis</h4>
                        <div className="data-display">
                          <pre>{JSON.stringify(analyticsData.benchmarks, null, 2)}</pre>
                        </div>
                      </div>
                    )}

                    {analyticsTab === 'root' && analyticsData.root_cause && (
                      <div className="root-cause-content">
                        <h4>Root Cause Analysis</h4>
                        <div className="data-display">
                          <pre>{analyticsData.root_cause}</pre>
                        </div>
                      </div>
                    )}

                    {analyticsTab === 'cross' && analyticsData.cross_framework && (
                      <div className="cross-framework-content">
                        <h4>Cross-Framework Mapping</h4>
                        <div className="data-display">
                          <pre>{JSON.stringify(analyticsData.cross_framework, null, 2)}</pre>
                        </div>
                      </div>
                    )}

                    {/* Heatmap Tab */}
                    {analyticsTab === 'heatmap' && analyticsData.heatmap && (
                      <div className="heatmap-content">
                        <h4>Heatmap Analysis</h4>
                        <div className="heatmap-container">
                          {Object.entries(analyticsData.heatmap).map(([rowLabel, row], i) => (
                            <div key={rowLabel} className="heatmap-section">
                              <h5 className="heatmap-title">{rowLabel}</h5>
                              <div className="heatmap-description">
                                {rowLabel.includes('Risk') && 'Distribution of controls by risk level'}
                                {rowLabel.includes('ESG') && 'Distribution of ESG metrics by factor'}
                                {rowLabel.includes('Trust') && 'Distribution of SOC 2 controls by Trust Service Criteria'}
                                {rowLabel.includes('Status') && 'Distribution of controls by status'}
                                {!rowLabel.includes('Risk') && !rowLabel.includes('ESG') && !rowLabel.includes('Trust') && !rowLabel.includes('Status') && 
                                 'Distribution of items across different categories'}
                              </div>
                              
                              <div className="heatmap-grid">
                                {Object.entries(row).map(([colLabel, value], j) => (
                                  <div key={colLabel} className="heatmap-cell">
                                    <div className="heatmap-label">{colLabel}</div>
                                    <div 
                                      className="heatmap-value"
                                      style={{ background: getHeatColor(value) }}
                                      title={`${colLabel}: ${value} items`}
                                    >
                                      <span className="value-number">{value}</span>
                                      <span className="value-unit">items</span>
                                    </div>
                                  </div>
                                ))}
                              </div>
                              
                              <div className="heatmap-summary">
                                <div className="summary-stat">
                                  <span className="stat-label">Total Items:</span>
                                  <span className="stat-value">{Object.values(row).reduce((sum, val) => sum + val, 0)}</span>
                                </div>
                                <div className="summary-stat">
                                  <span className="stat-label">Categories:</span>
                                  <span className="stat-value">{Object.keys(row).length}</span>
                                </div>
                                <div className="summary-stat">
                                  <span className="stat-label">Highest Count:</span>
                                  <span className="stat-value">{Math.max(...Object.values(row))}</span>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Side Panels */}
      {panelType && (
        <div className="side-panel">
          <div className="panel-header">
            <h3>
              {isSOX ? (
                panelType === "high" ? "High Risk Controls" : 
                panelType === "failed" ? "Failed Controls" : "Overdue Controls"
              ) : isESG ? (
                panelType === "critical" ? "Critical ESG Metrics" : 
                panelType === "failed" ? "Failed ESG Metrics" : "Overdue ESG Metrics"
              ) : isSOC2 ? (
                panelType === "critical" ? "Critical SOC 2 Controls (CC)" : 
                panelType === "failed" ? "Failed SOC 2 Controls" : "Overdue SOC 2 Controls"
              ) : (
                panelType === "failed" ? "Failed Controls" : "Overdue Controls"
              )}
            </h3>
            <button className="close-button" onClick={() => setPanelType(null)}>×</button>
          </div>
          <div className="panel-content">
            {panelItems.map((item, i) => (
              <div key={i} className="panel-item">{item}</div>
            ))}
          </div>
        </div>
      )}

      {showAnomalyPanel && (
        <div className="side-panel">
          <div className="panel-header">
            <h3>Anomalies Detected</h3>
            <button className="close-button" onClick={() => setShowAnomalyPanel(false)}>×</button>
          </div>
          <div className="panel-content">
            {anomalies.map((anomaly, i) => (
              <div key={i} className="panel-item">{anomaly}</div>
            ))}
          </div>
        </div>
      )}

      {/* Analytics Modal */}
      {analyticsModal && (
        <div className="modal-overlay" onClick={() => setAnalyticsModal(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>
                {analyticsModal.type === 'trends' ? `Trend Details: ${analyticsModal.key.replace(/_/g, ' ')}` : 
                 analyticsModal.type === 'owner' ? `Owner Details: ${analyticsModal.owner}` : 'Analytics Details'}
              </h3>
              <button className="close-button" onClick={() => setAnalyticsModal(null)}>×</button>
            </div>
            <div className="modal-body">
              {analyticsModal.type === 'trends' && (
                <div>
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={Object.entries(analyticsData.trends[analyticsModal.key]).map(([k, v]) => ({ name: k, value: v }))}>
                      <Line type="monotone" dataKey="value" stroke="var(--primary-blue)" strokeWidth={2} />
                      <XAxis dataKey="name" stroke="var(--neutral-600)" />
                      <YAxis stroke="var(--neutral-600)" />
                      <Tooltip />
                    </LineChart>
                  </ResponsiveContainer>
                  <div className="data-display">
                    <pre>{JSON.stringify(analyticsData.trends[analyticsModal.key], null, 2)}</pre>
                  </div>
                </div>
              )}
              {analyticsModal.type === 'owner' && (
                <div>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={[analyticsData.owner_performance[analyticsModal.owner]]}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--neutral-200)" />
                      <XAxis dataKey="owner" stroke="var(--neutral-600)" />
                      <YAxis stroke="var(--neutral-600)" />
                      <Tooltip />
                      <Bar dataKey="total" fill="var(--primary-blue)" name="Total" />
                      <Bar dataKey="failed" fill="var(--error-red)" name="Failed" />
                      <Bar dataKey="overdue" fill="var(--warning-amber)" name="Overdue" />
                    </BarChart>
                  </ResponsiveContainer>
                  <div className="data-display">
                    <pre>{JSON.stringify(analyticsData.owner_performance[analyticsModal.owner], null, 2)}</pre>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Audit Trail Button */}
      <button className="audit-button" onClick={() => setShowAuditPanel(!showAuditPanel)}>
        🕵️ Audit Trail
      </button>

      {showAuditPanel && (
        <div className="audit-panel">
          <div className="panel-header">
            <h3>Audit Trail</h3>
            <button className="close-button" onClick={() => setShowAuditPanel(false)}>×</button>
          </div>
          <div className="panel-content">
            {auditTrail.map((entry, i) => (
              <div key={i} className="audit-item">{entry}</div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default UploadPage; 