import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
import { ToolList } from './pages/ToolList'
import { ToolDetail } from './pages/ToolDetail'
import { ToolForm } from './pages/ToolForm'
import { McpTest } from './pages/McpTest'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<ToolList />} />
          <Route path="tools/new" element={<ToolForm />} />
          <Route path="tools/:name" element={<ToolDetail />} />
          <Route path="tools/:name/edit" element={<ToolForm />} />
          <Route path="mcp-test" element={<McpTest />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
