import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Brain, FileText, MessageSquare, FileCheck, ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";

const Index = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted/50">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <div className="flex items-center justify-center mb-6">
            <Brain className="h-16 w-16 text-primary mr-4" />
            <h1 className="text-5xl font-bold">Hệ thống quản lý tài liệu</h1>
          </div>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Hệ thống quản lý tài liệu nội bộ thông minh - Nơi tập trung và khai thác tri thức dữ liệu một cách hiệu quả
          </p>
          <div className="mt-8">
            <Link to="/dashboard">
              <Button size="lg" className="text-lg px-8 py-6">
                Bắt đầu sử dụng
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16">
          <Card className="text-center hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="mx-auto bg-primary/10 w-16 h-16 rounded-full flex items-center justify-center mb-4">
                <FileText className="h-8 w-8 text-primary" />
              </div>
              <CardTitle>Quản Lý Tài Liệu</CardTitle>
              <CardDescription>
                Tải lên và tổ chức các tài liệu kiến thức của công ty
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Datasheets sản phẩm</li>
                <li>• User manuals</li>
                <li>• Báo cáo kỹ thuật</li>
                <li>• Quy trình vận hành</li>
              </ul>
            </CardContent>
          </Card>

          <Card className="text-center hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="mx-auto bg-primary/10 w-16 h-16 rounded-full flex items-center justify-center mb-4">
                <MessageSquare className="h-8 w-8 text-primary" />
              </div>
              <CardTitle>Hỏi Đáp AI</CardTitle>
              <CardDescription>
                Đặt câu hỏi và nhận câu trả lời từ chính tài liệu của bạn
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Tìm kiếm thông tin nhanh chóng</li>
                <li>• Câu trả lời chính xác</li>
                <li>• Trích dẫn nguồn tài liệu</li>
                <li>• Lưu lịch sử hỏi đáp</li>
              </ul>
            </CardContent>
          </Card>

          <Card className="text-center hover:shadow-lg transition-shadow md:col-span-2 lg:col-span-1">
            <CardHeader>
              <div className="mx-auto bg-primary/10 w-16 h-16 rounded-full flex items-center justify-center mb-4">
                <FileCheck className="h-8 w-8 text-primary" />
              </div>
              <CardTitle>Tạo Báo Cáo Tự Động</CardTitle>
              <CardDescription>
                Tự động tạo Bảng Tuyên Bố Đáp Ứng Kỹ Thuật
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Đối chiếu yêu cầu kỹ thuật</li>
                <li>• So sánh thông số sản phẩm</li>
                <li>• Đánh giá mức độ đáp ứng</li>
                <li>• Xuất file Excel hoàn chỉnh</li>
              </ul>
            </CardContent>
          </Card>
        </div>

        <div className="text-center">
          <Card className="max-w-4xl mx-auto">
            <CardHeader>
              <CardTitle className="text-2xl">Quy trình hoạt động</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="text-center">
                  <div className="bg-primary text-primary-foreground rounded-full w-10 h-10 flex items-center justify-center mx-auto mb-3 text-lg font-bold">1</div>
                  <h4 className="font-medium mb-2">Tải lên tài liệu</h4>
                  <p className="text-sm text-muted-foreground">Upload các file PDF, Word, PowerPoint</p>
                </div>
                <div className="text-center">
                  <div className="bg-primary text-primary-foreground rounded-full w-10 h-10 flex items-center justify-center mx-auto mb-3 text-lg font-bold">2</div>
                  <h4 className="font-medium mb-2">AI xử lý nội dung</h4>
                  <p className="text-sm text-muted-foreground">Hệ thống phân tích và index nội dung</p>
                </div>
                <div className="text-center">
                  <div className="bg-primary text-primary-foreground rounded-full w-10 h-10 flex items-center justify-center mx-auto mb-3 text-lg font-bold">3</div>
                  <h4 className="font-medium mb-2">Hỏi đáp thông minh</h4>
                  <p className="text-sm text-muted-foreground">Đặt câu hỏi bằng ngôn ngữ tự nhiên</p>
                </div>
                <div className="text-center">
                  <div className="bg-primary text-primary-foreground rounded-full w-10 h-10 flex items-center justify-center mx-auto mb-3 text-lg font-bold">4</div>
                  <h4 className="font-medium mb-2">Tạo báo cáo</h4>
                  <p className="text-sm text-muted-foreground">Tự động sinh báo cáo từ dữ liệu</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Index;
