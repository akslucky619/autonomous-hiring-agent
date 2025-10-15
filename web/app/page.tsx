'use client'

import { useState, useEffect } from 'react'
import { Bot, Upload, Target, TrendingUp, Workflow, Settings, Eye } from 'lucide-react'
import axios from 'axios'

const N8N_URL = process.env.NEXT_PUBLIC_N8N_URL || 'http://localhost:5678'

interface WorkflowStatus {
  id: string
  name: string
  active: boolean
  triggerCount: number
}

export default function Home() {
  const [activeTab, setActiveTab] = useState('agent')
  const [workflows, setWorkflows] = useState<WorkflowStatus[]>([])
  const [loading, setLoading] = useState(false)

  const tabs = [
    { id: 'agent', label: 'AI Agent', icon: Bot, description: 'Autonomous hiring workflows' },
    { id: 'upload', label: 'Resume Upload', icon: Upload, description: 'Process resume files' },
    { id: 'ranking', label: 'Candidate Ranking', icon: TrendingUp, description: 'Rank and filter candidates' },
    { id: 'workflows', label: 'n8n Workflows', icon: Workflow, description: 'View and manage workflows' },
    { id: 'settings', label: 'Settings', icon: Settings, description: 'Configure system' },
  ]

  const renderTabContent = () => {
    switch (activeTab) {
      case 'agent':
        return <AgentDashboard />
      case 'upload':
        return <ResumeUpload />
      case 'ranking':
        return <CandidateRanking />
      case 'workflows':
        return <WorkflowManager />
      case 'settings':
        return <SettingsPanel />
      default:
        return null
    }
  }

  return (
    <div className="space-y-6">
      {/* Header Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Bot className="h-8 w-8 text-n8n-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">AI Agent</p>
              <p className="text-2xl font-semibold text-gray-900">Active</p>
            </div>
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Workflow className="h-8 w-8 text-primary-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Workflows</p>
              <p className="text-2xl font-semibold text-gray-900">3</p>
            </div>
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Target className="h-8 w-8 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Active Goals</p>
              <p className="text-2xl font-semibold text-gray-900">0</p>
            </div>
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <TrendingUp className="h-8 w-8 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Executions</p>
              <p className="text-2xl font-semibold text-gray-900">0</p>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-n8n-500 text-n8n-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="h-5 w-5 mr-2" />
                {tab.label}
              </button>
            )
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {renderTabContent()}
      </div>
    </div>
  )
}

// Agent Dashboard Component
function AgentDashboard() {
  const [goals, setGoals] = useState<any[]>([])
  const [showCreateGoal, setShowCreateGoal] = useState(false)
  const [newGoal, setNewGoal] = useState({
    title: '',
    description: '',
    target_positions: 1,
    priority: 'medium'
  })

  const createGoal = async () => {
    if (!newGoal.title || !newGoal.description) {
      alert('Please fill in title and description')
      return
    }

    try {
      const response = await axios.post(`${N8N_URL}/webhook/create-goal`, newGoal)
      alert('Goal created! AI agent is now working autonomously.')
      setNewGoal({ title: '', description: '', target_positions: 1, priority: 'medium' })
      setShowCreateGoal(false)
    } catch (error) {
      console.error('Error creating goal:', error)
      alert('Error creating goal. Make sure n8n is running.')
    }
  }

  return (
    <div className="space-y-6">
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Autonomous AI Agent</h2>
          <button
            onClick={() => setShowCreateGoal(!showCreateGoal)}
            className="btn-n8n"
          >
            Create Goal
          </button>
        </div>
        
        <p className="text-gray-600 mb-6">
          The AI agent works autonomously to achieve your hiring goals. Create a goal and watch it:
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="workflow-node">
            <Target className="h-6 w-6 text-green-600 mb-2" />
            <h3 className="font-medium text-gray-900">Analyze Requirements</h3>
            <p className="text-sm text-gray-600">Extract skills and criteria from your goal</p>
          </div>
          <div className="workflow-node">
            <TrendingUp className="h-6 w-6 text-blue-600 mb-2" />
            <h3 className="font-medium text-gray-900">Search & Rank</h3>
            <p className="text-sm text-gray-600">Find and score candidates automatically</p>
          </div>
          <div className="workflow-node">
            <Bot className="h-6 w-6 text-purple-600 mb-2" />
            <h3 className="font-medium text-gray-900">Send Outreach</h3>
            <p className="text-sm text-gray-600">Generate and send personalized messages</p>
          </div>
        </div>

        {showCreateGoal && (
          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="text-md font-medium text-gray-900 mb-4">Create New Hiring Goal</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Goal Title *
                </label>
                <input
                  type="text"
                  value={newGoal.title}
                  onChange={(e) => setNewGoal(prev => ({ ...prev, title: e.target.value }))}
                  className="input-field"
                  placeholder="e.g., Hire 3 Senior Python Developers"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description *
                </label>
                <textarea
                  value={newGoal.description}
                  onChange={(e) => setNewGoal(prev => ({ ...prev, description: e.target.value }))}
                  rows={3}
                  className="input-field"
                  placeholder="Describe the role requirements, skills needed, and any specific criteria..."
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Target Positions
                  </label>
                  <input
                    type="number"
                    value={newGoal.target_positions}
                    onChange={(e) => setNewGoal(prev => ({ ...prev, target_positions: parseInt(e.target.value) || 1 }))}
                    min="1"
                    className="input-field"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Priority
                  </label>
                  <select
                    value={newGoal.priority}
                    onChange={(e) => setNewGoal(prev => ({ ...prev, priority: e.target.value }))}
                    className="input-field"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                </div>
              </div>
              
              <div className="flex justify-end space-x-2">
                <button
                  onClick={() => setShowCreateGoal(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  onClick={createGoal}
                  className="btn-n8n"
                >
                  Create Goal
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// Resume Upload Component
function ResumeUpload() {
  return (
    <div className="space-y-6">
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Resume Upload</h2>
        <p className="text-gray-600 mb-4">
          Upload resumes to be processed by the n8n workflow. The system will:
        </p>
        
        <div className="space-y-3">
          <div className="flex items-center space-x-3">
            <div className="w-6 h-6 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-sm">1</div>
            <span className="text-gray-700">Extract text from PDF files</span>
          </div>
          <div className="flex items-center space-x-3">
            <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm">2</div>
            <span className="text-gray-700">Normalize skills and extract structured data</span>
          </div>
          <div className="flex items-center space-x-3">
            <div className="w-6 h-6 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center text-sm">3</div>
            <span className="text-gray-700">Generate AI embeddings for semantic search</span>
          </div>
          <div className="flex items-center space-x-3">
            <div className="w-6 h-6 bg-orange-100 text-orange-600 rounded-full flex items-center justify-center text-sm">4</div>
            <span className="text-gray-700">Store candidate data in database</span>
          </div>
        </div>
        
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-600">
            <strong>Webhook URL:</strong> <code>{N8N_URL}/webhook/upload-resume</code>
          </p>
          <p className="text-sm text-gray-600 mt-1">
            Use this endpoint to upload resumes programmatically or integrate with other systems.
          </p>
        </div>
      </div>
    </div>
  )
}

// Candidate Ranking Component
function CandidateRanking() {
  return (
    <div className="space-y-6">
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Candidate Ranking</h2>
        <p className="text-gray-600 mb-4">
          The AI-powered ranking system evaluates candidates using multiple factors:
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="font-medium text-gray-900 mb-3">Scoring Factors</h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Semantic Similarity</span>
                <span className="text-sm font-medium text-gray-900">40%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Skill Overlap</span>
                <span className="text-sm font-medium text-gray-900">30%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Experience Match</span>
                <span className="text-sm font-medium text-gray-900">20%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Recency Bonus</span>
                <span className="text-sm font-medium text-gray-900">10%</span>
              </div>
            </div>
          </div>
          
          <div>
            <h3 className="font-medium text-gray-900 mb-3">Filtering Options</h3>
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-sm text-gray-600">Location matching</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <span className="text-sm text-gray-600">Experience requirements</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                <span className="text-sm text-gray-600">Work authorization</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                <span className="text-sm text-gray-600">Custom criteria</span>
              </div>
            </div>
          </div>
        </div>
        
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-600">
            <strong>Ranking Webhook:</strong> <code>{N8N_URL}/webhook/rank-candidates</code>
          </p>
          <p className="text-sm text-gray-600 mt-1">
            Send JD ID and optional filters to get ranked candidate results.
          </p>
        </div>
      </div>
    </div>
  )
}

// Workflow Manager Component
function WorkflowManager() {
  return (
    <div className="space-y-6">
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">n8n Workflows</h2>
        
        <div className="space-y-4">
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-medium text-gray-900">Resume Processing Pipeline</h3>
                <p className="text-sm text-gray-600">Processes uploaded resumes and extracts candidate data</p>
              </div>
              <div className="flex items-center space-x-2">
                <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">Active</span>
                <a href={`${N8N_URL}/workflow/resume-processing`} target="_blank" rel="noopener noreferrer">
                  <Eye className="h-4 w-4 text-gray-400 hover:text-gray-600" />
                </a>
              </div>
            </div>
          </div>
          
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-medium text-gray-900">Candidate Ranking Pipeline</h3>
                <p className="text-sm text-gray-600">Ranks and filters candidates based on job requirements</p>
              </div>
              <div className="flex items-center space-x-2">
                <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">Active</span>
                <a href={`${N8N_URL}/workflow/candidate-ranking`} target="_blank" rel="noopener noreferrer">
                  <Eye className="h-4 w-4 text-gray-400 hover:text-gray-600" />
                </a>
              </div>
            </div>
          </div>
          
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-medium text-gray-900">AI Agent - Autonomous Hiring</h3>
                <p className="text-sm text-gray-600">Autonomous agent that works toward hiring goals</p>
              </div>
              <div className="flex items-center space-x-2">
                <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">Active</span>
                <a href={`${N8N_URL}/workflow/ai-agent-autonomous`} target="_blank" rel="noopener noreferrer">
                  <Eye className="h-4 w-4 text-gray-400 hover:text-gray-600" />
                </a>
              </div>
            </div>
          </div>
        </div>
        
        <div className="mt-6">
          <a href={N8N_URL} target="_blank" rel="noopener noreferrer" className="btn-n8n">
            Open n8n Editor
          </a>
        </div>
      </div>
    </div>
  )
}

// Settings Panel Component
function SettingsPanel() {
  return (
    <div className="space-y-6">
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">System Configuration</h2>
        
        <div className="space-y-6">
          <div>
            <h3 className="font-medium text-gray-900 mb-2">n8n Configuration</h3>
            <div className="space-y-2">
              <div>
                <label className="block text-sm font-medium text-gray-700">n8n URL</label>
                <input
                  type="text"
                  value={N8N_URL}
                  readOnly
                  className="input-field bg-gray-50"
                />
              </div>
            </div>
          </div>
          
          <div>
            <h3 className="font-medium text-gray-900 mb-2">Database Configuration</h3>
            <div className="space-y-2">
              <div>
                <label className="block text-sm font-medium text-gray-700">PostgreSQL</label>
                <input
                  type="text"
                  value="postgresql://postgres:password@postgres:5432/hiring_automation"
                  readOnly
                  className="input-field bg-gray-50"
                />
              </div>
            </div>
          </div>
          
          <div>
            <h3 className="font-medium text-gray-900 mb-2">AI Services</h3>
            <div className="space-y-2">
              <div>
                <label className="block text-sm font-medium text-gray-700">Ollama Embeddings</label>
                <input
                  type="text"
                  value="http://ollama:11434"
                  readOnly
                  className="input-field bg-gray-50"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Text Extraction</label>
                <input
                  type="text"
                  value="http://text-extract:8001"
                  readOnly
                  className="input-field bg-gray-50"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
