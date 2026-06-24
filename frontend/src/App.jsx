import React, { useState, useEffect, useRef } from 'react';
import './App.css';

// Generate session ID for conversation persistence
const generateSessionId = () => {
  return 'sess_' + Math.random().toString(36).substring(2, 11);
};

function App() {
  const [messages, setMessages] = useState([
    {
      text: "Hello! I am your Ayurcare Agent. To guide you, I will collect some details about your symptoms and lifestyle.\n\nTo begin, what main symptoms are you experiencing today?",
      sender: 'agent',
      isWarning: false
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => generateSessionId());
  
  // Dosha state: Vata, Pitta, Kapha breakdown
  const [doshaState, setDoshaState] = useState(null);
  
  const messagesEndRef = useRef(null);

  // Auto scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleDownloadReport = () => {
    const currentSessionId = sessionId;
    if (!currentSessionId || !doshaState) return;
    const downloadUrl = '/api/download_report?session_id=' + currentSessionId;
    window.open(downloadUrl, '_blank');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { text: userMessage, sender: 'user', isWarning: false }]);
    setLoading(true);

    const API_URL = import.meta.env.VITE_API_URL || '';

    try {
      const response = await fetch(`${API_URL}/api/agent`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          session_id: sessionId
        })
      });

      if (!response.ok) {
        throw new Error("Failed to contact the wellness assistant");
      }

      const data = await response.json();
      
      const isSafetyWarning = data.reply.includes("SAFETY WARNING:") || data.reply.includes("emergency care") || data.reply.includes("see a doctor");

      setMessages((prev) => [...prev, {
        text: data.reply,
        sender: 'agent',
        isWarning: isSafetyWarning
      }]);

      if (data.dosha_state) {
        setDoshaState(data.dosha_state);
      }

    } catch (error) {
      setMessages((prev) => [...prev, {
        text: "I apologize, but I encountered an error connecting to the wellness engine. Please try again later.",
        sender: 'agent',
        isWarning: true
      }]);
    } finally {
      setLoading(false);
    }
  };

  // Helper to map dosha strength from Prakriti JSON to percentage heights
  const getDoshaHeight = (doshaName) => {
    if (!doshaState || !doshaState.constitution_breakdown) {
      return '15%'; // Default resting/breathing height
    }
    const val = doshaState.constitution_breakdown[doshaName];
    if (!val) return '15%';
    
    // Support either descriptive tags (High/Medium/Low) or quantitative values
    const stringVal = String(val).toLowerCase();
    if (stringVal.includes('high') || stringVal === 'h') return '95%';
    if (stringVal.includes('medium') || stringVal === 'med' || stringVal === 'm') return '60%';
    if (stringVal.includes('low') || stringVal === 'l') return '25%';
    
    // Support raw numbers or percentages
    const numVal = parseInt(stringVal);
    if (!isNaN(numVal)) {
      return `${Math.min(Math.max(numVal, 15), 100)}%`;
    }
    return '15%';
  };

  const isDoshaActive = (doshaName) => {
    if (!doshaState || !doshaState.dominant_dosha) return false;
    return doshaState.dominant_dosha.toLowerCase().includes(doshaName.toLowerCase());
  };

  return (
    <div className="app-container">
      {/* Signature Vertical Pulse Bars Panel */}
      <div className="pulse-bars-panel">
        <div className="panel-title">Constitutional Pulse</div>
        <div className="bars-container">
          {/* Vata Bar */}
          <div className="pulse-bar-wrapper vata">
            <div className="pulse-bar-track">
              <div className="pulse-bar-fill" style={{ height: getDoshaHeight('Vata') }}></div>
            </div>
            <div className={`pulse-bar-label ${isDoshaActive('Vata') ? 'active' : ''}`}>Vata</div>
          </div>

          {/* Pitta Bar */}
          <div className="pulse-bar-wrapper pitta">
            <div className="pulse-bar-track">
              <div className="pulse-bar-fill" style={{ height: getDoshaHeight('Pitta') }}></div>
            </div>
            <div className={`pulse-bar-label ${isDoshaActive('Pitta') ? 'active' : ''}`}>Pitta</div>
          </div>

          {/* Kapha Bar */}
          <div className="pulse-bar-wrapper kapha">
            <div className="pulse-bar-track">
              <div className="pulse-bar-fill" style={{ height: getDoshaHeight('Kapha') }}></div>
            </div>
            <div className={`pulse-bar-label ${isDoshaActive('Kapha') ? 'active' : ''}`}>Kapha</div>
          </div>
        </div>
      </div>

      {/* Main Chat Interface */}
      <div className="main-chat-container">
        <div className="header">
          <h1>Ayurcare Guidance</h1>
          <span>Wellness Session</span>
        </div>

        <div className="messages-list">
          {messages.map((msg, index) => (
            <div 
              key={index} 
              className={`message-wrapper ${msg.sender} ${msg.isWarning ? 'safety-warning' : ''}`}
            >
              <div className="message-bubble">{msg.text}</div>
              <div className="message-meta">{msg.sender}</div>
            </div>
          ))}
          
          {loading && (
            <div className="loading-wrapper">
              <div className="dot-pulse">
                <div className="dot"></div>
                <div className="dot"></div>
                <div className="dot"></div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {doshaState && (
          <div className="download-report-container">
            <button 
              onClick={handleDownloadReport}
              className="download-button"
            >
              Download Weekly Wellness Report
            </button>
          </div>
        )}

        <form onSubmit={handleSubmit} className="input-form">
          <input
            type="text"
            className="message-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your reply..."
            disabled={loading}
            maxLength={500}
          />
          <button 
            type="submit" 
            className="send-button"
            disabled={loading || !input.trim()}
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;
