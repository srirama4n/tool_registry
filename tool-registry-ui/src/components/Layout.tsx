import { Link, Outlet, useLocation } from 'react-router-dom'
import { Wrench, List, PlusCircle, Zap } from 'lucide-react'

export function Layout() {
  const loc = useLocation()
  return (
    <div className="layout">
      <header className="header">
        <Link to="/" className="logo">
          <Wrench size={28} strokeWidth={2} className="logo-icon" />
          <span>Tool Registry</span>
        </Link>
        <nav>
          <Link to="/" className={loc.pathname === '/' ? 'active' : ''}>
            <List size={18} />
            <span>Tools</span>
          </Link>
          <Link to="/tools/new" className={loc.pathname === '/tools/new' ? 'active' : ''}>
            <PlusCircle size={18} />
            <span>Register Tool</span>
          </Link>
          <Link to="/mcp-test" className={loc.pathname === '/mcp-test' ? 'active' : ''}>
            <Zap size={18} />
            <span>MCP Test</span>
          </Link>
        </nav>
      </header>
      <main className="main">
        <Outlet />
      </main>
    </div>
  )
}
