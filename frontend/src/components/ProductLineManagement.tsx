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
import { Plus, Edit, Trash2, FolderOpen, Package } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import axios from "axios";

const API_BASE_URL = "http://localhost:5000/";

interface Category {
    id: string;
    name: string;
    product_lines?: ProductLine[];
}

interface Product {
    id: string;
    name: string;
}

interface ProductLine {
    id: string;
    name: string;
    category_id: string;
    products?: Product[];
}

interface ProductLineWithCategory extends ProductLine {
    category?: Category;
}

interface ProductLineManagementProps {
    onDataChanged?: () => void;
}

export const ProductLineManagement = ({ onDataChanged }: ProductLineManagementProps) => {
    const [productLines, setProductLines] = useState<ProductLineWithCategory[]>([]);
    const [categories, setCategories] = useState<Category[]>([]);
    const [loading, setLoading] = useState(true);
    const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
    const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
    const [editingProductLine, setEditingProductLine] = useState<ProductLineWithCategory | null>(null);
    const [deletingProductLine, setDeletingProductLine] = useState<ProductLineWithCategory | null>(null);
    const [formData, setFormData] = useState({ name: "", category_id: "" });
    const [submitting, setSubmitting] = useState(false);
    const { toast } = useToast();

    useEffect(() => {
        fetchInitialData();
    }, []);

    const fetchInitialData = async () => {
        try {
            setLoading(true);
            await fetchHierarchy();
        } catch (error) {
            console.error('Error fetching initial data:', error);
        } finally {
            setLoading(false);
        }
    };

    const fetchHierarchy = async () => {
        try {
            const response = await axios.get(`${API_BASE_URL}hierarchy`);
            const hierarchyData: Category[] = response.data;

            // Extract categories
            setCategories(hierarchyData);

            // Extract product lines with products info
            const allProductLines: ProductLineWithCategory[] = [];
            hierarchyData.forEach(category => {
                if (category.product_lines) {
                    category.product_lines.forEach(productLine => {
                        allProductLines.push({
                            ...productLine,
                            category: { id: category.id, name: category.name }
                        });
                    });
                }
            });
            setProductLines(allProductLines);

        } catch (error: any) {
            console.error('Error fetching hierarchy:', error);
            toast({
                title: "Lỗi",
                description: "Không thể tải dữ liệu",
                variant: "destructive"
            });
        }
    };

    const getCategoryName = (categoryId: string) => {
        const category = categories.find(c => c.id === categoryId);
        return category?.name || "Không xác định";
    };

    const handleCreate = async () => {
        if (!formData.name.trim() || !formData.category_id) {
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
            formDataToSend.append("category_id", formData.category_id);

            await axios.post(`${API_BASE_URL}product-lines`, formDataToSend);

            toast({
                title: "Thành công",
                description: "Đã tạo dòng sản phẩm thành công"
            });

            setFormData({ name: "", category_id: "" });
            setIsCreateDialogOpen(false);
            fetchHierarchy();
            onDataChanged?.();
        } catch (error: any) {
            console.error('Create error:', error);
            toast({
                title: "Lỗi",
                description: error.response?.data?.error || "Không thể tạo dòng sản phẩm",
                variant: "destructive"
            });
        } finally {
            setSubmitting(false);
        }
    };

    const handleEdit = async () => {
        if (!formData.name.trim() || !editingProductLine) {
            toast({
                title: "Lỗi",
                description: "Vui lòng nhập tên dòng sản phẩm",
                variant: "destructive"
            });
            return;
        }

        setSubmitting(true);
        try {
            const formDataToSend = new FormData();
            formDataToSend.append("name", formData.name.trim());

            await axios.put(`${API_BASE_URL}product-lines/${editingProductLine.id}`, formDataToSend);

            toast({
                title: "Thành công",
                description: "Đã cập nhật dòng sản phẩm thành công"
            });

            setFormData({ name: "", category_id: "" });
            setIsEditDialogOpen(false);
            setEditingProductLine(null);
            fetchHierarchy();
            onDataChanged?.();
        } catch (error: any) {
            console.error('Update error:', error);
            toast({
                title: "Lỗi",
                description: error.response?.data?.error || "Không thể cập nhật dòng sản phẩm",
                variant: "destructive"
            });
        } finally {
            setSubmitting(false);
        }
    };

    const handleDelete = async () => {
        if (!deletingProductLine) return;

        setSubmitting(true);
        try {
            await axios.delete(`${API_BASE_URL}product-lines/${deletingProductLine.id}`);

            toast({
                title: "Thành công",
                description: "Đã xóa dòng sản phẩm thành công"
            });

            setDeletingProductLine(null);
            fetchHierarchy();
            onDataChanged?.();
        } catch (error: any) {
            console.error('Delete error:', error);
            toast({
                title: "Lỗi",
                description: error.response?.data?.error || "Không thể xóa dòng sản phẩm",
                variant: "destructive"
            });
        } finally {
            setSubmitting(false);
        }
    };

    const openEditDialog = (productLine: ProductLineWithCategory) => {
        setEditingProductLine(productLine);
        setFormData({ name: productLine.name, category_id: productLine.category_id });
        setIsEditDialogOpen(true);
    };

    const openCreateDialog = () => {
        setFormData({ name: "", category_id: "" });
        setIsCreateDialogOpen(true);
    };

    if (loading) {
        return <div className="text-center py-8">Đang tải...</div>;
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-2xl font-bold">Quản lý Dòng sản phẩm</h2>
                    <p className="text-muted-foreground">Quản lý các dòng sản phẩm theo danh mục</p>
                </div>
                <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
                    <DialogTrigger asChild>
                        <Button onClick={openCreateDialog}>
                            <Plus className="h-4 w-4 mr-2" />
                            Thêm dòng sản phẩm
                        </Button>
                    </DialogTrigger>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Tạo dòng sản phẩm mới</DialogTitle>
                            <DialogDescription>
                                Nhập thông tin để tạo dòng sản phẩm mới
                            </DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4">
                            <div>
                                <Label htmlFor="productline-name">Tên dòng sản phẩm *</Label>
                                <Input
                                    id="productline-name"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    placeholder="Ví dụ: DC Power Systems"
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
                                {submitting ? "Đang tạo..." : "Tạo dòng sản phẩm"}
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Danh sách dòng sản phẩm</CardTitle>
                    <CardDescription>
                        Tổng cộng {productLines.length} dòng sản phẩm
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Tên dòng sản phẩm</TableHead>
                                <TableHead>Danh mục</TableHead>
                                <TableHead>Số sản phẩm</TableHead>
                                <TableHead className="text-right">Thao tác</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {productLines.map((productLine) => (
                                <TableRow key={productLine.id}>
                                    <TableCell>
                                        <div className="flex items-center gap-2">
                                            <FolderOpen className="h-4 w-4 text-green-500" />
                                            <span className="font-medium">{productLine.name}</span>
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        <Badge variant="secondary">
                                            {productLine.category?.name || getCategoryName(productLine.category_id)}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>
                                        <Badge variant="outline">
                                            {productLine.products?.length || 0} sản phẩm
                                        </Badge>
                                    </TableCell>
                                    <TableCell className="text-right">
                                        <div className="flex gap-2 justify-end">
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => openEditDialog(productLine)}
                                            >
                                                <Edit className="h-3 w-3" />
                                            </Button>
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => setDeletingProductLine(productLine)}
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

                    {productLines.length === 0 && (
                        <div className="text-center py-8">
                            <Package className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                            <h3 className="text-lg font-medium mb-2">Chưa có dòng sản phẩm nào</h3>
                            <p className="text-muted-foreground mb-4">
                                Bắt đầu bằng cách tạo dòng sản phẩm đầu tiên
                            </p>
                            <Button onClick={openCreateDialog} disabled={categories.length === 0}>
                                <Plus className="h-4 w-4 mr-2" />
                                {categories.length === 0 ? "Tạo danh mục trước" : "Tạo dòng sản phẩm đầu tiên"}
                            </Button>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Edit Dialog */}
            <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Chỉnh sửa dòng sản phẩm</DialogTitle>
                        <DialogDescription>
                            Cập nhật thông tin dòng sản phẩm
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                        <div>
                            <Label htmlFor="edit-productline-name">Tên dòng sản phẩm *</Label>
                            <Input
                                id="edit-productline-name"
                                value={formData.name}
                                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                placeholder="Ví dụ: DC Power Systems"
                            />
                        </div>
                        <div>
                            <Label>Danh mục hiện tại</Label>
                            <div className="p-2 bg-muted rounded-md">
                                <Badge variant="secondary">
                                    {editingProductLine?.category?.name || getCategoryName(editingProductLine?.category_id || "")}
                                </Badge>
                            </div>
                            <p className="text-xs text-muted-foreground mt-1">
                                Để thay đổi danh mục, vui lòng xóa và tạo lại dòng sản phẩm
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
            <AlertDialog open={!!deletingProductLine} onOpenChange={() => setDeletingProductLine(null)}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Xác nhận xóa dòng sản phẩm</AlertDialogTitle>
                        <AlertDialogDescription>
                            Bạn có chắc chắn muốn xóa dòng sản phẩm <strong>"{deletingProductLine?.name}"</strong>?
                            <br />
                            <span className="text-destructive">
                                Tất cả sản phẩm trong dòng sản phẩm này cũng sẽ bị xóa.
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
                            {submitting ? "Đang xóa..." : "Xóa dòng sản phẩm"}
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
};
