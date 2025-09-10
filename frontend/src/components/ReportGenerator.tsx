import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { FileText, Download, Settings, Play, ChevronDown, ChevronRight, Folder, File, X } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import axios from "axios";

const API_BASE_URL = "http://52.64.205.176:5000/";

interface FileItem {
  id: string;
  name: string;
}

interface Product {
  id: string;
  name: string;
  files: FileItem[];
}

interface ProductLine {
  id: string;
  name: string;
  products: Product[];
}

interface Category {
  id: string;
  name: string;
  product_lines: ProductLine[];
}

export const ReportGenerator = () => {
  const [requirementFile, setRequirementFile] = useState<File | null>(null);
  const [reportTitle, setReportTitle] = useState("");
  const [generating, setGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [reportType, setReportType] = useState<"auto" | "manual">("manual");
  const [collectionName, setCollectionName] = useState("hello_my_friend");

  // Hierarchy data
  const [hierarchy, setHierarchy] = useState<Category[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  const [expandedProductLines, setExpandedProductLines] = useState<Set<string>>(new Set());
  const [expandedProducts, setExpandedProducts] = useState<Set<string>>(new Set());

  const { toast } = useToast();

  useEffect(() => {
    fetchHierarchy();
  }, []);

  const fetchHierarchy = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}hierarchy`);
      setHierarchy(response.data);
    } catch (error: any) {
      console.error('Error fetching hierarchy:', error);
      toast({
        title: "Lỗi",
        description: "Không thể tải cấu trúc tài liệu",
        variant: "destructive"
      });
    }
  };

  const handleRequirementUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      setRequirementFile(e.target.files[0]);
    }
  };

  const toggleFileSelection = (fileId: string) => {
    const newSelection = new Set(selectedFiles);
    if (newSelection.has(fileId)) {
      newSelection.delete(fileId);
    } else {
      newSelection.add(fileId);
    }
    setSelectedFiles(newSelection);
  };

  const toggleExpanded = (id: string, type: 'category' | 'productLine' | 'product') => {
    let setExpanded: React.Dispatch<React.SetStateAction<Set<string>>>;

    switch (type) {
      case 'category':
        setExpanded = setExpandedCategories;
        break;
      case 'productLine':
        setExpanded = setExpandedProductLines;
        break;
      case 'product':
        setExpanded = setExpandedProducts;
        break;
    }

    setExpanded(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const clearAllSelectedFiles = () => {
    setSelectedFiles(new Set());
    toast({
      title: "Đã bỏ chọn",
      description: "Đã bỏ chọn tất cả các file"
    });
  };

  const generateReport = async () => {
    // Validation
    if (!requirementFile || !reportTitle.trim()) {
      toast({
        title: "Lỗi",
        description: "Vui lòng cung cấp file yêu cầu kỹ thuật và tiêu đề báo cáo",
        variant: "destructive"
      });
      return;
    }

    if (reportType === "manual" && selectedFiles.size === 0) {
      toast({
        title: "Lỗi",
        description: "Vui lòng chọn ít nhất một file tài liệu sản phẩm",
        variant: "destructive"
      });
      return;
    }

    setGenerating(true);
    setProgress(0);

    try {
      // Tạo FormData
      const formData = new FormData();
      formData.append("pdf_file", requirementFile);
      formData.append("type", reportType);
      formData.append("collection_name", collectionName);

      if (reportType === "manual") {
        const fileIds = Array.from(selectedFiles).join(',');
        formData.append("filename_ids", fileIds);
      }

      // Progress simulation
      const steps = [
        "Đang tải file lên server...",
        "Đang phân tích file yêu cầu kỹ thuật...",
        "Đang xử lý tài liệu sản phẩm...",
        "Đang đối chiếu thông số kỹ thuật...",
        "Đang tạo file Excel..."
      ];

      // Simulate progress
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 80) return prev;
          return prev + 10;
        });
      }, 500);

      for (let i = 0; i < 3; i++) {
        await new Promise(resolve => setTimeout(resolve, 800));
        toast({
          title: "Đang xử lý",
          description: steps[i]
        });
      }

      // Gọi API
      const response = await axios.post(`${API_BASE_URL}generate-excel`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        responseType: 'blob', // Quan trọng: để nhận file
      });

      clearInterval(progressInterval);
      setProgress(100);

      // Tải xuống file
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${reportTitle}.xlsx`;
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
        description: error.response?.data?.error || error.message || "Có lỗi xảy ra khi tạo báo cáo",
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
              <Label htmlFor="report-title">Tiêu đề báo cáo *</Label>
              <Input
                id="report-title"
                value={reportTitle}
                onChange={(e) => setReportTitle(e.target.value)}
                placeholder="Ví dụ: Bảng Tuyên Bố Đáp Ứng UPS Netsure 731"
              />
            </div>

            <div>
              <Label htmlFor="requirement-file">File yêu cầu kỹ thuật (.pdf) *</Label>
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

            <div>
              <Label>Chế độ tạo báo cáo</Label>
              <Select value={reportType} onValueChange={(value: "auto" | "manual") => setReportType(value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="auto">Tự động (AI chọn file phù hợp)</SelectItem>
                  <SelectItem value="manual">Thủ công (Tự chọn file)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="collection-name">Collection Name</Label>
              <Input
                id="collection-name"
                value={collectionName}
                onChange={(e) => setCollectionName(e.target.value)}
                placeholder="hello_my_friend"
              />
            </div>
          </CardContent>
        </Card>

        {/* File Selection or Instructions Panel */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 justify-between">
              <div className="flex items-center gap-2">
                {reportType === "manual" ? (
                  <>
                    <Folder className="h-5 w-5" />
                    Chọn tài liệu sản phẩm
                    <Badge variant="outline">{selectedFiles.size} đã chọn</Badge>
                  </>
                ) : (
                  <>
                    <FileText className="h-5 w-5" />
                    Hướng dẫn sử dụng
                  </>
                )}
              </div>
              {reportType === "manual" && selectedFiles.size > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={clearAllSelectedFiles}
                  className="text-xs"
                >
                  <X className="h-3 w-3 mr-1" />
                  Bỏ chọn tất cả
                </Button>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="max-h-96 overflow-y-auto">
            {reportType === "manual" ? (
              <div className="space-y-2">
                {hierarchy.map((category) => (
                  <div key={category.id} className="border rounded-lg p-2">
                    <Collapsible>
                      <CollapsibleTrigger
                        className="flex items-center gap-2 w-full text-left p-2 hover:bg-muted rounded"
                        onClick={() => toggleExpanded(category.id, 'category')}
                      >
                        {expandedCategories.has(category.id) ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )}
                        <Folder className="h-4 w-4 text-blue-500" />
                        <span className="font-medium">{category.name}</span>
                      </CollapsibleTrigger>
                      <CollapsibleContent className="ml-6 mt-2 space-y-2">
                        {category.product_lines.map((productLine) => (
                          <div key={productLine.id}>
                            <Collapsible>
                              <CollapsibleTrigger
                                className="flex items-center gap-2 w-full text-left p-2 hover:bg-muted rounded"
                                onClick={() => toggleExpanded(productLine.id, 'productLine')}
                              >
                                {expandedProductLines.has(productLine.id) ? (
                                  <ChevronDown className="h-3 w-3" />
                                ) : (
                                  <ChevronRight className="h-3 w-3" />
                                )}
                                <Folder className="h-3 w-3 text-green-500" />
                                <span className="text-sm">{productLine.name}</span>
                              </CollapsibleTrigger>
                              <CollapsibleContent className="ml-5 mt-1 space-y-1">
                                {productLine.products.map((product) => (
                                  <div key={product.id}>
                                    <Collapsible>
                                      <CollapsibleTrigger
                                        className="flex items-center gap-2 w-full text-left p-1 hover:bg-muted rounded"
                                        onClick={() => toggleExpanded(product.id, 'product')}
                                      >
                                        {expandedProducts.has(product.id) ? (
                                          <ChevronDown className="h-3 w-3" />
                                        ) : (
                                          <ChevronRight className="h-3 w-3" />
                                        )}
                                        <Folder className="h-3 w-3 text-orange-500" />
                                        <span className="text-sm">{product.name}</span>
                                        <Badge variant="outline" className="text-xs">
                                          {product.files.length} files
                                        </Badge>
                                      </CollapsibleTrigger>
                                      <CollapsibleContent className="ml-5 mt-1 space-y-1">
                                        {product.files.map((file) => (
                                          <div key={file.id} className="flex items-center gap-2 p-1">
                                            <Checkbox
                                              id={file.id}
                                              checked={selectedFiles.has(file.id)}
                                              onCheckedChange={() => toggleFileSelection(file.id)}
                                            />
                                            <File className="h-3 w-3 text-gray-500" />
                                            <label
                                              htmlFor={file.id}
                                              className="text-xs cursor-pointer flex-1"
                                            >
                                              {file.name}
                                            </label>
                                          </div>
                                        ))}
                                      </CollapsibleContent>
                                    </Collapsible>
                                  </div>
                                ))}
                              </CollapsibleContent>
                            </Collapsible>
                          </div>
                        ))}
                      </CollapsibleContent>
                    </Collapsible>
                  </div>
                ))}
              </div>
            ) : (
              <div>
                <div className="space-y-3 text-sm">
                  <div className="flex gap-3">
                    <div className="bg-primary text-primary-foreground rounded-full w-6 h-6 flex items-center justify-center text-xs font-medium">1</div>
                    <p>Tải lên file yêu cầu kỹ thuật (PDF)</p>
                  </div>
                  <div className="flex gap-3">
                    <div className="bg-primary text-primary-foreground rounded-full w-6 h-6 flex items-center justify-center text-xs font-medium">2</div>
                    <p>Chọn chế độ "Tự động" - AI sẽ tự động tìm và chọn tài liệu phù hợp</p>
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
                    <li>• File Excel hoàn chỉnh để tải xuống</li>
                  </ul>
                </div>
              </div>
            )}
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
              disabled={
                generating ||
                !requirementFile ||
                !reportTitle.trim() ||
                (reportType === "manual" && selectedFiles.size === 0)
              }
              className="flex-1"
            >
              <Play className="h-4 w-4 mr-2" />
              {generating ? "Đang tạo báo cáo..." : "Tạo báo cáo Excel"}
            </Button>

            {!generating && (
              <Button variant="outline" disabled>
                <Download className="h-4 w-4 mr-2" />
                Tải mẫu PDF
              </Button>
            )}
          </div>

          <div className="mt-4 text-xs text-muted-foreground">
            <p><strong>Chế độ tự động:</strong> AI sẽ phân tích file yêu cầu và tự động chọn tài liệu phù hợp từ database.</p>
            <p><strong>Chế độ thủ công:</strong> Bạn chọn cụ thể các file tài liệu để so sánh với yêu cầu kỹ thuật.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};