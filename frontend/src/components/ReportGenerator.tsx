import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { FileText, Download, Settings, Play } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

export const ReportGenerator = () => {
  const [requirementFile, setRequirementFile] = useState<File | null>(null);
  const [productDocs, setProductDocs] = useState<File[]>([]);
  const [reportTitle, setReportTitle] = useState("");
  const [generating, setGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const { toast } = useToast();

  const handleRequirementUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      setRequirementFile(e.target.files[0]);
    }
  };

  const handleProductDocsUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setProductDocs(Array.from(e.target.files));
    }
  };

  const generateReport = async () => {
    if (!requirementFile || !productDocs.length || !reportTitle.trim()) {
      toast({
        title: "Lỗi",
        description: "Vui lòng cung cấp đầy đủ thông tin",
        variant: "destructive"
      });
      return;
    }

    setGenerating(true);
    setProgress(0);

    try {
      // Simulate report generation process
      const steps = [
        "Đang phân tích file yêu cầu kỹ thuật...",
        "Đang xử lý tài liệu sản phẩm...",
        "Đang đối chiếu thông số kỹ thuật...",
        "Đang tạo bảng tuyên bố đáp ứng...",
        "Đang tạo file Word..."
      ];

      for (let i = 0; i < steps.length; i++) {
        await new Promise(resolve => setTimeout(resolve, 1500));
        setProgress((i + 1) * 20);
        
        toast({
          title: "Đang xử lý",
          description: steps[i]
        });
      }

      // Simulate file download
      const blob = new Blob(['Đây là nội dung báo cáo mẫu'], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${reportTitle}.docx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast({
        title: "Thành công",
        description: "Đã tạo và tải xuống báo cáo thành công"
      });

    } catch (error: any) {
      console.error('Report generation error:', error);
      toast({
        title: "Lỗi",
        description: "Có lỗi xảy ra khi tạo báo cáo",
        variant: "destructive"
      });
    } finally {
      setGenerating(false);
      setProgress(0);
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Configuration Panel */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Cấu hình báo cáo
            </CardTitle>
            <CardDescription>
              Thiết lập thông tin để tạo Bảng Tuyên Bố Đáp Ứng Kỹ Thuật
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="report-title">Tiêu đề báo cáo</Label>
              <Input
                id="report-title"
                value={reportTitle}
                onChange={(e) => setReportTitle(e.target.value)}
                placeholder="Ví dụ: Bảng Tuyên Bố Đáp Ứng UPS Netsure 731"
              />
            </div>

            <div>
              <Label htmlFor="requirement-file">File yêu cầu kỹ thuật (.pdf)</Label>
              <Input
                id="requirement-file"
                type="file"
                accept=".pdf"
                onChange={handleRequirementUpload}
                className="mt-1"
              />
              {requirementFile && (
                <p className="text-sm text-muted-foreground mt-1">
                  Đã chọn: {requirementFile.name}
                </p>
              )}
            </div>
           
            {/* <div>
              <Label htmlFor="product-docs">Tài liệu sản phẩm (.pdf, .doc, .docx)</Label>
              <Input
                id="product-docs"
                type="file"
                multiple
                accept=".pdf,.doc,.docx"
                onChange={handleProductDocsUpload}
                className="mt-1"
              />
              {productDocs.length > 0 && (
                <p className="text-sm text-muted-foreground mt-1">
                  Đã chọn {productDocs.length} file tài liệu
                </p>
              )}
            </div> */}
          </CardContent>
        </Card>

        {/* Instructions Panel */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Hướng dẫn sử dụng
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 text-sm">
              <div className="flex gap-3">
                <div className="bg-primary text-primary-foreground rounded-full w-6 h-6 flex items-center justify-center text-xs font-medium">1</div>
                <p>Tải lên file yêu cầu kỹ thuật (ví dụ: Chuong V Yeu cau ky thuat.pdf)</p>
              </div>
              <div className="flex gap-3">
                <div className="bg-primary text-primary-foreground rounded-full w-6 h-6 flex items-center justify-center text-xs font-medium">2</div>
                <p>Chọn các tài liệu kỹ thuật sản phẩm liên quan (ví dụ: Netsure-731-A41-user-manual.pdf)</p>
              </div>
              <div className="flex gap-3">
                <div className="bg-primary text-primary-foreground rounded-full w-6 h-6 flex items-center justify-center text-xs font-medium">3</div>
                <p>Nhập tiêu đề cho báo cáo</p>
              </div>
              <div className="flex gap-3">
                <div className="bg-primary text-primary-foreground rounded-full w-6 h-6 flex items-center justify-center text-xs font-medium">4</div>
                <p>Bấm "Tạo báo cáo" và đợi hệ thống xử lý</p>
              </div>
            </div>

            <div className="mt-6 p-4 bg-muted rounded-lg">
              <h4 className="font-medium mb-2">Kết quả:</h4>
              <ul className="text-sm space-y-1 text-muted-foreground">
                <li>• Bảng so sánh thông số kỹ thuật</li>
                <li>• Đánh giá mức độ đáp ứng</li>
                <li>• Trích dẫn nguồn tài liệu</li>
                <li>• File Word hoàn chỉnh để tải xuống</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Generation Panel */}
      <Card>
        <CardHeader>
          <CardTitle>Tạo báo cáo</CardTitle>
        </CardHeader>
        <CardContent>
          {generating && (
            <div className="space-y-4 mb-6">
              <div className="flex items-center gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-primary border-t-transparent"></div>
                <span className="text-sm">Đang xử lý...</span>
              </div>
              <Progress value={progress} className="w-full" />
              <p className="text-xs text-muted-foreground">
                Quá trình này có thể mất vài phút tùy thuộc vào kích thước tài liệu
              </p>
            </div>
          )}

          <div className="flex gap-4">
            <Button 
              onClick={generateReport}
              disabled={generating || !requirementFile || !productDocs.length || !reportTitle.trim()}
              className="flex-1"
            >
              <Play className="h-4 w-4 mr-2" />
              {generating ? "Đang tạo báo cáo..." : "Tạo báo cáo"}
            </Button>
            
            {!generating && (
              <Button variant="outline" disabled>
                <Download className="h-4 w-4 mr-2" />
                Tải xuống mẫu
              </Button>
            )}
          </div>

          {/* <p className="text-xs text-muted-foreground mt-4">
            <strong>Lưu ý:</strong> Tính năng này yêu cầu tích hợp với AI service để phân tích và so sánh tài liệu. 
            Hiện tại chỉ là demo UI, cần implement backend với OpenAI hoặc dịch vụ AI khác.
          </p> */}
        </CardContent>
      </Card>
    </div>
  );
};