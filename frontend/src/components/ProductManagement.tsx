import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Plus, Edit, Trash2, Package, FileText } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import axios from "axios";

const API_BASE_URL = "http://52.64.205.176:8080/";

interface Category {
    id: string;
    name: string;
}

interface ProductLine {
    id: string;
    name: string;
    category_id: string;
}

interface FileItem {
    id: string;
    name: string;
}

interface Product {
    id: string;
    name: string;
    product_line_id: string;
    files?: FileItem[];
}

interface ProductWithDetails extends Product {
    product_line?: {
        id: string;
        name: string;
        category: Category;
    };
}

interface ProductManagementProps {
    onDataChanged?: () => void;
}

export const ProductManagement = ({ onDataChanged }: ProductManagementProps) => {
    const [products, setProducts] = useState<ProductWithDetails[]>([]);
    const [categories, setCategories] = useState<Category[]>([]);
    const [productLines, setProductLines] = useState<ProductLine[]>([]);
    const [filteredProductLines, setFilteredProductLines] = useState<ProductLine[]>([]);
    const [loading, setLoading] = useState(true);
    const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
    const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
    const [editingProduct, setEditingProduct] = useState<ProductWithDetails | null>(null);
    const [deletingProduct, setDeletingProduct] = useState<ProductWithDetails | null>(null);
    const [formData, setFormData] = useState({ name: "", category_id: "", product_line_id: "" });
    const [submitting, setSubmitting] = useState(false);
    const { toast } = useToast();

    useEffect(() => {
        fetchInitialData();
    }, []);

    useEffect(() => {
        if (formData.category_id) {
            const filtered = productLines.filter(pl => pl.category_id === formData.category_id);
            setFilteredProductLines(filtered);
            setFormData(prev => ({ ...prev, product_line_id: "" }));
        } else {
            setFilteredProductLines([]);
        }
    }, [formData.category_id, productLines]);

    const fetchInitialData = async () => {
        try {
            setLoading(true);
            await fetchHierarchyData();
        } catch (error) {
            console.error('Error fetching initial data:', error);
        } finally {
            setLoading(false);
        }
    };

    const fetchHierarchyData = async () => {
        try {
            const response = await axios.get(`${API_BASE_URL}hierarchy`);
            console.log("Hierarchy response:", response.data);

            // Extract categories, product lines, and products from hierarchy
            const categoriesData: Category[] = [];
            const productLinesData: ProductLine[] = [];
            const productsData: ProductWithDetails[] = [];

            response.data.forEach((category: any) => {
                // Add category
                categoriesData.push({
                    id: category.id,
                    name: category.name
                });

                category.product_lines.forEach((productLine: any) => {
                    // Add product line
                    productLinesData.push({
                        id: productLine.id,
                        name: productLine.name,
                        category_id: category.id
                    });

                    productLine.products.forEach((product: any) => {
                        // Add product with full details
                        productsData.push({
                            id: product.id,
                            name: product.name,
                            product_line_id: productLine.id,
                            files: product.files || [],
                            product_line: {
                                id: productLine.id,
                                name: productLine.name,
                                category: {
                                    id: category.id,
                                    name: category.name
                                }
                            }
                        });
                    });
                });
            });

            // Set all data at once
            setCategories(categoriesData);
            setProductLines(productLinesData);
            setProducts(productsData);

        } catch (error: any) {
            console.error('Error fetching hierarchy data:', error);
            toast({
                title: "Lỗi",
                description: "Không thể tải dữ liệu hệ thống",
                variant: "destructive"
            });
        }
    };



    const handleCreate = async () => {
        if (!formData.name.trim() || !formData.product_line_id) {
            toast({
                title: "Lỗi",
                description: "Vui lòng điền đầy đủ thông tin",
                variant: "destructive"
            });
            return;
        }

        setSubmitting(true);
        try {
            const formDataToSend = new FormData();
            formDataToSend.append("name", formData.name.trim());
            formDataToSend.append("product_line_id", formData.product_line_id);

            await axios.post(`${API_BASE_URL}products`, formDataToSend);

            toast({
                title: "Thành công",
                description: "Đã tạo sản phẩm thành công"
            });

            setFormData({ name: "", category_id: "", product_line_id: "" });
            setIsCreateDialogOpen(false);
            await fetchHierarchyData(); // Refresh all data from hierarchy
            onDataChanged?.();
        } catch (error: any) {
            console.error('Create error:', error);
            toast({
                title: "Lỗi",
                description: error.response?.data?.error || "Không thể tạo sản phẩm",
                variant: "destructive"
            });
        } finally {
            setSubmitting(false);
        }
    };

    const handleEdit = async () => {
        if (!formData.name.trim() || !editingProduct) {
            toast({
                title: "Lỗi",
                description: "Vui lòng nhập tên sản phẩm",
                variant: "destructive"
            });
            return;
        }

        setSubmitting(true);
        try {
            const formDataToSend = new FormData();
            formDataToSend.append("name", formData.name.trim());

            await axios.put(`${API_BASE_URL}products/${editingProduct.id}`, formDataToSend);

            toast({
                title: "Thành công",
                description: "Đã cập nhật sản phẩm thành công"
            });

            setFormData({ name: "", category_id: "", product_line_id: "" });
            setIsEditDialogOpen(false);
            setEditingProduct(null);
            await fetchHierarchyData(); // Refresh all data from hierarchy
            onDataChanged?.();
        } catch (error: any) {
            console.error('Update error:', error);
            toast({
                title: "Lỗi",
                description: error.response?.data?.error || "Không thể cập nhật sản phẩm",
                variant: "destructive"
            });
        } finally {
            setSubmitting(false);
        }
    };

    const handleDelete = async () => {
        if (!deletingProduct) return;

        setSubmitting(true);
        try {
            await axios.delete(`${API_BASE_URL}products/${deletingProduct.id}`);

            toast({
                title: "Thành công",
                description: "Đã xóa sản phẩm thành công"
            });

            setDeletingProduct(null);
            await fetchHierarchyData(); // Refresh all data from hierarchy
            onDataChanged?.();
        } catch (error: any) {
            console.error('Delete error:', error);
            toast({
                title: "Lỗi",
                description: error.response?.data?.error || "Không thể xóa sản phẩm",
                variant: "destructive"
            });
        } finally {
            setSubmitting(false);
        }
    };

    const openEditDialog = (product: ProductWithDetails) => {
        setEditingProduct(product);
        setFormData({
            name: product.name,
            category_id: product.product_line?.category?.id || "",
            product_line_id: product.product_line_id
        });
        setIsEditDialogOpen(true);
    };

    const openCreateDialog = () => {
        setFormData({ name: "", category_id: "", product_line_id: "" });
        setIsCreateDialogOpen(true);
    };

    if (loading) {
        return <div className="text-center py-8">Đang tải...</div>;
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-2xl font-bold">Quản lý Sản phẩm</h2>
                    <p className="text-muted-foreground">Quản lý các sản phẩm theo dòng sản phẩm</p>
                </div>
                <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
                    <DialogTrigger asChild>
                        <Button onClick={openCreateDialog}>
                            <Plus className="h-4 w-4 mr-2" />
                            Thêm sản phẩm
                        </Button>
                    </DialogTrigger>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Tạo sản phẩm mới</DialogTitle>
                            <DialogDescription>
                                Nhập thông tin để tạo sản phẩm mới
                            </DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4">
                            <div>
                                <Label htmlFor="product-name">Tên sản phẩm *</Label>
                                <Input
                                    id="product-name"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    placeholder="Ví dụ: NetSure 801 Series"
                                />
                            </div>
                            <div>
                                <Label htmlFor="category-select">Danh mục *</Label>
                                <Select value={formData.category_id} onValueChange={(value) => setFormData({ ...formData, category_id: value })}>
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
                                <Label htmlFor="productline-select">Dòng sản phẩm *</Label>
                                <Select
                                    value={formData.product_line_id}
                                    onValueChange={(value) => setFormData({ ...formData, product_line_id: value })}
                                    disabled={!formData.category_id}
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
                        </div>
                        <DialogFooter>
                            <Button
                                variant="outline"
                                onClick={() => setIsCreateDialogOpen(false)}
                                disabled={submitting}
                            >
                                Hủy
                            </Button>
                            <Button onClick={handleCreate} disabled={submitting}>
                                {submitting ? "Đang tạo..." : "Tạo sản phẩm"}
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Danh sách sản phẩm</CardTitle>
                    <CardDescription>
                        Tổng cộng {products.length} sản phẩm
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Tên sản phẩm</TableHead>
                                <TableHead>Dòng sản phẩm</TableHead>
                                <TableHead>Danh mục</TableHead>
                                <TableHead>Số tài liệu</TableHead>
                                <TableHead className="text-right">Thao tác</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {products.map((product) => (
                                <TableRow key={product.id}>
                                    <TableCell>
                                        <div className="flex items-center gap-2">
                                            <Package className="h-4 w-4 text-orange-500" />
                                            <span className="font-medium">{product.name}</span>
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        <Badge variant="secondary">
                                            {product.product_line?.name || "Không xác định"}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>
                                        <Badge variant="outline">
                                            {product.product_line?.category?.name || "Không xác định"}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>
                                        <div className="flex items-center gap-1">
                                            <FileText className="h-3 w-3 text-muted-foreground" />
                                            <span>{product.files?.length || 0} tài liệu</span>
                                        </div>
                                    </TableCell>
                                    <TableCell className="text-right">
                                        <div className="flex gap-2 justify-end">
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => openEditDialog(product)}
                                            >
                                                <Edit className="h-3 w-3" />
                                            </Button>
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => setDeletingProduct(product)}
                                                className="text-destructive hover:text-destructive"
                                            >
                                                <Trash2 className="h-3 w-3" />
                                            </Button>
                                        </div>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>

                    {products.length === 0 && (
                        <div className="text-center py-8">
                            <Package className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                            <h3 className="text-lg font-medium mb-2">Chưa có sản phẩm nào</h3>
                            <p className="text-muted-foreground mb-4">
                                Bắt đầu bằng cách tạo sản phẩm đầu tiên
                            </p>
                            <Button onClick={openCreateDialog} disabled={productLines.length === 0}>
                                <Plus className="h-4 w-4 mr-2" />
                                {productLines.length === 0 ? "Tạo dòng sản phẩm trước" : "Tạo sản phẩm đầu tiên"}
                            </Button>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Edit Dialog */}
            <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Chỉnh sửa sản phẩm</DialogTitle>
                        <DialogDescription>
                            Cập nhật thông tin sản phẩm
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                        <div>
                            <Label htmlFor="edit-product-name">Tên sản phẩm *</Label>
                            <Input
                                id="edit-product-name"
                                value={formData.name}
                                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                placeholder="Ví dụ: NetSure 801 Series"
                            />
                        </div>
                        <div>
                            <Label>Dòng sản phẩm hiện tại</Label>
                            <div className="p-2 bg-muted rounded-md">
                                <Badge variant="secondary">
                                    {editingProduct?.product_line?.name || "Không xác định"}
                                </Badge>
                            </div>
                            <p className="text-xs text-muted-foreground mt-1">
                                Để thay đổi dòng sản phẩm, vui lòng xóa và tạo lại sản phẩm
                            </p>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button
                            variant="outline"
                            onClick={() => setIsEditDialogOpen(false)}
                            disabled={submitting}
                        >
                            Hủy
                        </Button>
                        <Button onClick={handleEdit} disabled={submitting}>
                            {submitting ? "Đang cập nhật..." : "Cập nhật"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Delete Confirmation Dialog */}
            <AlertDialog open={!!deletingProduct} onOpenChange={() => setDeletingProduct(null)}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Xác nhận xóa sản phẩm</AlertDialogTitle>
                        <AlertDialogDescription>
                            Bạn có chắc chắn muốn xóa sản phẩm <strong>"{deletingProduct?.name}"</strong>?
                            <br />
                            <span className="text-destructive">
                                Tất cả tài liệu của sản phẩm này cũng sẽ bị xóa.
                            </span>
                            <br />
                            Hành động này không thể hoàn tác.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel disabled={submitting}>
                            Hủy
                        </AlertDialogCancel>
                        <AlertDialogAction
                            onClick={handleDelete}
                            disabled={submitting}
                            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                        >
                            {submitting ? "Đang xóa..." : "Xóa sản phẩm"}
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
};
