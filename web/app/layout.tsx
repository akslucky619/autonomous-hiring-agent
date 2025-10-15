import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'n8n AI Hiring Agent',
  description: 'Autonomous hiring automation powered by n8n workflows',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen bg-gray-50">
          <nav className="bg-white shadow-sm border-b">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between h-16">
                <div className="flex items-center">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-n8n-500 rounded-lg flex items-center justify-center">
                      <span className="text-white font-bold text-sm">n8n</span>
                    </div>
                    <h1 className="text-xl font-bold text-gray-900">
                      AI Hiring Agent
                    </h1>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <span className="text-sm text-gray-500">Powered by n8n Workflows</span>
                  <a 
                    href="http://localhost:5678" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="btn-n8n text-sm"
                  >
                    Open n8n
                  </a>
                </div>
              </div>
            </div>
          </nav>
          <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}
