import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Send, MessageSquare, Bot, User, FileText } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { supabase } from "@/integrations/supabase/client";

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  referencedDocuments?: string[];
}

interface QueryHistory {
  id: string;
  question: string;
  answer: string;
  referenced_documents: string[];
  created_at: string;
}

export const KnowledgeChat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [queryHistory, setQueryHistory] = useState<QueryHistory[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  useEffect(() => {
    fetchQueryHistory();
    // Add welcome message
    setMessages([{
      id: '1',
      type: 'assistant',
      content: 'Xin chào! Tôi là trợ lý AI của bạn. Hãy hỏi tôi bất cứ điều gì về các tài liệu đã tải lên.',
      timestamp: new Date()
    }]);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const fetchQueryHistory = async () => {
    try {
      const { data, error } = await supabase
        .from('knowledge_queries')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(10);

      if (error) throw error;
      setQueryHistory(data || []);
    } catch (error: any) {
      console.error('Error fetching query history:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue("");
    setLoading(true);

    try {
      // Simulate AI response (replace with actual AI service call)
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `Tôi đã tìm kiếm trong các tài liệu và đây là câu trả lời cho câu hỏi: "${inputValue}".\n\nDựa trên các tài liệu đã tải lên, tôi có thể cung cấp thông tin liên quan. Tuy nhiên, để có câu trả lời chính xác hơn, bạn cần tích hợp với dịch vụ AI như OpenAI hoặc các dịch vụ xử lý tài liệu khác.`,
        timestamp: new Date(),
        referencedDocuments: ['doc1', 'doc2']
      };

      setMessages(prev => [...prev, aiResponse]);

      // Save to database
      const { data: { user } } = await supabase.auth.getUser();
      if (user) {
        await supabase
          .from('knowledge_queries')
          .insert({
            user_id: user.id,
            question: userMessage.content,
            answer: aiResponse.content,
            referenced_documents: aiResponse.referencedDocuments || []
          });
        
        fetchQueryHistory();
      }

    } catch (error: any) {
      console.error('Error sending message:', error);
      toast({
        title: "Lỗi",
        description: "Không thể gửi tin nhắn. Vui lòng thử lại.",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const loadHistoryQuery = (query: QueryHistory) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: query.question,
      timestamp: new Date(query.created_at)
    };

    const aiMessage: Message = {
      id: (Date.now() + 1).toString(),
      type: 'assistant',
      content: query.answer,
      timestamp: new Date(query.created_at),
      referencedDocuments: query.referenced_documents
    };

    setMessages([userMessage, aiMessage]);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[600px]">
      {/* Chat History Sidebar */}
      <div className="lg:col-span-1">
        <Card className="h-full">
          <CardContent className="p-4">
            <h3 className="font-medium mb-4 flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              Lịch sử hỏi đáp
            </h3>
            <ScrollArea className="h-[500px]">
              <div className="space-y-2">
                {queryHistory.map((query) => (
                  <Card 
                    key={query.id} 
                    className="p-3 cursor-pointer hover:bg-accent transition-colors"
                    onClick={() => loadHistoryQuery(query)}
                  >
                    <p className="text-sm font-medium line-clamp-2 mb-1">
                      {query.question}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(query.created_at).toLocaleDateString('vi-VN')}
                    </p>
                    {query.referenced_documents.length > 0 && (
                      <Badge variant="outline" className="text-xs mt-1">
                        {query.referenced_documents.length} tài liệu
                      </Badge>
                    )}
                  </Card>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      {/* Main Chat Area */}
      <div className="lg:col-span-3">
        <Card className="h-full flex flex-col">
          <CardContent className="flex-1 p-0 flex flex-col">
            {/* Messages */}
            <ScrollArea className="flex-1 p-4">
              <div className="space-y-4">
                {messages.map((message) => (
                  <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[80%] rounded-lg p-3 ${
                      message.type === 'user' 
                        ? 'bg-primary text-primary-foreground' 
                        : 'bg-muted'
                    }`}>
                      <div className="flex items-center gap-2 mb-2">
                        {message.type === 'user' ? (
                          <User className="h-4 w-4" />
                        ) : (
                          <Bot className="h-4 w-4" />
                        )}
                        <span className="text-xs opacity-70">
                          {message.timestamp.toLocaleTimeString('vi-VN')}
                        </span>
                      </div>
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                      {message.referencedDocuments && message.referencedDocuments.length > 0 && (
                        <div className="mt-2 flex items-center gap-1">
                          <FileText className="h-3 w-3" />
                          <span className="text-xs opacity-70">
                            Tham khảo {message.referencedDocuments.length} tài liệu
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {loading && (
                  <div className="flex justify-start">
                    <div className="max-w-[80%] rounded-lg p-3 bg-muted">
                      <div className="flex items-center gap-2">
                        <Bot className="h-4 w-4" />
                        <span className="text-sm">Đang suy nghĩ...</span>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            {/* Input Form */}
            <div className="border-t p-4">
              <form onSubmit={handleSubmit} className="flex gap-2">
                <Input
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Đặt câu hỏi về tài liệu..."
                  disabled={loading}
                  className="flex-1"
                />
                <Button type="submit" disabled={loading || !inputValue.trim()}>
                  <Send className="h-4 w-4" />
                </Button>
              </form>
              <p className="text-xs text-muted-foreground mt-2">
                Hỏi về nội dung trong các tài liệu đã tải lên
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};