import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import { Send, Globe, Zap, Cpu, Search, Terminal } from 'lucide-react'

function App() {
  const [input, setInput] = useState('')
  const [selectedModel, setSelectedModel] = useState('gemini') // 'gemini' ou 'groq'
  // Estado para visualização na tela (UI simples)
  const [messages, setMessages] = useState([
    {
      role: 'model',
      text: 'Sistema MCP Online. Conectado ao Gemini 2.5 Flash.\nPronto para acessar suas ferramentas e APIs.'
    }
  ])
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(scrollToBottom, [messages])

  const handleSend = async () => {
    if (!input.trim()) return

    const userText = input
    setInput('')
    
    // 1. Atualiza UI imediatamente
    setMessages(prev => [...prev, { role: 'user', text: userText }])
    setLoading(true)

    try {
      // 2. Prepara o histórico no formato exato que o Gemini exige
      // Ignoramos a última mensagem do usuário pois ela vai no campo 'message'
      const historyForApi = messages.map(msg => ({
        role: msg.role,
        parts: [{ text: msg.text }]
      }))

      // 3. Envia para o nosso Backend MCP Host
      const response = await axios.post('/api/chat', {
        message: userText,
        history: historyForApi,
        model: selectedModel  // Envia o modelo selecionado
      })

      // 4. Recebe a resposta final (já processada pelas ferramentas)
      setMessages(prev => [...prev, { role: 'model', text: response.data.reply }])

    } catch (error) {
      console.error(error)
      setMessages(prev => [...prev, { 
        role: 'model', 
        text: '⚠️ Erro de conexão com o servidor MCP Host. Verifique se o terminal do Python está rodando.' 
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-screen bg-[#0d1117] text-gray-100 font-sans selection:bg-blue-500 selection:text-white">
      
      {/* --- Browser Address Bar --- */}
      <div className="bg-[#161b22] p-3 border-b border-gray-800 flex items-center gap-4 sticky top-0 z-10 shadow-md">
        <div className="flex gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500 hover:bg-red-600 transition-colors"></div>
          <div className="w-3 h-3 rounded-full bg-yellow-500 hover:bg-yellow-600 transition-colors"></div>
          <div className="w-3 h-3 rounded-full bg-green-500 hover:bg-green-600 transition-colors"></div>
        </div>
        
        {/* Fake URL Bar */}
        <div className="bg-[#0d1117] flex-1 rounded-md border border-gray-700 h-9 flex items-center px-3 text-sm text-gray-400 font-mono gap-2 relative group">
          <Zap size={14} className="text-yellow-400" />
          <span className="group-hover:text-gray-200 transition-colors">mcp://agent-browser/main</span>
        </div>

        {/* Status Indicators + Model Selector */}
        <div className="flex gap-3 text-xs text-gray-500 font-mono">
          {/* Model Selector */}
          <div className="flex items-center gap-0 rounded bg-gray-800/50 overflow-hidden">
            <button
              onClick={() => setSelectedModel('gemini')}
              className={`px-3 py-1 transition-all ${
                selectedModel === 'gemini'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              <Zap size={12} className="inline mr-1" />
              GEMINI
            </button>
            <button
              onClick={() => setSelectedModel('groq')}
              className={`px-3 py-1 transition-all ${
                selectedModel === 'groq'
                  ? 'bg-purple-600 text-white'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              <Terminal size={12} className="inline mr-1" />
              GROQ
            </button>
          </div>

          <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-gray-800/50">
            <Cpu size={12} className="text-blue-400" />
            <span>MCP HOST</span>
          </div>
          <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-gray-800/50">
            <Globe size={12} className="text-green-400" />
            <span>ONLINE</span>
          </div>
        </div>
      </div>

      {/* --- Main Content Area --- */}
      <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6 scroll-smooth">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            
            {/* Avatar / Icon */}
            {msg.role === 'model' && (
              <div className="w-8 h-8 rounded-full bg-blue-600/20 flex items-center justify-center mr-3 mt-1 border border-blue-500/30">
                <Terminal size={16} className="text-blue-400" />
              </div>
            )}

            {/* Message Bubble */}
            <div className={`max-w-[85%] md:max-w-[70%] p-4 rounded-2xl shadow-sm ${
              msg.role === 'user' 
                ? 'bg-blue-600 text-white rounded-tr-sm' 
                : 'bg-[#161b22] text-gray-200 rounded-tl-sm border border-gray-800'
            }`}>
              <p className="whitespace-pre-wrap leading-relaxed text-sm md:text-base font-medium">
                {msg.text}
              </p>
            </div>
          </div>
        ))}

        {/* Loading State */}
        {loading && (
          <div className="flex justify-start animate-pulse">
             <div className="w-8 h-8 rounded-full bg-blue-600/20 flex items-center justify-center mr-3 mt-1 border border-blue-500/30">
                <Terminal size={16} className="text-blue-400" />
              </div>
            <div className="bg-[#161b22] p-4 rounded-2xl rounded-tl-sm border border-gray-800 flex items-center gap-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></span>
                <span className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></span>
                <span className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></span>
              </div>
              <span className="text-xs text-gray-500 font-mono">Executando ferramentas...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* --- Input Area --- */}
      <div className="p-4 bg-[#161b22] border-t border-gray-800">
        <div className="max-w-4xl mx-auto relative">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Digite um comando para as APIs..."
            className="w-full bg-[#0d1117] text-gray-200 border border-gray-700 rounded-xl pl-5 pr-14 py-4 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all placeholder:text-gray-600 font-medium"
            disabled={loading}
          />
          <button 
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="absolute right-2 top-2 bottom-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:hover:bg-blue-600 text-white p-2.5 rounded-lg transition-all"
          >
            {loading ? <Search size={20} className="animate-spin" /> : <Send size={20} />}
          </button>
        </div>
        <div className="text-center mt-3 text-xs text-gray-600 font-mono">
          Powered by Gemini 2.5 & MCP Protocol
        </div>
      </div>
    </div>
  )
}

export default App