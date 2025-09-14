import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Send, MessageSquare, Bot, User, FileText, ChevronDown } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  referencedDocuments?: SourceDocument[];
}

interface SourceDocument {
  file_name: string;
  product_name: string;
  category: string;
  score: number;
}

interface ChatResponse {
  answer: string;
  source_documents: SourceDocument[];
  question: string;
  success: boolean;
  error?: string;
}

export const KnowledgeChat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [collectionName, setCollectionName] = useState("hello_my_friend");
  const [showScrollButton, setShowScrollButton] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  // Backend API base URL
  const API_BASE_URL = "http://52.64.205.176:8080/";

  useEffect(() => {
    checkAgentHealth();
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

  const handleScroll = (event: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, scrollHeight, clientHeight } = event.currentTarget;
    const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;
    setShowScrollButton(!isNearBottom && messages.length > 3);
  };

  const checkAgentHealth = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/chat/health?collection_name=${collectionName}`);
      const data = await response.json();

      if (data.status !== 'healthy') {
        toast({
          title: "Cảnh báo",
          description: "AI Agent có thể không hoạt động ổn định",
          variant: "destructive"
        });
      }
    } catch (error) {
      console.error('Error checking agent health:', error);
      toast({
        title: "Lỗi kết nối",
        description: "Không thể kết nối với AI Agent",
        variant: "destructive"
      });
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
    const currentQuestion = inputValue;
    setInputValue("");
    setLoading(true);

    try {
      // Call chat API
      const formData = new FormData();
      formData.append('question', currentQuestion);
      formData.append('collection_name', collectionName);

      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        body: formData,
      });

      let chatResponse: ChatResponse;

      try {
        chatResponse = await response.json();
      } catch (parseError) {
        throw new Error(`HTTP error! status: ${response.status} - Cannot parse response`);
      }

      // Xử lý cả HTTP error và success response
      if (!response.ok) {
        // Nếu server trả về lỗi nhưng có JSON response với answer
        if (chatResponse && chatResponse.answer) {
          const aiResponse: Message = {
            id: (Date.now() + 1).toString(),
            type: 'assistant',
            content: chatResponse.answer,
            timestamp: new Date(),
            referencedDocuments: chatResponse.source_documents || []
          };
          setMessages(prev => [...prev, aiResponse]);
          return; // Không throw error nữa
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      if (!chatResponse.success) {
        // Nếu server trả về lỗi nhưng có answer, hiển thị answer
        if (chatResponse.answer) {
          const aiResponse: Message = {
            id: (Date.now() + 1).toString(),
            type: 'assistant',
            content: chatResponse.answer,
            timestamp: new Date(),
            referencedDocuments: chatResponse.source_documents || []
          };
          setMessages(prev => [...prev, aiResponse]);
          return; // Không throw error nữa
        }
        throw new Error(chatResponse.error || 'Unknown error occurred');
      }

      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: chatResponse.answer,
        timestamp: new Date(),
        referencedDocuments: chatResponse.source_documents
      };

      setMessages(prev => [...prev, aiResponse]);

    } catch (error: any) {
      console.error('Error sending message:', error);

      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `Xin lỗi, tôi gặp lỗi khi xử lý câu hỏi của bạn: ${error.message}`,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, errorMessage]);

      toast({
        title: "Lỗi",
        description: "Không thể gửi tin nhắn. Vui lòng thử lại.",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([{
      id: '1',
      type: 'assistant',
      content: 'Xin chào! Tôi là trợ lý AI của bạn. Hãy hỏi tôi bất cứ điều gì về các tài liệu đã tải lên.',
      timestamp: new Date()
    }]);
  };

  return (
    <div className="w-full">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[600px] max-h-[600px] overflow-hidden">
        {/* Chat Controls Sidebar */}
        <div className="lg:col-span-1 h-full overflow-hidden">
          <Card className="h-full">
            <CardContent className="p-4 h-full overflow-y-auto">
              <h3 className="font-medium mb-4 flex items-center gap-2">
                <MessageSquare className="h-4 w-4" />
                Điều khiển Chat
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Collection Name:</label>
                  <Input
                    value={collectionName}
                    onChange={(e) => setCollectionName(e.target.value)}
                    placeholder="hello_my_friend"
                    className="mt-1"
                  />
                </div>
                <Button
                  onClick={clearChat}
                  variant="outline"
                  className="w-full"
                >
                  Xóa cuộc trò chuyện
                </Button>
                <Button
                  onClick={checkAgentHealth}
                  variant="outline"
                  className="w-full"
                >
                  Kiểm tra trạng thái Agent
                </Button>
              </div>
              <div className="mt-6">
                <h4 className="font-medium text-sm mb-2">Hướng dẫn sử dụng:</h4>
                <ul className="text-xs text-muted-foreground space-y-1">
                  <li>• Đặt câu hỏi về tài liệu đã tải lên</li>
                  <li>• Agent sẽ tìm kiếm trong vector database</li>
                  <li>• Xem tài liệu tham khảo trong phản hồi</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Chat Area */}
        <div className="lg:col-span-3 h-full overflow-hidden">
          <Card className="h-full flex flex-col">
            <CardContent className="flex-1 p-0 flex flex-col overflow-hidden relative min-h-0">
              {/* Messages */}
              <ScrollArea className="flex-1 min-h-0" onScrollCapture={handleScroll}>
                <div className="space-y-4 p-4">
                  {messages.map((message) => (
                    <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-[80%] rounded-lg p-3 break-words ${message.type === 'user'
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
                        <p className="text-sm whitespace-pre-wrap break-words overflow-wrap-anywhere">{message.content}</p>
                        {message.referencedDocuments && message.referencedDocuments.length > 0 && (
                          <div className="mt-3">
                            <div className="flex items-center gap-1 mb-2">
                              <FileText className="h-3 w-3" />
                              <span className="text-xs opacity-70">
                                Tham khảo {message.referencedDocuments.length} tài liệu:
                              </span>
                            </div>
                            <div className="space-y-1">
                              {message.referencedDocuments.map((doc, index) => (
                                <div key={index} className="text-xs bg-background/50 rounded p-2">
                                  <div className="font-medium">{doc.file_name}</div>
                                  <div className="text-muted-foreground">
                                    {doc.product_name} - {doc.category}
                                  </div>
                                  <div className="text-muted-foreground">
                                    Độ liên quan: {(doc.score * 100).toFixed(1)}%
                                  </div>
                                </div>
                              ))}
                            </div>
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

              {/* Scroll to bottom button */}
              {showScrollButton && (
                <Button
                  variant="secondary"
                  size="sm"
                  className="absolute bottom-20 right-4 rounded-full w-10 h-10 p-0 shadow-lg z-10"
                  onClick={scrollToBottom}
                  title="Cuộn xuống tin nhắn mới nhất"
                >
                  <ChevronDown className="h-4 w-4" />
                </Button>
              )}

              {/* Input Form */}
              <div className="border-t p-4 flex-shrink-0 bg-background">
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
    </div>
  );
};