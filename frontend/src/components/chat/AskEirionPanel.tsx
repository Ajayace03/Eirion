import { useState, useRef, useEffect } from "react";
import { MessageSquare, X, Send, Bot, User } from "lucide-react";
import { useWizardStore } from "../../store/wizardStore";

interface Message {
  role: "user" | "eirion";
  text: string;
}

export default function AskEirionPanel() {
  const { analysisResult } = useWizardStore();
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    { role: "eirion", text: "Hello. I am Eirion. I have full context of your metabolic data, genetics, and current regimen. What would you like to know about your longevity blueprint?" }
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      endRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isOpen, isTyping]);

  const handleSend = async () => {
    if (!input.trim() || !analysisResult) return;
    
    const userMessage = input.trim();
    setMessages(prev => [...prev, { role: "user", text: userMessage }]);
    setInput("");
    setIsTyping(true);

    try {
      const res = await fetch("http://localhost:8000/chat/ask", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": "Bearer bypass-string"
        },
        body: JSON.stringify({
          message: userMessage,
          context_payload: analysisResult // Pass entire state to backend for prompt injection
        })
      });

      if (!res.ok) throw new Error("API Error");
      const data = await res.json();
      
      setMessages(prev => [...prev, { role: "eirion", text: data.reply }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: "eirion", text: "I'm having trouble connecting to my cognitive core right now. Please try again later." }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <>
      {/* Floating Action Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-blue-gray-900 text-white rounded-full flex items-center justify-center shadow-xl hover:shadow-2xl hover:scale-105 transition-all z-40"
      >
        <MessageSquare className="w-6 h-6" />
      </button>

      {/* Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-blue-gray-900/20 backdrop-blur-sm z-50 transition-opacity" 
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sliding Drawer */}
      <div 
        className={`fixed inset-y-0 right-0 w-full sm:w-[400px] bg-white shadow-2xl transform transition-transform duration-300 ease-in-out z-50 flex flex-col ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-blue-gray-100 bg-blue-gray-50/50">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-blue-gray-900 flex items-center justify-center">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-blue-gray-900">Ask Eirion</h3>
              <p className="text-xs text-blue-gray-500 font-medium">Personalized Clinical AI</p>
            </div>
          </div>
          <button onClick={() => setIsOpen(false)} className="p-2 text-blue-gray-500 hover:text-blue-gray-900 rounded-lg hover:bg-blue-gray-100 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Chat Log */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {messages.map((m, idx) => (
            <div key={idx} className={`flex gap-3 ${m.role === "user" ? "flex-row-reverse" : ""}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${m.role === "user" ? "bg-amber-100 text-amber-700" : "bg-blue-gray-100 text-blue-gray-700"}`}>
                {m.role === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>
              <div className={`text-sm px-4 py-3 rounded-2xl max-w-[80%] ${
                m.role === "user" 
                  ? "bg-blue-gray-900 text-white rounded-tr-sm" 
                  : "bg-blue-gray-50 text-blue-gray-800 border border-blue-gray-100 rounded-tl-sm prose prose-sm"
              }`}>
                {m.text}
              </div>
            </div>
          ))}
          {isTyping && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-blue-gray-100 flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4 text-blue-gray-700" />
              </div>
              <div className="bg-blue-gray-50 border border-blue-gray-100 px-4 py-3 rounded-2xl rounded-tl-sm flex gap-1 items-center">
                <div className="w-1.5 h-1.5 bg-blue-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
                <div className="w-1.5 h-1.5 bg-blue-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
                <div className="w-1.5 h-1.5 bg-blue-gray-400 rounded-full animate-bounce" />
              </div>
            </div>
          )}
          <div ref={endRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-blue-gray-100 bg-white">
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Ask anything about your data..."
              className="flex-1 bg-blue-gray-50 border border-blue-gray-200 rounded-full px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-gray-900 focus:border-transparent transition-all"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isTyping}
              className="w-10 h-10 rounded-full bg-blue-gray-900 text-white flex items-center justify-center hover:bg-blue-gray-800 disabled:opacity-50 transition-colors"
            >
              <Send className="w-4 h-4 ml-0.5" />
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
