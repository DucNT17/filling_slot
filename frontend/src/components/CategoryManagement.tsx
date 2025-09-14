import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Plus, Edit, Trash2, Folder, FolderOpen } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import axios from "axios";

const API_BASE_URL = "http://52.64.205.176:8080/";

interface Category {
    id: string;
    name: string;
    product_lines?: ProductLine[];
}

interface ProductLine {
    id: string;
    name: string;
    category_id: string;
}

interface CategoryManagementProps {
    onDataChanged?: () => void;
}

export const CategoryManagement = ({ onDataChanged }: CategoryManagementProps) => {
    const [categories, setCategories] = useState<Category[]>([]);
    const [loading, setLoading] = useState(true);
    const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
    const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
    const [editingCategory, setEditingCategory] = useState<Category | null>(null);
    const [deletingCategory, setDeletingCategory] = useState<Category | null>(null);
    const [formData, setFormData] = useState({ name: "" });
    const [submitting, setSubmitting] = useState(false);
    const { toast } = useToast();

    useEffect(() => {
        fetchCategories();
    }, []);

    const fetchCategories = async () => {
        try {
            setLoading(true);
            const response = await axios.get(`${API_BASE_URL}hierarchy`);
            setCategories(response.data);
        } catch (error: any) {
            console.error('Error fetching categories:', error);
            toast({
                title: "Lỗi",
                description: "Không thể tải danh sách danh mục",
                variant: "destructive"
            });
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = async () => {
        if (!formData.name.trim()) {
            toast({
                title: "Lỗi",
                description: "Vui lòng nhập tên danh mục",
                variant: "destructive"
            });
            return;
        }

        setSubmitting(true);
        try {
            const formDataToSend = new FormData();
            formDataToSend.append("name", formData.name.trim());

            await axios.post(`${API_BASE_URL}categories`, formDataToSend);

            toast({
                title: "Thành công",
                description: "Đã tạo danh mục thành công"
            });

            setFormData({ name: "" });
            setIsCreateDialogOpen(false);
            fetchCategories();
            onDataChanged?.();
        } catch (error: any) {
            console.error('Create error:', error);
            toast({
                title: "Lỗi",
                description: error.response?.data?.error || "Không thể tạo danh mục",
                variant: "destructive"
            });
        } finally {
            setSubmitting(false);
        }
    };

    const handleEdit = async () => {
        if (!formData.name.trim() || !editingCategory) {
            toast({
                title: "Lỗi",
                description: "Vui lòng nhập tên danh mục",
                variant: "destructive"
            });
            return;
        }

        setSubmitting(true);
        try {
            const formDataToSend = new FormData();
            formDataToSend.append("name", formData.name.trim());

            await axios.put(`${API_BASE_URL}categories/${editingCategory.id}`, formDataToSend);

            toast({
                title: "Thành công",
                description: "Đã cập nhật danh mục thành công"
            });

            setFormData({ name: "" });
            setIsEditDialogOpen(false);
            setEditingCategory(null);
            fetchCategories();
            onDataChanged?.();
        } catch (error: any) {
            console.error('Update error:', error);
            toast({
                title: "Lỗi",
                description: error.response?.data?.error || "Không thể cập nhật danh mục",
                variant: "destructive"
            });
        } finally {
            setSubmitting(false);
        }
    };

    const handleDelete = async () => {
        if (!deletingCategory) return;

        setSubmitting(true);
        try {
            await axios.delete(`${API_BASE_URL}categories/${deletingCategory.id}`);

            toast({
                title: "Thành công",
                description: "Đã xóa danh mục thành công"
            });

            setDeletingCategory(null);
            fetchCategories();
            onDataChanged?.();
        } catch (error: any) {
            console.error('Delete error:', error);
            toast({
                title: "Lỗi",
                description: error.response?.data?.error || "Không thể xóa danh mục",
                variant: "destructive"
            });
        } finally {
            setSubmitting(false);
        }
    };

    const openEditDialog = (category: Category) => {
        setEditingCategory(category);
        setFormData({ name: category.name });
        setIsEditDialogOpen(true);
    };

    const openCreateDialog = () => {
        setFormData({ name: "" });
        setIsCreateDialogOpen(true);
    };

    if (loading) {
        return <div className="text-center py-8">Đang tải...</div>;
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-2xl font-bold">Quản lý Danh mục</h2>
                    <p className="text-muted-foreground">Quản lý các danh mục sản phẩm</p>
                </div>
                <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
                    <DialogTrigger asChild>
                        <Button onClick={openCreateDialog}>
                            <Plus className="h-4 w-4 mr-2" />
                            Thêm danh mục
                        </Button>
                    </DialogTrigger>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Tạo danh mục mới</DialogTitle>
                            <DialogDescription>
                                Nhập thông tin để tạo danh mục mới
                            </DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4">
                            <div>
                                <Label htmlFor="category-name">Tên danh mục *</Label>
                                <Input
                                    id="category-name"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    placeholder="Ví dụ: Critical Power"
                                />
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
                                {submitting ? "Đang tạo..." : "Tạo danh mục"}
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Danh sách danh mục</CardTitle>
                    <CardDescription>
                        Tổng cộng {categories.length} danh mục
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Tên danh mục</TableHead>
                                <TableHead>Số dòng sản phẩm</TableHead>
                                <TableHead className="text-right">Thao tác</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {categories.map((category) => (
                                <TableRow key={category.id}>
                                    <TableCell>
                                        <div className="flex items-center gap-2">
                                            <Folder className="h-4 w-4 text-blue-500" />
                                            <span className="font-medium">{category.name}</span>
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        <Badge variant="outline">
                                            {category.product_lines?.length || 0} dòng sản phẩm
                                        </Badge>
                                    </TableCell>
                                    <TableCell className="text-right">
                                        <div className="flex gap-2 justify-end">
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => openEditDialog(category)}
                                            >
                                                <Edit className="h-3 w-3" />
                                            </Button>
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => setDeletingCategory(category)}
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

                    {categories.length === 0 && (
                        <div className="text-center py-8">
                            <FolderOpen className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                            <h3 className="text-lg font-medium mb-2">Chưa có danh mục nào</h3>
                            <p className="text-muted-foreground mb-4">
                                Bắt đầu bằng cách tạo danh mục đầu tiên
                            </p>
                            <Button onClick={openCreateDialog}>
                                <Plus className="h-4 w-4 mr-2" />
                                Tạo danh mục đầu tiên
                            </Button>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Edit Dialog */}
            <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Chỉnh sửa danh mục</DialogTitle>
                        <DialogDescription>
                            Cập nhật thông tin danh mục
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                        <div>
                            <Label htmlFor="edit-category-name">Tên danh mục *</Label>
                            <Input
                                id="edit-category-name"
                                value={formData.name}
                                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                placeholder="Ví dụ: Critical Power"
                            />
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
            <AlertDialog open={!!deletingCategory} onOpenChange={() => setDeletingCategory(null)}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Xác nhận xóa danh mục</AlertDialogTitle>
                        <AlertDialogDescription>
                            Bạn có chắc chắn muốn xóa danh mục <strong>"{deletingCategory?.name}"</strong>?
                            <br />
                            <span className="text-destructive">
                                Tất cả dòng sản phẩm và sản phẩm trong danh mục này cũng sẽ bị xóa.
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
                            {submitting ? "Đang xóa..." : "Xóa danh mục"}
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
};
