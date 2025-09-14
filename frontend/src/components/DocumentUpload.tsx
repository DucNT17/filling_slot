import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent } from "@/components/ui/card";
import { Upload, FileText, X } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import axios from "axios";

const API_BASE_URL = "http://52.64.205.176:8080/";

interface DocumentUploadProps {
  onDocumentUploaded: () => void;
}

interface Category {
  id: string;
  name: string;
}

interface ProductLine {
  id: string;
  name: string;
  category_id: string;
}

interface Product {
  id: string;
  name: string;
  product_line_id: string;
}

export const DocumentUpload = ({ onDocumentUploaded }: DocumentUploadProps) => {
  const [files, setFiles] = useState<File[]>([]);
  const [productName, setProductName] = useState("");
  const [description, setDescription] = useState("");
  const [featuresBenefits, setFeaturesBenefits] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [productLineId, setProductLineId] = useState("");
  const [collectionName, setCollectionName] = useState("hello_my_friend");
  const [uploading, setUploading] = useState(false);

  const [categories, setCategories] = useState<Category[]>([]);
  const [productLines, setProductLines] = useState<ProductLine[]>([]);
  const [filteredProductLines, setFilteredProductLines] = useState<ProductLine[]>([]);

  const { toast } = useToast();

  useEffect(() => {
    fetchCategories();
    fetchProductLines();
  }, []);

  useEffect(() => {
    if (categoryId) {
      const filtered = productLines.filter(pl => pl.category_id === categoryId);
      setFilteredProductLines(filtered);
      setProductLineId(""); // Reset product line selection when category changes
    } else {
      setFilteredProductLines([]);
    }
  }, [categoryId, productLines]);

  const fetchCategories = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}categories`);
      setCategories(response.data);
    } catch (error: any) {
      console.error('Error fetching categories:', error);
      toast({
        title: "Lỗi",
        description: "Không thể tải danh sách danh mục",
        variant: "destructive"
      });
    }
  };

  const fetchProductLines = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}product-lines`);
      setProductLines(response.data);
    } catch (error: any) {
      console.error('Error fetching product lines:', error);
      toast({
        title: "Lỗi",
        description: "Không thể tải danh sách dòng sản phẩm",
        variant: "destructive"
      });
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  };

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const uploadDocument = async () => {
    if (!files.length || !productName.trim() || !categoryId || !productLineId) {
      toast({
        title: "Lỗi",
        description: "Vui lòng điền đầy đủ thông tin và chọn file",
        variant: "destructive"
      });
      return;
    }

    setUploading(true);

    try {
      // Tìm tên category và product line từ ID
      const selectedCategory = categories.find(c => c.id === categoryId);
      const selectedProductLine = productLines.find(pl => pl.id === productLineId);

      if (!selectedCategory || !selectedProductLine) {
        throw new Error("Không tìm thấy thông tin danh mục hoặc dòng sản phẩm");
      }

      // Tạo FormData để upload
      const formData = new FormData();
      formData.append("category", selectedCategory.name);
      formData.append("product_line", selectedProductLine.name);
      formData.append("product_name", productName);
      formData.append("description", description);
      formData.append("features_benefits", featuresBenefits);
      formData.append("collection_name", collectionName);

      // Thêm tất cả files
      files.forEach(file => {
        formData.append("files", file);
      });

      const response = await axios.post(`${API_BASE_URL}upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      toast({
        title: "Thành công",
        description: `Đã tải lên ${files.length} tài liệu thành công`
      });

      // Reset form
      setFiles([]);
      setProductName("");
      setDescription("");
      setFeaturesBenefits("");
      setCategoryId("");
      setProductLineId("");
      setCollectionName("hello_my_friend");
      onDocumentUploaded();

    } catch (error: any) {
      console.error('Upload error:', error);
      toast({
        title: "Lỗi",
        description: error.response?.data?.error || error.message || "Có lỗi xảy ra khi tải lên tài liệu",
        variant: "destructive"
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <div>
            <Label htmlFor="productName">Tên sản phẩm *</Label>
            <Input
              id="productName"
              value={productName}
              onChange={(e) => setProductName(e.target.value)}
              placeholder="Nhập tên sản phẩm"
            />
          </div>

          <div>
            <Label htmlFor="category">Danh mục *</Label>
            <Select value={categoryId} onValueChange={setCategoryId}>
              <SelectTrigger>
                <SelectValue placeholder="Chọn danh mục" />
              </SelectTrigger>
              <SelectContent>
                {categories.map((category) => (
                  <SelectItem key={category.id} value={category.id}>
                    {category.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="productLine">Dòng sản phẩm *</Label>
            <Select
              value={productLineId}
              onValueChange={setProductLineId}
              disabled={!categoryId}
            >
              <SelectTrigger>
                <SelectValue placeholder="Chọn dòng sản phẩm" />
              </SelectTrigger>
              <SelectContent>
                {filteredProductLines.map((productLine) => (
                  <SelectItem key={productLine.id} value={productLine.id}>
                    {productLine.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="description">Mô tả *</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Mô tả về sản phẩm"
              rows={3}
            />
          </div>

          <div>
            <Label htmlFor="featuresBenefits">Tính năng & Lợi ích *</Label>
            <Textarea
              id="featuresBenefits"
              value={featuresBenefits}
              onChange={(e) => setFeaturesBenefits(e.target.value)}
              placeholder="Các tính năng và lợi ích của sản phẩm"
              rows={3}
            />
          </div>

          <div>
            <Label htmlFor="collectionName">Collection Name</Label>
            <Input
              id="collectionName"
              value={collectionName}
              onChange={(e) => setCollectionName(e.target.value)}
              placeholder="hello_my_friend"
            />
          </div>
        </div>

        <div>
          <Label htmlFor="files">Chọn file *</Label>
          <div className="mt-2">
            <Input
              id="files"
              type="file"
              multiple
              onChange={handleFileSelect}
              accept=".pdf,.doc,.docx,.txt,.md"
              className="mb-4"
            />

            {files.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium">File đã chọn:</h4>
                {files.map((file, index) => (
                  <Card key={index}>
                    <CardContent className="p-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <FileText className="h-4 w-4 text-primary" />
                          <div>
                            <p className="text-sm font-medium">{file.name}</p>
                            <p className="text-xs text-muted-foreground">
                              {(file.size / 1024 / 1024).toFixed(2)} MB
                            </p>
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeFile(index)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <Button
        onClick={uploadDocument}
        disabled={uploading || !files.length || !productName.trim() || !categoryId || !productLineId || !description.trim() || !featuresBenefits.trim()}
        className="w-full"
      >
        <Upload className="h-4 w-4 mr-2" />
        {uploading ? "Đang tải lên..." : `Tải lên ${files.length} tài liệu`}
      </Button>
    </div>
  );
};