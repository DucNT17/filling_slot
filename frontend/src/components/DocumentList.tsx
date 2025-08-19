import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { FileText, Download, Trash2, Search, Calendar, User, Tag } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import axios from "axios";

const API_BASE_URL = "http://localhost:5000/";

interface Document {
  id: string;
  name: string;
  product_id: string;
  product?: {
    id: string;
    name: string;
    product_line: {
      id: string;
      name: string;
      category: {
        id: string;
        name: string;
      }
    }
  };
}

interface Category {
  id: string;
  name: string;
}

export const DocumentList = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const { toast } = useToast();

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    try {
      await Promise.all([
        fetchDocuments(),
        fetchCategories()
      ]);
    } catch (error) {
      console.error('Error fetching initial data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchDocuments = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}files`);
      console.log("Files response:", response.data);
      setDocuments(response.data || []);
    } catch (error: any) {
      console.error('Error fetching documents:', error);
      toast({
        title: "Lỗi",
        description: `Không thể tải danh sách tài liệu: ${error.message}`,
        variant: "destructive"
      });
    }
  };

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

  const deleteDocument = async (document: Document) => {
    if (!confirm(`Bạn có chắc muốn xóa tài liệu "${document.name}"?`)) return;

    try {
      await axios.delete(`${API_BASE_URL}files/${document.id}`);

      toast({
        title: "Thành công",
        description: "Đã xóa tài liệu thành công"
      });

      fetchDocuments();
    } catch (error: any) {
      console.error('Delete error:', error);
      toast({
        title: "Lỗi",
        description: "Không thể xóa tài liệu",
        variant: "destructive"
      });
    }
  };

  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = doc.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.product?.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.product?.product_line?.name?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesCategory = categoryFilter === "all" ||
      doc.product?.product_line?.category?.id === categoryFilter;

    return matchesSearch && matchesCategory;
  });

  if (loading) {
    return <div className="text-center py-8">Đang tải...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row gap-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Tìm kiếm tài liệu..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
        <Select value={categoryFilter} onValueChange={setCategoryFilter}>
          <SelectTrigger className="w-full md:w-48">
            <SelectValue placeholder="Lọc theo danh mục" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tất cả danh mục</SelectItem>
            {categories.map((category) => (
              <SelectItem key={category.id} value={category.id}>
                {category.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="text-sm text-muted-foreground">
        Hiển thị {filteredDocuments.length} / {documents.length} tài liệu
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredDocuments.map((document) => (
          <Card key={document.id} className="hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="h-5 w-5 text-primary" />
                  {document.product?.product_line?.category && (
                    <Badge variant="secondary">
                      {document.product.product_line.category.name}
                    </Badge>
                  )}
                </div>
              </div>
              <CardTitle className="text-base leading-tight">
                {document.name}
              </CardTitle>
            </CardHeader>

            <CardContent className="space-y-3">
              {document.product && (
                <div className="space-y-2 text-xs text-muted-foreground">
                  <div className="flex items-center gap-2">
                    <Tag className="h-3 w-3" />
                    <span>Sản phẩm: {document.product.name}</span>
                  </div>
                  {document.product.product_line && (
                    <div className="flex items-center gap-2">
                      <Tag className="h-3 w-3" />
                      <span>Dòng sản phẩm: {document.product.product_line.name}</span>
                    </div>
                  )}
                </div>
              )}

              <div className="flex gap-2 pt-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    toast({
                      title: "Thông báo",
                      description: "Tính năng tải xuống sẽ được cập nhật sau"
                    });
                  }}
                  className="flex-1"
                >
                  <Download className="h-4 w-4 mr-1" />
                  Tải xuống
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => deleteDocument(document)}
                  className="text-destructive hover:text-destructive"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredDocuments.length === 0 && (
        <div className="text-center py-12">
          <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2">Không có tài liệu nào</h3>
          <p className="text-muted-foreground">
            {searchTerm || categoryFilter !== "all"
              ? "Không tìm thấy tài liệu phù hợp với bộ lọc"
              : "Chưa có tài liệu nào được tải lên"
            }
          </p>
        </div>
      )}
    </div>
  );
};