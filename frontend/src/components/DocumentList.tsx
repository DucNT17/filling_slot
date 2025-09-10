import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { FileText, Download, Trash2, Search, ChevronDown, ChevronRight, Folder, FolderOpen, Package } from "lucide-react";
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

export const DocumentList = () => {
  const [hierarchy, setHierarchy] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [deletingFile, setDeletingFile] = useState<FileItem | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Expansion states
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
        description: `Không thể tải cấu trúc tài liệu: ${error.message}`,
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
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

  const handleDeleteClick = (file: FileItem) => {
    setDeletingFile(file);
  };

  const confirmDelete = async () => {
    if (!deletingFile) return;

    setIsDeleting(true);
    try {
      await axios.delete(`${API_BASE_URL}files/${deletingFile.id}`);

      toast({
        title: "Thành công",
        description: "Đã xóa tài liệu thành công"
      });

      fetchHierarchy(); // Refresh hierarchy after delete
      setDeletingFile(null);
    } catch (error: any) {
      console.error('Delete error:', error);
      toast({
        title: "Lỗi",
        description: "Không thể xóa tài liệu",
        variant: "destructive"
      });
    } finally {
      setIsDeleting(false);
    }
  };

  const cancelDelete = () => {
    setDeletingFile(null);
  };

  // Filter and count functions
  const getFilteredHierarchy = () => {
    return hierarchy.filter(category => {
      // Category filter
      if (categoryFilter !== "all" && category.id !== categoryFilter) {
        return false;
      }

      // Search filter - check if any file in this category matches
      if (searchTerm) {
        const hasMatchingFile = category.product_lines.some(pl =>
          pl.products.some(product =>
            product.files.some(file =>
              file.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
              product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
              pl.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
              category.name.toLowerCase().includes(searchTerm.toLowerCase())
            )
          )
        );
        return hasMatchingFile;
      }

      return true;
    });
  };

  const getTotalFileCount = () => {
    return hierarchy.reduce((total, category) =>
      total + category.product_lines.reduce((plTotal, pl) =>
        plTotal + pl.products.reduce((pTotal, product) =>
          pTotal + product.files.length, 0), 0), 0);
  };

  const getFilteredFileCount = () => {
    return getFilteredHierarchy().reduce((total, category) =>
      total + category.product_lines.reduce((plTotal, pl) =>
        plTotal + pl.products.reduce((pTotal, product) =>
          pTotal + product.files.filter(file =>
            !searchTerm ||
            file.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            pl.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            category.name.toLowerCase().includes(searchTerm.toLowerCase())
          ).length, 0), 0), 0);
  };

  const filteredHierarchy = getFilteredHierarchy();

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
            {hierarchy.map((category) => (
              <SelectItem key={category.id} value={category.id}>
                {category.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="text-sm text-muted-foreground">
        Hiển thị {getFilteredFileCount()} / {getTotalFileCount()} tài liệu
      </div>

      <div className="space-y-4">
        {filteredHierarchy.map((category) => (
          <Card key={category.id} className="overflow-hidden">
            <Collapsible
              open={expandedCategories.has(category.id)}
              onOpenChange={() => toggleExpanded(category.id, 'category')}
            >
              <CollapsibleTrigger className="w-full">
                <CardHeader className="hover:bg-muted/50 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {expandedCategories.has(category.id) ? (
                        <ChevronDown className="h-5 w-5 text-muted-foreground" />
                      ) : (
                        <ChevronRight className="h-5 w-5 text-muted-foreground" />
                      )}
                      <Folder className="h-5 w-5 text-blue-500" />
                      <CardTitle className="text-lg">{category.name}</CardTitle>
                    </div>
                    <Badge variant="outline">
                      {category.product_lines.reduce((total, pl) =>
                        total + pl.products.reduce((pTotal, product) =>
                          pTotal + product.files.length, 0), 0)} files
                    </Badge>
                  </div>
                </CardHeader>
              </CollapsibleTrigger>

              <CollapsibleContent>
                <CardContent className="pt-0">
                  <div className="space-y-3 ml-8">
                    {category.product_lines.map((productLine) => (
                      <div key={productLine.id}>
                        <Collapsible
                          open={expandedProductLines.has(productLine.id)}
                          onOpenChange={() => toggleExpanded(productLine.id, 'productLine')}
                        >
                          <CollapsibleTrigger className="w-full">
                            <div className="flex items-center gap-3 p-2 hover:bg-muted/30 rounded-md">
                              {expandedProductLines.has(productLine.id) ? (
                                <ChevronDown className="h-4 w-4 text-muted-foreground" />
                              ) : (
                                <ChevronRight className="h-4 w-4 text-muted-foreground" />
                              )}
                              <FolderOpen className="h-4 w-4 text-green-500" />
                              <span className="font-medium text-left flex-1">{productLine.name}</span>
                              <Badge variant="secondary" className="text-xs">
                                {productLine.products.reduce((total, product) =>
                                  total + product.files.length, 0)} files
                              </Badge>
                            </div>
                          </CollapsibleTrigger>

                          <CollapsibleContent>
                            <div className="ml-7 mt-2 space-y-2">
                              {productLine.products.map((product) => (
                                <div key={product.id}>
                                  <Collapsible
                                    open={expandedProducts.has(product.id)}
                                    onOpenChange={() => toggleExpanded(product.id, 'product')}
                                  >
                                    <CollapsibleTrigger className="w-full">
                                      <div className="flex items-center gap-3 p-2 hover:bg-muted/20 rounded-md">
                                        {expandedProducts.has(product.id) ? (
                                          <ChevronDown className="h-3 w-3 text-muted-foreground" />
                                        ) : (
                                          <ChevronRight className="h-3 w-3 text-muted-foreground" />
                                        )}
                                        <Package className="h-3 w-3 text-orange-500" />
                                        <span className="text-sm font-medium text-left flex-1">{product.name}</span>
                                        <Badge variant="outline" className="text-xs">
                                          {product.files.length} files
                                        </Badge>
                                      </div>
                                    </CollapsibleTrigger>

                                    <CollapsibleContent>
                                      <div className="ml-6 mt-2 space-y-1">
                                        {product.files
                                          .filter(file =>
                                            !searchTerm ||
                                            file.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                                            product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                                            productLine.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                                            category.name.toLowerCase().includes(searchTerm.toLowerCase())
                                          )
                                          .map((file) => (
                                            <div key={file.id} className="flex items-center justify-between p-2 hover:bg-muted/10 rounded-md border border-muted">
                                              <div className="flex items-center gap-2">
                                                <FileText className="h-3 w-3 text-gray-500" />
                                                <span className="text-sm">{file.name}</span>
                                              </div>
                                              <div className="flex gap-1">
                                                <Button
                                                  variant="ghost"
                                                  size="sm"
                                                  onClick={(e) => {
                                                    e.stopPropagation();
                                                    toast({
                                                      title: "Thông báo",
                                                      description: "Tính năng tải xuống sẽ được cập nhật sau"
                                                    });
                                                  }}
                                                  className="h-6 w-6 p-0"
                                                >
                                                  <Download className="h-3 w-3" />
                                                </Button>
                                                <Button
                                                  variant="ghost"
                                                  size="sm"
                                                  onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleDeleteClick(file);
                                                  }}
                                                  className="h-6 w-6 p-0 text-destructive hover:text-destructive"
                                                >
                                                  <Trash2 className="h-3 w-3" />
                                                </Button>
                                              </div>
                                            </div>
                                          ))}
                                      </div>
                                    </CollapsibleContent>
                                  </Collapsible>
                                </div>
                              ))}
                            </div>
                          </CollapsibleContent>
                        </Collapsible>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </CollapsibleContent>
            </Collapsible>
          </Card>
        ))}
      </div>

      {filteredHierarchy.length === 0 && (
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

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!deletingFile} onOpenChange={() => setDeletingFile(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Xác nhận xóa tài liệu</AlertDialogTitle>
            <AlertDialogDescription>
              Bạn có chắc chắn muốn xóa tài liệu <strong>"{deletingFile?.name}"</strong>?
              <br />
              Hành động này không thể hoàn tác.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={cancelDelete} disabled={isDeleting}>
              Hủy
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDelete}
              disabled={isDeleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isDeleting ? "Đang xóa..." : "Xóa"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};