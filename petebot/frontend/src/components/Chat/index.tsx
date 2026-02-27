import { useState } from 'react'
import { Send } from 'lucide-react'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: 'Hello! I\'m your AI assistant. How can I help you today?' }
  ])
  const [input, setInput] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return

    const userMessage: Message = { role: 'user', content: input }
    setMessages([...messages, userMessage])
    setInput('')

    // TODO: Send to API and get response
    setTimeout(() => {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'I received your message. Let me help you with that...'
      }])
    }, 1000)
  }

  return (
    <div className="stack">
      <div>
        <h1 className="page-title">AI Chat</h1>
        <p className="page-subtitle mt-1">Chat with your AI assistant</p>
      </div>

      <div className="card p-4 sm:p-6">
        {/* Messages */}
        <div className="h-[48vh] min-h-[16rem] max-h-[calc(100vh-19rem)] overflow-y-auto space-y-4 pr-1 sm:h-[54vh] lg:max-h-[calc(100vh-16rem)]">
          {messages.map((message, i) => (
            <div
              key={i}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] rounded-2xl p-4 sm:max-w-[80%] ${
                  message.role === 'user'
                    ? 'bg-primary-600 text-white'
                    : 'glass'
                }`}
              >
                <p className="table-text whitespace-pre-wrap">{message.content}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Input */}
        <form onSubmit={handleSubmit} className="mt-4">
          <div className="glass p-2 flex items-center gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message..."
              className="flex-1 bg-transparent border-none outline-none px-4 py-2 muted-text placeholder:text-white/50"
            />
            <button
              type="submit"
              className="btn-primary p-3 rounded-xl"
              disabled={!input.trim()}
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
