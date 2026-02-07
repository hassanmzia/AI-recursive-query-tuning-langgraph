import React, { useEffect } from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { useAppStore } from '../store';
import { wsService } from '../services/websocket';

const navItems = [
  { path: '/chat', icon: '\u{1F4AC}', label: 'Query & Answer' },
  { path: '/dashboard', icon: '\u{1F4CA}', label: 'Dashboard' },
  { path: '/workflow', icon: '\u{1F504}', label: 'Workflow Viz' },
  { path: '/documents', icon: '\u{1F4C4}', label: 'Documents' },
  { path: '/agents', icon: '\u{1F916}', label: 'Agents & MCP' },
  { path: '/history', icon: '\u{1F4CB}', label: 'History' },
];

export default function Layout() {
  const wsConnected = useAppStore((s) => s.wsConnected);
  const setWsConnected = useAppStore((s) => s.setWsConnected);
  const location = useLocation();

  useEffect(() => {
    wsService.connect();
    const unsub = wsService.on('connection_status', (msg) => {
      setWsConnected(msg.connected);
    });
    return () => { unsub(); wsService.disconnect(); };
  }, [setWsConnected]);

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-logo">
            RQT Engine
            <span>Recursive Query Tuning</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon">{item.icon}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span className={`status-dot ${wsConnected ? 'online' : 'offline'}`} />
            <span>{wsConnected ? 'Connected' : 'Disconnected'}</span>
          </div>
          <div style={{ marginTop: 6, fontSize: 11, opacity: 0.6 }}>
            LangGraph + Multi-Agent
          </div>
        </div>
      </aside>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
