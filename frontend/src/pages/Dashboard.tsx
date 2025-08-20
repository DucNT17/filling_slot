import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { DocumentUpload } from "@/components/DocumentUpload";
import { DocumentList } from "@/components/DocumentList";
import { KnowledgeChat } from "@/components/KnowledgeChat";
import { ReportGenerator } from "@/components/ReportGenerator";
import { ManagementDashboard } from "@/components/ManagementDashboard";
import { FileText, MessageSquare, Upload, FileCheck, Settings } from "lucide-react";

const Dashboard = () => {
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleDocumentUploaded = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  const handleDataChanged = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">
            Trung Tâm Tri Thức Thông Minh
          </h1>
          <p className="text-muted-foreground">
            Quản lý tài liệu và hỏi đáp với AI về kiến thức công ty
          </p>
        </div>

        <Tabs defaultValue="documents" className="space-y-6">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="documents" className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Quản Lý Tài Liệu
            </TabsTrigger>
            <TabsTrigger value="upload" className="flex items-center gap-2">
              <Upload className="h-4 w-4" />
              Tải Lên
            </TabsTrigger>
            <TabsTrigger value="chat" className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              Hỏi Đáp AI
            </TabsTrigger>
            <TabsTrigger value="reports" className="flex items-center gap-2">
              <FileCheck className="h-4 w-4" />
              Tạo Báo Cáo
            </TabsTrigger>
            <TabsTrigger value="management" className="flex items-center gap-2">
              <Settings className="h-4 w-4" />
              Quản Lý Hệ Thống
            </TabsTrigger>
          </TabsList>

          <TabsContent value="documents">
            <Card>
              <CardHeader>
                <CardTitle>Danh Sách Tài Liệu</CardTitle>
                <CardDescription>
                  Quản lý và tìm kiếm tài liệu đã tải lên
                </CardDescription>
              </CardHeader>
              <CardContent>
                <DocumentList key={refreshTrigger} />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="upload">
            <Card>
              <CardHeader>
                <CardTitle>Tải Lên Tài Liệu</CardTitle>
                <CardDescription>
                  Tải lên các tài liệu kiến thức của công ty
                </CardDescription>
              </CardHeader>
              <CardContent>
                <DocumentUpload onDocumentUploaded={handleDocumentUploaded} />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="chat">
            <Card>
              <CardHeader>
                <CardTitle>Hỏi Đáp Với AI</CardTitle>
                <CardDescription>
                  Đặt câu hỏi và nhận câu trả lời từ tài liệu đã tải lên
                </CardDescription>
              </CardHeader>
              <CardContent>
                <KnowledgeChat />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="reports">
            <Card>
              <CardHeader>
                <CardTitle>Tạo Báo Cáo Tự Động</CardTitle>
                <CardDescription>
                  Tự động tạo Bảng Tuyên Bố Đáp Ứng Kỹ Thuật
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ReportGenerator />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="management">
            <ManagementDashboard />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Dashboard;